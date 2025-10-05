#-------------------------------------------------------------------------------
# Name:        Assignment 2: Geoprocessing for Map Overlays
# Purpose:     To automate the data conversion and manipulation process of
#              base features.
#
# Author:      Kristy Guan
#
# Created:     27/09/2024
# Completed:   21/10/2024
# Copyright:   (c) 954512 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Import all required modules
import arcpy, os, sys

import time # Import time module
start = time.time() # Record start time. reference: https://www.geeksforgeeks.org/how-to-check-the-execution-time-of-python-script/
print("Start of script.\n")

# Set the overwrite outputs environment
arcpy.env.overwriteOutput = True #allow overwriting files, default is False


#-------------------------------------------------------------------------------
# Functions
#-------------------------------------------------------------------------------

# Function to print out the last message from a Function Tool
def messages():
    count = arcpy.GetMessageCount()
    print(arcpy.GetMessage(count-1), "\n")


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
        if "RA" in fc:
            print("Skipping RA (road allowance).\n")
        else:
            setCSAndSaveToGDB(fc, out_path, out_cs)


# Function to check and set coordinate system
# in_feature is the input feature name
# out_path is the desired output path
# out_cs is the desired output coordinate system
def setCSAndSaveToGDB(in_feature, out_path, out_cs):

    geom_typ = arcpy.Describe(in_feature).shapeType
    sr = arcpy.Describe(in_feature).spatialReference

    # set name
    if "Point" in in_feature: #fix name of GPS Point
        name = "GPS_Point"
    else:
        name = setName(in_feature)

    # Check Coordinate system
    if sr == out_cs:
        print(f"{in_feature} is already set in {out_cs.name}...")
        print(f"Saving to gdb...")
        arcpy.FeatureClassToFeatureClass_conversion(in_feature, out_path, name)
        messages()
        return
    elif sr.name == "Unknown": # reference: https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/spatialreference.htm
        print(f"{in_feature} has unknown spatial reference, exiting...")
        exit()

    print(f"{in_feature} is in {sr.name}, projecting to {out_cs.name}...")
    arcpy.Project_management(in_feature, os.path.join(out_path, name), out_cs)
    messages()


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
root_path = r"C:\GEOS456\Assign02"

# Name of folders containing fc
folders = ["Base", "DLS"]
folders_path = [os.path.join(root_path,folders[0]), os.path.join(root_path,folders[1])]

# Output geodatabase and path for final data
out_gdb = "Assignment02.gdb" #required name
out_path = os.path.join(root_path, out_gdb)

# Scratch geodatabase and path for intermediate data
scratch_gdb = "Scratch.gdb"
scratch_path = os.path.join(root_path, scratch_gdb)

# Output coordinate system
out_cs = arcpy.SpatialReference("NAD 1983 UTM Zone 11N")


# Delete existing geodatabases
checkExistandDelete(root_path, out_gdb)
checkExistandDelete(root_path, scratch_gdb)


# List of all FC (shapefile)
for dirpath, dirnames, filenames in os.walk(root_path): # reference: https://docs.python.org/3/library/os.html
    arcpy.env.workspace = dirpath

    fcList = arcpy.ListFeatureClasses()

    print(f"List of feature classes from {dirpath}:")
    for fc in fcList:
        print("\t", fc) #prints one feature class from the list

        # Describe data type, geometry, and spatial reference of each shapefile
        fcDesc = arcpy.Describe(fc)
        print(f"\t\t Data Type: {fcDesc.dataType}")
        print(f"\t\t Geometry: {fcDesc.shapeType}")
        print(f"\t\t Spatial Reference: {fcDesc.spatialReference.name}")
        print()


# Create GDB and datasets (will check for and delete existing gdb if necessary)
createGDBandDatasets(root_path, out_gdb, folders, out_cs) # gdb for final outputs
createGDBandDatasets(root_path, scratch_gdb, folders, out_cs) # gdb for intermediate data


# Convert/project all data and store in gdb and appropriate feature datasets
# From root folder (contains GPS Point) to Scratch gdb
saveToGDB(in_path=root_path, out_path=scratch_path, out_cs=out_cs)
# From Base folder to Scratch gdb
saveToGDB(in_path=folders_path[0], out_path=os.path.join(scratch_path, folders[0]), out_cs=out_cs)
# From DLS folder to Scratch gdb
saveToGDB(in_path=folders_path[1], out_path=os.path.join(scratch_path, folders[1]), out_cs=out_cs)


#-------------------------------------------------------------------------------
arcpy.env.workspace = scratch_path

# Export GPS Point to final output gdb
gps_point = "GPS_Point"
print(f"Exporting GPS Point to {out_gdb}...")
arcpy.ExportFeatures_conversion(gps_point, os.path.join(out_path, gps_point))
messages()


# Identify the Township (TWP) and name it Study_Area using Select Layer by Location.
# reference: https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-location.htm

twp = os.path.join(folders[1], "TWP")

try:
    print("Selecting Township intersecting wtih GPS Point...")
    select_layer = arcpy.SelectLayerByLocation_management(twp, "INTERSECT", gps_point)
    messages()
    print(f"Exporting selected Township to {out_gdb} and renaming it to Study_Area... ")
    study_area = arcpy.ExportFeatures_conversion(select_layer, os.path.join(*[out_path, folders[1], "Study_Area"]))
    messages()
    print("Deleting old TWP feature class... ")
    arcpy.Delete_management(os.path.join(folders[1], "TWP"))
    messages()
except Exception as e:
    print(f"Failed to retrieve Study Area: {e}")

# Clip all feature classes with Study Area
try:
    datasets = arcpy.ListDatasets(feature_type='feature') # reference: https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/listfeatureclasses.htm

    for dataset in datasets:
        fcList = arcpy.ListFeatureClasses("","",dataset)

        for fc in fcList:
            print(f"Clipping {fc} with Study Area...")
            arcpy.Clip_analysis(fc, study_area, os.path.join(*[out_path, dataset, fc]))
            messages()
except Exception as e:
    print(f"Failed to clip all features: {e}")


#-------------------------------------------------------------------------------
arcpy.env.workspace = out_path

# List of FC in each dataset and describe final spatial reference
datasets = arcpy.ListDatasets()
print(f"List of all feature classes from {out_gdb}:")
for dataset in datasets:
    fcList = arcpy.ListFeatureClasses("", "", dataset)
    print(f"From {dataset} dataset:")
    for fc in fcList:
        print(f"\t {fc}") #prints one feature class from the list

        fcDesc = arcpy.Describe(fc)
        print(f"\t\t Spatial Reference: {fcDesc.spatialReference.name}")
        print()

# Get LSD that intersects GPS Point
try:
    print("Selecting LSD intersecting wtih GPS Point...")
    lsd_location = arcpy.SelectLayerByLocation_management(os.path.join(folders[1], "LSD"), "INTERSECT", gps_point)
    messages()

    # Use search cursor to obtain full LSD description
    scursor = arcpy.da.SearchCursor(lsd_location, ["LSD", "QTR", "SEC", "TWP", "RGE", "MER"])

    print("Full LSD description for GPS location: ") # should be LSD5 - SW31 - TWP21 - RGE25 - 4
    for row in scursor:
        print(f"\tLSD{row[0]} - {row[1]}{row[2]} - TWP{row[3]} - RGE{row[4]} - {row[5]} \n")
except Exception as e:
    print(f"Failed to retrieve LSD description: {e}")

#-------------------------------------------------------------------------------

# Remove locks by deleting selected layers and references
print("Deleting Selected Layers and references to remove lock:")
try:
    print("Deleting selected TWP layer...")
    arcpy.Delete_management(select_layer)
    messages()
    print("Deleting selected LSD layer...")
    arcpy.Delete_management(lsd_location)
    messages()
    del select_layer, study_area, lsd_location
except Exception as e:
    print(f"Failed to delete all select_layers and references: {e}")

# Delete scratch gdb and all intermediate data
try:
    print(f"Deleting {scratch_gdb} along with all intermediate data...")
    arcpy.Delete_management(scratch_path)
    messages()
except Exception as e:
    print(f"Failed to delete {scratch_gdb}: {e}")


#-------------------------------------------------------------------------------
# Record end time
end = time.time()

# Print the difference between start and end time in seconds
print(f"The time to execute the script was {round(end-start, 2)} seconds!")

print("End of script.")