#-------------------------------------------------------------------------------
# Name:        Final Project - Connecting Wildlife Habitat
# Purpose:     To incorporate Python functionality learned throughout the semester.
#
# Author:      Kristy Guan
#
# Created:     29/11/2024
# Copyright:   (c) 954512 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------



# Import all required modules
import arcpy, os, sys
from arcpy.sa import *
import arcpy.mp as MAP

import time # Import time module
start = time.time() # Record start time. reference: https://www.geeksforgeeks.org/how-to-check-the-execution-time-of-python-script/
print("Start of script.\n")


# Set the overwrite outputs environment
arcpy.env.overwriteOutput = True #allow overwriting files, default is False

# Check out the Spatial extension
arcpy.CheckOutExtension("Spatial")

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

# Function to print out the first and last message from a Function Tool
def messages():
    print(arcpy.GetMessage(0)) # print first message of tool
    count = (arcpy.GetMessageCount())
    print(arcpy.GetMessage(count-1)) # print last message of tool
    print()


# Function to check for the existence of the gdb and to delete it
def checkExistandDelete(path, gdb_name):
    arcpy.env.workspace = path

    print(f"Checking for existence of {gdb_name}...")
    # check if gdb exists (in path/workspace location)
    if arcpy.Exists(gdb_name) == True:
        print(f"{gdb_name} exists, it will be deleted...")
        arcpy.Delete_management(gdb_name)
        messages()
    else:
        print(f"{gdb_name} does not exist.\n")


# Function to check if GDB exist and create new gdb
# folder_path is the input folder path
# gdb_name is the desired name for the gdb
# dataset_name is the desired name(s) for the datasets. can leave empty ("") for no datasets
# out_cs is the desired output coordinate system
def createGDBandDatasets(folder_path, gdb_name, dataset_name, out_cs):
    # Set workspace
    arcpy.env.workspace = folder_path

    # Check if gdb exists and delete
    checkExistandDelete(folder_path, gdb_name)

    # Create the gdb
    print(f"Creating {gdb_name}...")
    arcpy.CreateFileGDB_management(folder_path, gdb_name)
    messages()

    out_path = os.path.join(folder_path, gdb_name)

    if dataset_name != "":
        for name in dataset_name:
            print(f"Creating {name} dataset for {gdb_name}...")
            arcpy.CreateFeatureDataset_management(out_path, name, out_cs)
            messages()


# Function to save all features from an input path
# in_path is the input path
# out_path is the desired output path
# out_cs is the desired output coordinate system
def saveToGDB(in_path, out_path, out_cs):
    # Set workspace
    arcpy.env.workspace = in_path

    # List of the RAW data (shapefiles)
    fcList = arcpy.ListFeatureClasses()

    for fc in fcList:
        setCSAndSaveToGDB(fc, out_path, out_cs)


### Function to check and set coordinate system
### in_feature is the input feature name
### out_path is the desired output path
### out_cs is the desired output coordinate system
##def setCSAndSaveToGDB(in_feature, out_path, out_cs):
##
##
##    print("in setCS, in feature: ", in_feature)
##
##    sr = arcpy.Describe(in_feature).spatialReference
##
##    # set name
##    name = setName(in_feature)
##
##    # Check Coordinate system
##    if sr == out_cs:
##        print(f"{in_feature} is already set in {out_cs.name}...")
##        print(f"Saving to gdb...")
##        arcpy.FeatureClassToFeatureClass_conversion(in_feature, out_path, name)
##        messages()
##        return
##    elif sr.name == "Unknown": # reference: https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/spatialreference.htm
##        print(f"{in_feature} has unknown spatial reference, exiting...")
##        exit()
##
##    print(f"{in_feature} is in {sr.name}, projecting to {out_cs.name}...")
##    arcpy.Project_management(in_feature, os.path.join(out_path, name), out_cs)
##    messages()
##
##
### Function to clean up file names
### It will remove the file extension and leading digits from the filename
##def setName(name):
##    # extract file name without file extension
##    name = os.path.splitext(name)[0]
##    # remove digits at beginning of name
##    if name[0].isdigit():
##        name = name.split("_", 1)[1]
##    return name


#-------------------------------------------------------------------------------
# Main script block
#-------------------------------------------------------------------------------

# Path to required data location
root_path = r"C:\GEOS456\FinalProject"


study_area = r"C:\GEOS456\FinalProject\Kananaskis\KCountry_Bound.shp"



# Output geodatabase and path for final data
out_gdb = "KananaskisWildlife.gdb" #required name
out_path = os.path.join(root_path, out_gdb)

# Scratch geodatabase and path for intermediate data
scratch_gdb = "Scratch.gdb"
scratch_path = os.path.join(root_path, scratch_gdb)

# Output coordinate system
out_cs = arcpy.SpatialReference("NAD 1983 UTM Zone 11N")



# Raster cell size (required)
cell = 25 # in meters


#-------------------------------------------------------------------------------
arcpy.env.workspace = root_path

# Create GDB and datasets (will check for and delete existing gdb if necessary)
createGDBandDatasets(root_path, out_gdb, "", out_cs) # gdb for final outputs
createGDBandDatasets(root_path, scratch_gdb, "", out_cs) # gdb for intermediate data

print(f"\n{'- - '*20}\n") # print separator line


# Convert/project all data and store in gdb (From root folder to Scratch gdb to Output gdb)
for dirpath, dirnames, filenames in arcpy.da.Walk(root_path, datatype=["FeatureClass", "RasterDataset"]):
    arcpy.env.workspace = dirpath

    if dirpath.endswith(".gdb"):
        continue #skips this directory


    for filename in filenames:
        print(f"dirpath: {dirpath}")
        print(f"\tfilename: {filename}")

        if filename.lower().endswith(".shp"):  # Check if it's a shapefile

            print("\t\t Shapefile", os.path.join(dirpath, filename))

            name = os.path.splitext(filename)[0]

            sr = arcpy.Describe(filename).spatialReference

            # Check Coordinate system
            if sr == out_cs:
                print(f"{filename} is already set in {out_cs.name}. Saving to gdb...")
                arcpy.FeatureClassToFeatureClass_conversion(filename, scratch_path, name)
                messages()
            elif sr.name == "Unknown":
                print(f"{filename} has unknown spatial reference, exiting...")
                exit() #end the program
            else:
                print(f"{filename} is in {sr.name}, projecting to {out_cs.name}...")
                arcpy.Project_management(os.path.join(dirpath, filename), os.path.join(scratch_path, name), out_cs)
                messages()

            print(f"Clipping to the boundary... ")
            arcpy.analysis.Clip(in_features=os.path.join(scratch_path, name), clip_features=study_area, out_feature_class=os.path.join(out_path, name))
            messages()

        elif filename.lower().endswith(".bnd"):
            rasters = arcpy.ListRasters()
            for raster in rasters:
                print("Saving raster to scratch...")
                arcpy.conversion.RasterToOtherFormat(Input_Rasters=os.path.join(dirpath, raster), Output_Workspace=scratch_path)
                messages()

                print("Projecting raster...")
                out_raster_path = os.path.join(scratch_path, f"{raster}_projected")
                arcpy.management.ProjectRaster(in_raster=os.path.join(scratch_path, raster),out_raster=out_raster_path, out_coor_system=out_cs, cell_size=cell)

                print("Extract by Mask with park boundary...")
                out_extract = ExtractByMask(in_raster=out_raster_path, in_mask_data=study_area)
                messages()

                print(f"Saving raster to {out_gdb}...")
                out_extract.save(os.path.join(out_path, raster))
                messages()

        else:
            print("\t\t else: hi, how ya doin'? Come here often? ")

        print()

# Delete scratch gdb and all intermediate data
try:
    print(f"Deleting {scratch_gdb} along with all intermediate data...")
    arcpy.Delete_management(scratch_path)
    messages()
except Exception as e:
    print(f"Failed to delete {scratch_gdb}: {e}")
##
##
##
###-------------------------------------------------------------------------------
### Optimal Routes Parameters
### Scale ranking from 1 (most desirable) to 10 (least desirable)
###-------------------------------------------------------------------------------
##
##arcpy.env.workspace = out_path
##
##
##
##
###-------------------------------------------------------------------------------
### Landcover - Characteristics of the area being traversed (shp)
##
##print("Landcover...")
##arcpy.conversion.PolygonToRaster(in_features="AB_Landcover", value_field="LC_class", out_rasterdataset="Landcover", cellsize=cell)
##messages()
##
##landcover =arcpy.Raster("Landcover")
###reclassify the land cover
##remap = RemapValue([
##    ['20', 10],
##    ['31', 8],
##    ['32', 7],
##    ['33', 6],
##    ['34', 10],
##    ['50', 3],
##    ['110', 2],
##    ['120', 9],
##    ['210', 1],
##    ['220', 1],
##    ['230', 1]
##])
##
### Apply reclassification
##landcover_reclass = Reclassify(landcover, "VALUE", remap, "DATA")
##messages()
##
###save the reclassified land cover
##landcover_reclass.save("Landcover_Reclass")
##
###-------------------------------------------------------------------------------
### Hydrology, Trails, Roads
### - Use Distance Accumulation tool (outputs a continuous raster)
### - Use the Rescale by Function tool to apply a continuous cost value between 0-10
##
### Set the environment
##arcpy.env.extent = study_area # makes sure the rasters cover the whole boundary extent
##arcpy.env.mask = study_area # makes sure the rasters don't extend beyond the boundary
##arcpy.env.cellSize = cell # makes sure the rasters are outputted in this cell size
##
###-------------------------------------------------------------------------------
### Hydrology - (desirable)
##print("Processing Hydrology...")
##print("Distance Accumulation...")
##hydro_dist = DistanceAccumulation("Hydro")
##print("Rescale by Function...")
##hydro_rescale = RescaleByFunction(hydro_dist, "TfLarge", 10, 0) # close = 1, desirable
##messages()
##
##hydro_rescale.save("Hydro_Rescaled")
##
##print("Deleting Hydro Dist...")
##arcpy.management.Delete(hydro_dist)
##messages()
##
###-------------------------------------------------------------------------------
### Trails - (avoid)
##print("Processing Trails...")
##trails_dist = DistanceAccumulation("Trails")
##trails_rescale = RescaleByFunction(trails_dist, "TfLarge", 0, 10) # close = 10, undesirable
##messages()
##
##trails_rescale.save("Trails_Rescaled")
##
##print("Deleting Trails Dist...")
##arcpy.management.Delete(trails_dist)
##messages()
##
###-------------------------------------------------------------------------------
### Road - (avoid)
### Merge Road and Transportation
##road_merge = arcpy.management.Merge(["Road", "Transportation"], "Road_Merged")
##
##print("Processing Road...")
##print("Distance Accumulation...")
##road_dist = DistanceAccumulation(road_merge)
##print("Rescale by Function...")
##road_rescale = RescaleByFunction(road_dist, "TfLarge", 0, 10) # close = 10, undesirable
##messages()
##
##road_rescale.save("Road_Rescaled")
##
##print("Deleting Road Merged...")
##arcpy.management.Delete(road_merge)
##messages()
##
##print("Deleting Roads Dist...")
##arcpy.management.Delete(road_dist)
##messages()
##
##
##
###-------------------------------------------------------------------------------
### Terrain Ruggedness (dem) - (avoid rugged terrain)
### Rescale by Function
##
##dem = arcpy.Raster("ab_dem")
##
##print("Terrain ruggedness...")
##
### Generate the terrain ruggedness
##terrainRug = FocalStatistics(dem, NbrRectangle(3,3,"CELL"), "RANGE")
##messages()
##
##terrainRug.save("TerrainR") #save to gdb
### Use the Rescale By Function to assign the classes to the continuous rasters
##terrainRug_rescale = RescaleByFunction(terrainRug, "TfLarge", 10, 1)
##messages()
##
##terrainRug_rescale.save("TerrainR_Rescale")
##
###-------------------------------------------------------------------------------
### Combine the cost surfaces into one single cost raster
### All weights are equal to 1
##
##
###combine all rescaled and reclassified rasters together using weighted sum
##print("Weight sum...")
##weighted_sum = WeightedSum(WSTable([[landcover_reclass, 'VALUE', 1], \
##    [hydro_rescale, 'VALUE', 1], [trails_rescale, 'Value', 1], \
##    [road_rescale, 'Value', 1], [terrainRug_rescale, 'Value', 1]]))
##messages()
##
###save the weighted sum
##weighted_sum.save("Combined_Cost")
##
###create the routes with the optimal region connections tool
##print("Computing optimal path...")
##optimal_routes = OptimalRegionConnections("Bear_Habitat", "Paths", "", weighted_sum)
##messages()


# Delete all reclass and rescale rasters !

#-------------------------------------------------------------------------------
# Check in the extension
arcpy.CheckInExtension("Spatial")

#-------------------------------------------------------------------------------
# Mapping
#-------------------------------------------------------------------------------
arcpy.env.workspace = out_path

###reference the aprx document using the mapping modules
##aprx = MAP.ArcGISProject(r"C:\GEOS456\FinalProject\GEOS456_FinalProject.aprx") #path to aprx doc
##
###save a copy of the aprx so we can preserve the original
##aprx.saveACopy(r"C:\GEOS456\FinalProject\GEOS456_FinalProject_New.aprx")
##
###use the mapping module to list map frames and properties
##print("List map frames and properties: ")
##maps = aprx.listMaps()
##for map in maps:
##    print("Map Name: ", map.name, "|", "Map Type: ", map.mapType)
##    print()
##
###save a specific map frame as a variable to reference in the script
###access the first map from the list and set the index position to 0
##m = aprx.listMaps("Map")[0] #Sets the 'map' map to index position 0 within variable m
##
###use the mapping module to add layers
##listFC = arcpy.ListFeatureClasses()
##listFC = ["KCountry_Bound", "Bear_Habitat", "Paths"]
##for fc in listFC:
##    #first step in the loop is to create feature layers form the list
##    layer = arcpy.MakeFeatureLayer_management(fc)
##    #next, we will save the feature layers as .lyrx files
##    lyrFile = arcpy.SaveToLayerFile_management(layer, "C:\\GEOS456\\FinalProject\\" + fc + ".lyrx") #creating a folder to hold the layers
##    #we then have to use the arcpy.mp.LayerFile function to create another mp module useable layer for some reason
##    #These layer files are PERMANENT!
##    lyrFile = MAP.LayerFile(lyrFile)
##    #so now, we have a layer files that can be added to the map frame
##    m.addLayer(lyrFile)
##    print(fc + " layer added.")
##aprx.save()
##
##
### generate a list of the layouts within the project
##layout = aprx.listLayouts()[0] # select Bear Habitat layer
##
### list the elements contained in the layout
## # there are LOTS of elements. you'd need to be familiar with them to know to modify them.
##elements = layout.listElements()
##for elem in elements:
##    print(elem.name)
##    print(elem.type)
##
##    # change the map title in the layout
##    if elem.name == "Map Title":
##        elem.text = "Connecting Bear"
##
##    # change/add a title to the legend element
##    if elem.name == "Legend":
##        elem.title = "Legend" ## # will not show since it's not activated
##
####m.zoomToAllLayers(True)
##
### export the final result to a PDF
## #layout is the only thing you can export to a PDF. not the APRX
##layout.exportToPDF(r"C:\GEOS456\FinalProject\GEOS456_FP_Guan_Kristy.pdf")
##
##aprx.save()




#-------------------------------------------------------------------------------
# Grid Statistics
#-------------------------------------------------------------------------------
# Average elevation of Kananaskis Country
# dem?


# The area of each landcover type within the park boundary


# Use a geometry token to print the total length of the optimal routes



# Print the NTS and the TWP-TGE-MER that covers the park





#-------------------------------------------------------------------------------
# Record end time
end = time.time()

# Print the difference between start and end time in seconds
print(f"\nThe time to execute the script was {round(end-start, 2)} seconds!")

print("\nEnd of script.")