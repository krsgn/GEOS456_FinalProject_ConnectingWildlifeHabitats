#-------------------------------------------------------------------------------
# Name:        Assignment 5
# Purpose:     Create a custom tool that will allow for user input to determine
#              results from a variety of crime types.
# Author:      Kristy Guan
#
# Created:     14/11/2024
# Copyright:   (c) 954512 2024
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# Import required modules
import arcpy, os
arcpy.env.overwriteOutput = True

# The workspace is the default GDB of the APRX ????????
arcpy.env.workspace = r"C:\GEOS456\Assign05\City_of_Nice_Place.gdb"

# Files hidden from users
precincts = "Precincts"
landmarks = "Landmarks"


# Use the get parameter as text and store those in variables
cr_arsons = arcpy.GetParameterAsText(0) # file path to arsons
cr_assault = arcpy.GetParameterAsText(1) # file path to assault
cr_burgl = arcpy.GetParameterAsText(2) # file path to burglaries
bufdist = arcpy.GetParameterAsText(3) # Linear Unit, string

# Create crime types list
crime_types = [cr_arsons, cr_assault, cr_burgl]

# Split the string and convert the first part to an integer
bufdist_num = int(bufdist.split()[0])

#-------------------------------------------------------------------------------
# Part 1 - Frequency of each crime type in each precinct
#-------------------------------------------------------------------------------

# FOR loop to intersect each crime type with the precincts
for crime in crime_types:

    # Get and format crime name
    crime_name = os.path.basename(crime)
    crime_name = crime_name.capitalize() # make sure name starts with a capital letter

    # Create output name for each crime
    pr_crime_name = "Precincts_" + crime_name

    # Intersect Precincts with crime
    arcpy.SetProgressor("default",f"Intersecting Precincts with {crime_name}...")
    pr_crime = arcpy.analysis.Intersect(in_features=[precincts, crime], out_feature_class=pr_crime_name)

    # Create Frequency tables of crimes per precincts
    arcpy.SetProgressor("default",f"Generating frequency table of {crime_name} in Precinct...")
    pr_crime_freq = arcpy.analysis.Frequency(in_table=pr_crime, out_table=pr_crime_name+"_Frequency", frequency_fields="Precinct")

    # Sort Frequency tables by Frequency, Ascending
    arcpy.SetProgressor("default", f"Sorting frequency table of {crime_name} in Precinct in Ascending Order by Frequency...")
    pr_crime_sort = arcpy.management.Sort(in_dataset=pr_crime_freq, out_dataset=pr_crime_name+"_Sorted", sort_field=[["FREQUENCY", "ASCENDING"]])

    # Delete Frequency tables
    arcpy.SetProgressor("default", f"Deleting unsorted frequency table of {crime_name} in Precinct...")
    arcpy.Delete_management(pr_crime_freq)

    # Print table
    arcpy.AddMessage(f"Frequency Table of {crime_name} in Precincts (in Ascending Order): ")
    with arcpy.da.SearchCursor(pr_crime_sort, ["Precinct", "FREQUENCY"]) as scursor:
        for row in scursor:
            arcpy.AddMessage(f"\tPrecinct: {row[0]} | Total {crime_name}: {row[1]}")

    arcpy.AddMessage(f"\n{'- - '*20}\n") # print separator line

#-------------------------------------------------------------------------------
# Part 2 - Assaults around landmarks
#-------------------------------------------------------------------------------

# Get assault file name for output
cr_assault_name = os.path.basename(cr_assault)
# Create output name
lm_assault_name = "Landmarks_" + cr_assault_name

#-------------------------------------------------------------------------------
# Part 2A - Total number of assaults within 250m of all landmarks
#-------------------------------------------------------------------------------

# Generate Buffer, Dissolved
arcpy.SetProgressor("default", f"Generating dissolved buffer at {bufdist_num} meters around Landmarks...")
lm_buf = arcpy.analysis.Buffer(in_features=landmarks, out_feature_class=f"Landmarks_Buffer_Dissolved_{str(bufdist_num)}m", buffer_distance_or_field=bufdist, dissolve_option="ALL")

# Intersect dissolved Landmarks buffer with assault
arcpy.SetProgressor("default", f"Intersecting Buffered Landmarks with {cr_assault_name}...")
lm_assault = arcpy.analysis.Intersect(in_features=[lm_buf, cr_assault], out_feature_class=f"Landmarks_{cr_assault_name}")

# Create Summary table for all assaults around Landmarks
arcpy.SetProgressor("default", f"Generating Summary table for total number of {cr_assault_name} around all Landmarks at {bufdist}...")
lm_assault_sum = arcpy.analysis.Statistics(in_table=lm_assault, out_table=lm_assault_name+"_Summary", statistics_fields="FID_Assault COUNT")

# Print answer
with arcpy.da.SearchCursor(lm_assault_sum, ["FREQUENCY"]) as scursor:
    for row in scursor:
        arcpy.AddMessage(f"Total number of assaults around all Landmarks within {bufdist}: {row[0]}")
arcpy.AddMessage(f"\n{'- - '*20}\n") # print separator line

# Delete Dissolved Buffer FC
arcpy.SetProgressor("default", f"Deleting intermediate data: {os.path.basename(lm_buf.getOutput(0))}...")
arcpy.Delete_management(lm_buf)
arcpy.SetProgressor("default", f"Deleting intermediate data: {os.path.basename(lm_assault.getOutput(0))}...")
arcpy.Delete_management(lm_assault)
arcpy.SetProgressor("default", f"Deleting intermediate data: {os.path.basename(lm_assault_sum.getOutput(0))}...")
arcpy.Delete_management(lm_assault_sum)

#-------------------------------------------------------------------------------
# Part 2B - Landmark with the most assaults
#-------------------------------------------------------------------------------

# Generate Buffer, no dissolve
arcpy.SetProgressor("default", f"Generating buffer at {bufdist_num} meters around Landmarks...")
lm_buf = arcpy.analysis.Buffer(in_features=landmarks, out_feature_class=f"Landmarks_Buffer_{str(bufdist_num)}m", buffer_distance_or_field=bufdist)

# Intersect Landmarks buffer with assault
arcpy.SetProgressor("default", f"Intersecting Buffered Landmarks with {cr_assault_name}...")
lm_assault = arcpy.analysis.Intersect(in_features=[lm_buf, cr_assault], out_feature_class=f"Landmarks_{cr_assault_name}")

# Create frequency tables of assaults per landmarks
arcpy.SetProgressor("default", f"Generating Frequency table of {cr_assault_name} around Landmarks at {bufdist}...")
lm_assault_freq = arcpy.analysis.Frequency(in_table=lm_assault, out_table=lm_assault_name+"_Frequency", frequency_fields="LANDNAME")

# Sort frequency tables by Frequency, Descending
arcpy.SetProgressor("default", f"Sorting Frequency table of {cr_assault_name} around Landmarks at {bufdist} in Descending Order by Frequency...")
lm_assault_sort = arcpy.management.Sort(in_dataset=lm_assault_freq, out_dataset=lm_assault_name+"_Sorted", sort_field=[["FREQUENCY", "DESCENDING"]])

# Delete unsorted frequency table
arcpy.SetProgressor("default", f"Deleting unsorted Frequency table of {cr_assault_name} around Landmarks...")
arcpy.Delete_management(lm_assault_freq)

# Print answer
arcpy.AddMessage(f"Landmark(s) with the most assaults:")
max_value = -1
with arcpy.da.SearchCursor(lm_assault_sort, ["FREQUENCY", "LANDNAME"]) as scursor:
    for row in scursor:
        if row[0] >= max_value:
            max_value = row[0]
            arcpy.AddMessage(f"\tLandmark Name: {row[1]} | Total assaults: {row[0]}")
        else:
            break

arcpy.AddMessage(f"\n{'- - '*20}\n") # print separator line

# -------------------------------------------------------------------------------

print("End of script.")