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

# Set the overwrite outputs environment
arcpy.env.overwriteOutput = True #allow overwriting files, default is False

# Check out the Spatial extension
arcpy.CheckOutExtension("Spatial")

#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

# Function to print out the first and last message from a Function Tool
def messages():
    print(arcpy.GetMessages(0)) # print first message of tool
    count = (arcpy.GetMessageCount())
    print(arcpy.GetMessages(count-1)) # print last message of tool


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

##    setCSAndSaveToGDB(fc, out_path, out_cs)


### Function to check and set coordinate system
### in_feature is the input feature name
### out_path is the desired output path
### out_cs is the desired output coordinate system
##def setCSAndSaveToGDB(in_feature, out_path, out_cs):
##
##    geom_typ = arcpy.Describe(in_feature).shapeType
##    sr = arcpy.Describe(in_feature).spatialReference
##
##    # set name
##    if "Point" in in_feature: #fix name of GPS Point
##        name = "GPS_Point"
##    else:
##        name = setName(in_feature)
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


# Function to clean up file names
# It will remove the file extension and leading digits from the filename
def setName(name):
    # extract file name without file extension
    name = os.path.splitext(name)[0]
    # remove digits at beginning of name
    if name[0].isdigit():
        name = name.split("_", 1)[1]
    return name


#-------------------------------------------------------------------------------
# Main script block
#-------------------------------------------------------------------------------

# Path to required data location
root_path = r"C:\GEOS456\FinalProject"

# Name of folders containing fc
##folders = ["Base", "DLS"]
##folders_path = [os.path.join(root_path,folders[0]), os.path.join(root_path,folders[1])]

ats = "ATS"
dem = "DEM"
kananaskis = "Kananaskis"
landcover = "Landcover"
nts = "NTS"
wildlife = "Wildlife"




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

# Delete existing geodatabases
checkExistandDelete(root_path, out_gdb)
checkExistandDelete(root_path, scratch_gdb)

# Create GDB and datasets (will check for and delete existing gdb if necessary)
createGDBandDatasets(root_path, out_gdb, "", out_cs) # gdb for final outputs
createGDBandDatasets(root_path, scratch_gdb, "", out_cs) # gdb for intermediate data


# Convert/project all data and store in gdb (From root folder to Scratch gdb)
##saveToGDB(in_path=root_path, out_path=scratch_path, out_cs=out_cs)
### From Base folder to Scratch gdb
##saveToGDB(in_path=folders_path[0], out_path=os.path.join(scratch_path, folders[0]), out_cs=out_cs)
### From DLS folder to Scratch gdb
##saveToGDB(in_path=folders_path[1], out_path=os.path.join(scratch_path, folders[1]), out_cs=out_cs)



### List of all FC (shapefile)
##for dirpath, dirnames, filenames in os.walk(root_path): # reference: https://docs.python.org/3/library/os.html
##    arcpy.env.workspace = dirpath
##
##    fcList = arcpy.ListFeatureClasses()
##
##    print(f"List of feature classes from {dirpath}:")
##    for fc in fcList:
##        print("\t", fc) #prints one feature class from the list
##
##        # Describe data type, geometry, and spatial reference of each shapefile
##        fcDesc = arcpy.Describe(fc)
##        print(f"\t\t Data Type: {fcDesc.dataType}")
##        print(f"\t\t Geometry: {fcDesc.shapeType}")
##        print(f"\t\t Spatial Reference: {fcDesc.spatialReference.name}")
##        print()


### Use Walk to iterate through the directory structure
##for dirpath, dirnames, filenames in arcpy.da.Walk(root_path, datatype="FeatureClass"):
##    arcpy.env.workspace = dirpath
##
##    fcList = arcpy.ListFeatureClasses()
##
##    print(f"List of feature classes from {dirpath}:")
##    for fc in fcList:
##        print("\tFC", fc) #prints one feature class from the list
##
##        geom_typ = arcpy.Describe(in_feature).shapeType
##        sr = arcpy.Describe(in_feature).spatialReference
##
##        # Check Coordinate system
##        if sr == out_cs:
##            print(f"{fc} is already set in {out_cs.name}...")
##            print(f"Saving to gdb...")
##            arcpy.conversion.FeatureClassToFeatureClass(in_features=os.path.join(dirpath, filename), out_path=scratch_path, out_name=fc)
##            messages()
##            return
##        elif sr.name == "Unknown": # reference: https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/spatialreference.htm
##            print(f"{in_feature} has unknown spatial reference, exiting...")
##            exit()
##
##        arcpy.management.Project(in_dataset, out_dataset, out_coor_system=out_cs)
##        messages()





##    print(f"dirpath {dirpath} \n\tdirname {dirnames}\n")
##    for filename in filenames:
##        print("\tfilename", filename, "\n")
##
##
##        fc_path = os.path.join(dirpath, filename)
##        desc = arcpy.da.Describe(fc_path)
##        print("desc", desc)
##
##        if desc['shapeType'] == ("Polygon" or "Polyline"):
##            print(f"{fc_path} is a {desc.shapeType} feature class.")
##        else:
##            print(f"{fc_path} is not a Polygon or Polyline feature class. ----------------------------------")
##
##        arcpy.conversion.FeatureClassToFeatureClass(in_features=os.path.join(dirpath, filename), out_path=scratch_path, out_name=filename)
##        arcpy.FeatureClassToFeatureClass_conversion(in_feature, out_path, name)
##        arcpy.analysis.Clip(in_features=filename, clip_features="Bear_Habitat", out_feature_class=save_path)






#-------------------------------------------------------------------------------
# Criteria

# Terrain (dem)
##dem = arcpy.Raster("dem")

# Landcover - Characteristics of the area being traversed (shp)
# clip



# Proximity to existing features/infrastructure (shp)
# Proximity to hydrology (shp)

# roads, trails, hydrology must be included







# Check in the extension
arcpy.CheckInExtension("Spatial")

print("\nEnd of script.")