#-------------------------------------------------------------------------------
# Name:        Final Project - Connecting Wildlife Habitat
# Purpose:     To incorporate Python functionality learned throughout the semester.
#
# Author:      Kristy Guan
#
# Created:     29/11/2024
# Copyright:   (c) ###### 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time # Import time module
start = time.time()
print("Start of script.\n")

# Import all required modules
import arcpy, os, sys
from arcpy.sa import *
import arcpy.mp as MAP

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


# Function to check and set coordinate system of a single FC
# in_feature is the input feature name
# out_path is the desired output path
# out_cs is the desired output coordinate system
def checkCS_Vector(in_feature, out_path, out_cs):

    # set name
    name = os.path.splitext(os.path.basename(in_feature))[0] #gets file name and remove extension

    print(f"Checking coordinate system for vector feature {name}...")

    sr = arcpy.Describe(in_feature).spatialReference

    # Check Coordinate system
    if sr.name == out_cs.name:
        print(f"{in_feature} is already set in {out_cs.name}...")
        print(f"Saving to gdb...")
        out_feature = arcpy.FeatureClassToFeatureClass_conversion(in_feature, out_path, name)
        messages()
        return out_feature

    elif sr.name == "Unknown":
        print(f"{in_feature} has unknown spatial reference, exiting...")
        exit()

    print(f"{in_feature} is in {sr.name}, projecting to {out_cs.name}...")
    out_feature = arcpy.Project_management(in_feature, os.path.join(out_path, name), out_cs)
    messages()
    return out_feature


#-------------------------------------------------------------------------------
# Main script block
#-------------------------------------------------------------------------------

# Path to required data location
root_path = r"C:\GEOS456\FinalProject"

# Output geodatabase and path for final data
out_gdb = "KananaskisWildlife.gdb" #required name
out_path = os.path.join(root_path, out_gdb)

# Scratch geodatabase and path for intermediate data
scratch_gdb = "Scratch.gdb"
scratch_path = os.path.join(root_path, scratch_gdb)

datasets = ["BaseFeatures", "StudyArea"]
datasets_path = [os.path.join(out_path, datasets[0]), os.path.join(out_path, datasets[1])]

# Output coordinate system
out_cs = arcpy.SpatialReference("NAD 1983 UTM Zone 11N")

# Raster cell size (required)
cell = 25 # in meters

# Name of study area file
study_area = "KCountry_Bound"


#-------------------------------------------------------------------------------
arcpy.env.workspace = root_path

# Create GDB and datasets (will check for and delete existing gdb if necessary)
createGDBandDatasets(root_path, out_gdb, datasets, out_cs) # gdb for final outputs
createGDBandDatasets(root_path, scratch_gdb, "", out_cs) # gdb for intermediate data

print(f"\n{'- - '*20}\n") # print separator line


print("= = = Data Conversion = = =")

# Get Study Area / Kananaskis boundary
for dirpath, _, filenames in arcpy.da.Walk(root_path, datatype="FeatureClass"):
    for filename in filenames:

        # Check if "KCountry_Bound" is in the filename (ignore file extension)
        if "KCountry_Bound" in filename and filename.lower().endswith(".shp"):
            file_path = os.path.join(dirpath, filename)
            print(f"Found shapefile: {file_path}\n")

            # check the coordinates system and save to final gdb
            study_area_path = checkCS_Vector(file_path, out_path, out_cs)
            print(study_area_path, "\n")



# Project/Clip all data and store in gdb (From root folder to Scratch gdb to Output gdb)
for dirpath, dirnames, filenames in arcpy.da.Walk(root_path, datatype=["FeatureClass", "RasterDataset"]):
    arcpy.env.workspace = dirpath

    if dirpath.endswith(".gdb"):
        continue #skips this directory


    for filename in filenames:

        # Skip study area
        if study_area in filename:
            continue # skils this file


        if filename.lower().endswith(".shp"):  # Check if it's a shapefile

            print(f"Processing Shapefile: {filename}\n")

            name = os.path.splitext(filename)[0]

            # check coordinate system and save to scratch gdb
            intermediate = checkCS_Vector(filename, scratch_path, out_cs)

            # clip to boundary and save to output gdb
            print(f"Clipping to the boundary... ")
            arcpy.analysis.Clip(in_features=intermediate, clip_features=study_area_path, out_feature_class=os.path.join(out_path, name))
            messages()

        elif filename.lower().endswith(".bnd"):
            rasters = arcpy.ListRasters()
            for raster in rasters:
                print(f"Processing raster: {raster}\n")
                print(f"Saving raster to {scratch_gdb}...")
                arcpy.conversion.RasterToOtherFormat(Input_Rasters=os.path.join(dirpath, raster), Output_Workspace=scratch_path)
                messages()

                print("Projecting raster...")
                out_raster_path = os.path.join(scratch_path, f"{raster}_projected")
                arcpy.management.ProjectRaster(in_raster=os.path.join(scratch_path, raster),out_raster=out_raster_path, out_coor_system=out_cs, cell_size=cell)

                print("Extract by Mask with park boundary...")
                out_extract = ExtractByMask(in_raster=out_raster_path, in_mask_data=study_area_path)
                messages()

                print(f"Saving raster to {out_gdb}...")
                out_extract.save(os.path.join(out_path, raster))
                messages()

print()

# Delete scratch gdb and all intermediate data
try:
    print(f"Deleting {scratch_gdb} along with all intermediate data...")
    arcpy.Delete_management(scratch_path)
    messages()
except Exception as e:
    print(f"Failed to delete {scratch_gdb}: {e}")

print(f"\n{'- - '*20}\n") # print separator line


#-------------------------------------------------------------------------------
# Optimal Routes Parameters
# Scale ranking from 1 (most desirable) to 10 (least desirable)
#-------------------------------------------------------------------------------

arcpy.env.workspace = out_path


print("= = = Cost Analysis = = =")

#-------------------------------------------------------------------------------
# Landcover - Characteristics of the area being traversed (shp)

print("Processing Landcover:")
print("Converting from polygon to raster...")
in_features="AB_Landcover"
value_field="LC_class"
out_rasterdataset = in_features +"_Ras"
arcpy.conversion.PolygonToRaster(in_features, value_field, out_rasterdataset, cellsize=cell)
messages()

landcover = arcpy.Raster(out_rasterdataset)
#reclassify the land cover
remap = RemapValue([
    ['20', 10],
    ['31', 8],
    ['32', 7],
    ['33', 6],
    ['34', 10],
    ['50', 3],
    ['110', 2],
    ['120', 9],
    ['210', 1],
    ['220', 1],
    ['230', 1]
])

# Apply reclassification
print("Reclassifying...")
landcover_reclass = Reclassify(landcover, "VALUE", remap, "DATA")
messages()

#save the reclassified land cover
print("Saving raster...")
landcover_reclass.save(f"{in_features}_Reclass")
messages()

print(f"Deleting {out_rasterdataset}...")
arcpy.management.Delete(landcover)
messages()

#-------------------------------------------------------------------------------
# Hydrology, Trails, Roads
# - Use Distance Accumulation tool (outputs a continuous raster)
# - Use the Rescale by Function tool to apply a continuous cost value between 0-10

# Set the environment
arcpy.env.extent = study_area # makes sure the rasters cover the whole boundary extent
arcpy.env.mask = study_area # makes sure the rasters don't extend beyond the boundary
arcpy.env.cellSize = cell # makes sure the rasters are outputted in this cell size

#-------------------------------------------------------------------------------
# Hydrology - (desirable)
print("Processing Hydrology:")
print("Computing Distance Accumulation...")
hydro_dist = DistanceAccumulation("Hydro")
messages()
print("Rescale by Function...")
hydro_rescale = RescaleByFunction(hydro_dist, "TfLarge", 10, 1) # small=1 / close is preferred
messages()

print("Saving raster...")
hydro_rescale.save("Hydro_Rescaled")
messages()

print("Deleting Hydro Dist...")
arcpy.management.Delete(hydro_dist)
messages()

#-------------------------------------------------------------------------------
# Trails - (avoid)
print("Processing Trails:")

print("Computing Distance Accumulation...")
trails_dist = DistanceAccumulation("Trails")
messages()

print("Rescale by Function...")
trails_rescale = RescaleByFunction(trails_dist, "TfLarge", 1, 10) # large=1 / far away is preferred
messages()

print("Saving raster...")
trails_rescale.save("Trails_Rescaled")
messages()

print("Deleting Trails Dist...")
arcpy.management.Delete(trails_dist)
messages()

#-------------------------------------------------------------------------------
# Road - (avoid)
print("Processing Roads: ")
# Merge Road and Transportation
print("Merging Road with Transportation...")
road_merge = arcpy.management.Merge(["Road", "Transportation"], "Road_Merged")
messages()

print("Computing Distance Accumulation...")
road_dist = DistanceAccumulation(road_merge)
messages()
print("Rescale by Function...")
road_rescale = RescaleByFunction(road_dist, "TfLarge", 1, 10) # large=1 / far away is preferred
messages()

print("Saving raster...")
road_rescale.save("Road_Rescaled")
messages()

print("Deleting Road Merged...")
arcpy.management.Delete(road_merge)
messages()

print("Deleting Transportation...")
arcpy.management.Delete("Transportation")
messages()

print("Deleting Roads Dist...")
arcpy.management.Delete(road_dist)
messages()


#-------------------------------------------------------------------------------
# Terrain Ruggedness (dem) - (avoid rugged terrain)
# Rescale by Function

dem = arcpy.Raster("ab_dem")

print("Processing DEM to get Terrain ruggedness: ")

# Generate the terrain ruggedness
print("Computing Focal Statistics...")
terrainRug = FocalStatistics(dem, NbrRectangle(3,3,"CELL"), "RANGE")
messages()

print("Saving raster...")
terrainRug.save("TerrainR") #save to gdb
messages()

# Use the Rescale By Function to assign the classes to the continuous rasters
print("Rescale by Function...")
terrainRug_rescale = RescaleByFunction(terrainRug, "TfLarge", 10, 1) # small=1 / low ruggedness is preferred
messages()

print("Saving raster...")
terrainRug_rescale.save("TerrainR_Rescaled")
messages()


#-------------------------------------------------------------------------------
# Combine the cost surfaces into one single cost raster
# All weights are equal to 1


#combine all rescaled and reclassified rasters together using weighted sum
print("Computing weighted sum...")
weighted_sum = WeightedSum(WSTable([[landcover_reclass, 'Value', 1], \
    [hydro_rescale, 'Value', 1], [trails_rescale, 'Value', 1], \
    [road_rescale, 'Value', 1], [terrainRug_rescale, 'Value', 1]]))
messages()

#save the weighted sum
print("Saving raster...")
weighted_sum.save("Combined_Cost")
messages()

#create the routes with the optimal region connections tool
print("Computing optimal path...")
optimal_routes = OptimalRegionConnections("Bear_Habitat", "Optimal_Routes", "", weighted_sum)
messages()


#-------------------------------------------------------------------------------
# Delete intermediate data (reclass, rescale, cost rasters)

rasters = arcpy.ListRasters()
for raster in rasters:
    if "Rescale" in raster or "Reclass" in raster or "Cost" in raster:
        try:
            # Delete the raster
            print(f"Deleted raster: {raster}")
            arcpy.management.Delete(raster)
            messages()
        except Exception as e:
            print(f"Error deleting raster {raster}: {e}")


#-------------------------------------------------------------------------------
# Mapping
#-------------------------------------------------------------------------------

print("= = = Map Creation = = =")

arcpy.env.workspace = out_path

#reference the aprx document using the mapping modules
aprx = MAP.ArcGISProject(r"C:\GEOS456\FinalProject\GEOS456_FinalProject.aprx") #path to aprx doc

#save a copy of the aprx so we can preserve the original
aprx.saveACopy(r"C:\GEOS456\FinalProject\GEOS456_FinalProject_Original.aprx")

#save a specific map frame as a variable to reference in the script
m = aprx.listMaps("Map")[0] #Sets m to 'Map' from index position 0 within list

#use the mapping module to add layers
listFC = ["KCountry_Bound", "Bear_Habitat", "Optimal_Routes"]
for fc in listFC:
    #first step in the loop is to create feature layers form the list
    layer = arcpy.MakeFeatureLayer_management(fc)
    #next, we will save the feature layers as .lyrx files
    lyrFile = arcpy.SaveToLayerFile_management(layer, "C:\\GEOS456\\FinalProject\\" + fc + ".lyrx") #creating a folder to hold the layers
    #we then have to use the arcpy.mp.LayerFile function to create another mp module useable layer for some reason
    #These layer files are PERMANENT!
    lyrFile = MAP.LayerFile(lyrFile)
    #so now, we have a layer files that can be added to the map frame
    m.addLayer(lyrFile)
    print(fc + " layer added.")


# generate a list of the layouts within the project
layout = aprx.listLayouts()[0] # select Bear Habitat layer

# list the elements contained in the layout
elements = layout.listElements()
for elem in elements:
    # change the map title in the layout
    if elem.name == "Map Title":
        print("Changing Map title...")
        elem.text = "Connecting Bear Habitats"

    # change/add a title to the legend element
    if elem.name == "Legend":
        print("Changing Legend title...")
        elem.title = "Legend"


# "zoom to" KCountry_Bound layer
lyr = m.listLayers("KCountry_Bound_Layer")[0]
lyt = aprx.listLayouts()[0]
mf = lyt.listElements("mapframe_element")[0]
mf.camera.setExtent(mf.getLayerExtent(lyr,True))
aprx.save()

# export the final result to a PDF
print("Exporting to PDF...")
layout.exportToPDF(r"C:\GEOS456\FinalProject\GEOS456_FP_Guan_Kristy.pdf")
messages()

aprx.save()


print(f"\n{'- - '*20}\n") # print separator line

#-------------------------------------------------------------------------------
# Grid Statistics
#-------------------------------------------------------------------------------
arcpy.env.workspace = out_path

print("= = = Grid Statistics = = =")

# Average elevation of Kananaskis Country

InZoneData = study_area
ZoneField = "GEONAME" #any field since it's 1 polygon
InValueRaster = dem
OutTable = "ab_dem_stats"
StatsType = "MEAN"

print("\nZonal Statistics to compute the average elevation of the park...")
ZonalStatisticsAsTable(InZoneData, ZoneField, InValueRaster, OutTable, "", StatsType)
messages()

with arcpy.da.SearchCursor(OutTable, ["MEAN"]) as scursor:
    for row in scursor:
        print(f"The average elevation of Kananaskis Country is {round(row[0], 2):,} meters.")


#-------------------------------------------------------------------------------
# The area of each landcover type within the park boundary

# Use landcover polygon
in_table="AB_Landcover"
out_table=in_table+"_stats"
statistics_fields="Shape_Area SUM"
case_field="LC_class"

print("\nSummary statistics to compute total area of each landcover type...")
arcpy.analysis.Statistics(in_table, out_table, statistics_fields, case_field)
messages()

with arcpy.da.SearchCursor(out_table, ["LC_class", "SUM_Shape_Area"]) as scursor:
    print("The area of each landcover type:")
    for row in scursor:
        print(f"\tLandcover type {row[0]} | Total Area: {round(row[1], 2):,} m2")


#-------------------------------------------------------------------------------
# Use a geometry token to print the total length of the optimal routes
with arcpy.da.SearchCursor(optimal_routes, ["REGION1", "REGION2","SHAPE@LENGTH"]) as scursor:
    total = 0
    print(f"\nLength of the optimal routes: ")
    for row in scursor:
        print(f"\tFrom Region {row[0]} to Region {row[1]}: {round(row[2], 2):,} meters")
        total += row[2]
    print(f"Total length of the optimal routes: {round(total, 2):,} meters")

#-------------------------------------------------------------------------------
# Print the NTS and the TWP-TGE-MER that covers the park

nts = "NTS50"
print("\nGetting NTS grid count...")
row_count = arcpy.management.GetCount(nts)
messages()
with arcpy.da.SearchCursor(nts, ["NAME"]) as scursor:
    print(f"There are {row_count} NTS grids covering the park: ")
    for row in scursor:
        print(f"\t{row[0]}")


township = "AB_Township"
print("\nGetting township count...")
row_count = arcpy.management.GetCount(township)
messages()
with arcpy.da.SearchCursor(township, ["DESCRIPTOR"]) as scursor:
    print(f"There are {row_count} Townships covering the park: ")
    for row in scursor:
        print(f"\t{row[0]}")

print()


#-------------------------------------------------------------------------------
# Final datasets
#-------------------------------------------------------------------------------

# Generate a list of final datasets, rasters and tables
print("= = = Final Datasets = = =")

arcpy.env.workspace = out_path

fcList = arcpy.ListFeatureClasses()
if fcList: #is not empty
    print("\nList of feature classes: ")
    for fc in fcList:
        desc = arcpy.Describe(fc)
        print(f"\tFeature class: {fc} | Geometry: {desc.shapeType} | Spatial Reference: {desc.spatialReference.name}")
else:
    print("No feature classes found.")

rasters = arcpy.ListRasters()
if rasters:
    print("\nList of rasters: ")
    for raster in rasters:
        # Get cell size and spatial reference
        desc = arcpy.Describe(raster)
        print(f"\tRaster: {raster} | Cell size: {desc.meanCellWidth} | Spatial Reference: {desc.spatialReference.name}")
else:
    print("No rasters found.")


# List tables (non-spatial data)
tables = arcpy.ListTables()
if tables:
    print("\nList of tables: ")
    for table in tables:
        print(f"\tTable: {table}")
else:
    print("No tables found.")

print(f"\n{'- - '*20}\n") # print separator line

#-------------------------------------------------------------------------------
# Check in the extension
arcpy.CheckInExtension("Spatial")

#-------------------------------------------------------------------------------
# Record end time
end = time.time()
total_seconds = end-start
minutes = int(total_seconds // 60)  # Get the number of full minutes
seconds_remain = round(total_seconds % 60, 2)
# Print the difference between start and end time in seconds
print(f"\nThe time to execute the script was {minutes} min and {seconds_remain} seconds!")

print("\nEnd of script.")
