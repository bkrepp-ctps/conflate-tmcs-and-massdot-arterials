# generate_tmc_events_for_arterials.py
#
# Usage: generate_tmc_events_for_arterials <MassDOT_route_id>
#
# This script does the following:
#     1. For a given MassDOT "route pair" (see below) generate an intermediate
#        CSV file containing the "overlay" of the following events onto it:
#           a. INRIX TMCs
#           b. Towns
#           c. Speed Limit
#           d. Number of travel lanes
#     2. Process the CSV file generated from step (1), producing a final output
#        CSV file containing one record per TMC. 
#
# Parameters
#   1. MassDOT "route_id root", i.e., the portion of a MassDOT route_id 
#      that specifies the "Route System" and "Route Number", but NOT
#      the route direction. For example, given a MassDOT route_id of 
#      "SR9 EB", its "roue_id root" is "SR9".
#   2. The route's primary direction, either 'NB' or 'EB'.
#   3. A file containing a list of TMC ID's whose corresponing 'Speed Limit'
#      and 'Number of Travel Lanes' features are to be located against
#      the specified route pair.
#
# NOTE: Parameters (1) and (2) are sufficient to create a query string that
#      will select the desired route pair (primary and secondary direction.)
#
# NOTE:process_csv_file.py depends upon the following modules:
#     1. csv
#     2. math
#     3. pydash
#     4. ma_towns
# The first two are standard modules, part of any standard Python installation.
# The third, pydash", requires explicit installation.
# We include an explicit "try: import pydash..." at the beginning of this module, 
# in order to notify the user if this library is not installed, and then exit.
# The fourth resides in the same directory as this script and process_csv_file.py.
#
# This script is derived from generate_tmc_events_for_expressways.py.
# At least at the current time, it is designed to support arterial routes that
# are either state routes or US routes.
# 
# Ben Krepp, attending metaphysician
# 03/11-12/2020
# ---------------------------------------------------------------------------

import arcpy
import process_csv_file

try:
    import pydash
except:
    arcpy.AddMessage("This script requires the pydash package, which is not installed on the computer running this script.")
    arcpy.AddMessage("Please have your System Administrator install the pydash package, and re-launch this script.")
    arcpy.AddMessage("The command to install pydash has the form: '<python_installation_directory>\PythonNN -m pip install pydash'")
    arcpy.AddError("Error: pydash package not installed. Terminating script execution.")
    exit()
# try/except
   
# Script parameters
# First parameter, MassDOT route_id "route" is REQUIRED
MassDOT_route_id_root = arcpy.GetParameterAsText(0)
# Debug/trace
arcpy.AddMessage("Processing " + MassDOT_route_id_root) 

# Second parameter, primary route direction, is REQUIRED
primary_route_dir = arcpy.GetParameterAsText(1)
secondary_route_dir = 'SB' if primary_route_dir == 'NB' else 'WB'

MassDOT_route_query_string  = "route_id = " + "'" + MassDOT_route_id_root + primary_route_dir + "'"
MassDOT_route_query_string += " OR route_id = "  + "'"  + MassDOT_route_id_root + secondary_route_dir + "'"
arcpy.AddMessage("MassDOT_route_query_string = " + MassDOT_route_query_string)

arcpy.Warning("*** WARNING: This script is under development.")

# Third parameter, indicating a file containing a specified list of TMCs, is REQUIRED.    
TMC_list_file = arcpy.GetParameterAsText(2)
#  Debug/trace
arcpy.AddMessage("TMC_list_file = " + TMC_list_file)

f = open(TMC_list_file, 'r')
str1 = f.read()
str2 = str1.replace('\n', '')
INRIX_query_string = "tmc IN (" + str2 + ")"
arcpy.AddMessage("Using specified list of TMCs.")
arcpy.AddMessage("INRIX_query_string = " + INRIX_query_string)


# Path to "base directory" in which all output files are written,
# and in which the re-generated LRSE FCs are found
#
base_dir = r'\\lilliput\groups\Data_Resources\conflate-tmcs-and-massdot-arterials'

# Connection file for read-only connection to ArcGIS 10.6 SDE mpodata.mpodata database
sde_mpodata_ro_connection = r'\\lindalino\users\Public\Documents\Public ArcGIS\Database Connections\CTPS 10.6.sde'

# INPUT DATA: INRIX TMCs, MassDOT routes, MassDOT event layers (speed limit, number of lanes), CTPS towns political boundaries
#
# INRIX TMCs
INRIX_MASSACHUSETTS_TMC_2019 = sde_mpodata_ro_connection + '\mpodata.mpodata.INRIX_MASSACHUSETTS_TMC_2019'
# Layer containing TMCs selected from the above
INRIX_TMCS = "INRIX_TMCS"

# MassDOT LRSN_Routes
MASSDOT_LRSN_Routes_19Dec2019 = sde_mpodata_ro_connection + '\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.MASSDOT_LRSN_Routes_19Dec2019'
# Layer containing route selected from the above
Selected_LRSN_Route = "Selected LRSN Route"

# MassDOT speed limit LRSE - use FC regenerated from event table and LRSN rather than raw MassDOT FC
#
# LRSE_Speed_Limit = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE  
#10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.LRSE_Speed_Limit'
#
LRSE_Speed_Limit = base_dir + '\\LRSE_Speed_Limit_FC_redux.gdb\\LRSE_Speed_Limit'

# Layer containing data selected from the above
Speed_Limit_Layer = "Speed Limit Layer"

# MassDOT number of travel lanes LRSE - use FC regenerated from event table and LRSN rather than raw MassDOT FC
#
# LRSE_Number_Travel_Lanes = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE #10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.LRSE_Number_Travel_Lanes'
#
LRSE_Number_Travel_Lanes = base_dir + '\\LRSE_Number_Travel_Lanes_FC_redux.gdb\LRSE_Number_Travel_Lanes'

# Layer containing data selected from the above
Num_Lanes_Layer = "Num Lanes Layer"

# Towns political boundaries
towns_pb_r = sde_mpodata_ro_connection + '\mpodata.mpodata.boundary\mpodata.mpodata.towns_pb_r'


# OUTPUT DATA: Event tables and CSV file

# Full path to geodatabase containing "template" TMC event table.
tmc_template_event_table_gdb =  base_dir + "\\tmc_event_table_template.gdb"

# Full paths of geodatabases in which event tables are written
#
tmc_event_table_gdb = base_dir + "\\tmc_events.gdb"
town_event_table_gdb = base_dir + "\\town_events.gdb"
overlay_events_1_gdb = base_dir + "\\overlay_1.gdb"
speed_limit_event_table_gdb = base_dir + "\\speed_limit_events.gdb"
overlay_events_2_gdb = base_dir + "\\overlay_2.gdb"
num_lanes_event_table_gdb = base_dir + "\\num_lanes_events.gdb"
overlay_events_3_gdb = base_dir + "\\overlay_3.gdb"
output_events_gdb = base_dir + "\\output_prep.gdb"

# Full path of directory in which intermediate CSV file is written
# 
output_csv_dir_1 = base_dir + "\\csv_intermediate"
# Full path of directory in which final (i.e., post-processed) CSV file is written
#
output_csv_dir_2 = base_dir + "\\csv_final"

# Names of generated event tables and intermediate CSV file
#
# base_table_name = MassDOT_route_id.lower().replace(' ','_')
base_table_name = MassDOT_route_id_root.lower()

# Raw (i.e., unsorted) TMC event table name
tmc_event_table_name_raw = base_table_name + "_events_tmc_raw"
# Sorted TMC event table name
tmc_event_table_name = base_table_name + "_events_tmc"
town_event_table_name = base_table_name + "_events_town"
overlay_event_table_1_name = base_table_name + "_events_overlay_1"
speed_limit_event_table_name = base_table_name + "_events_speedlimit"
overlay_event_table_2_name = base_table_name + "_events_overlay_2"
num_lanes_event_table_name = base_table_name + "_events_nlanes"
overlay_event_table_3_name = base_table_name + "_events_overlay_3"
# Note that the FINAL event table is written out as the INTERMEDIATE CSV file.
# Subsequent processing (by process_csv_file.py) writes out the FINAL CSV file.
output_event_table_name = base_table_name + "_events_output"
output_csv_file_name_1 = base_table_name + "_events_output.csv"
output_csv_file_name_2 = base_table_name + "_events_final.csv"

# Full path of "template" TMC event table
tmc_template_event_table = tmc_template_event_table_gdb +"\\TEMPLATE_events_tmc"

# Full paths of generated event tables
#
# Raw (i.e., unsorted) TMC event table
tmc_event_table_raw = tmc_event_table_gdb + "\\" + tmc_event_table_name_raw
# Sorted TMC event table
tmc_event_table = tmc_event_table_gdb + "\\" + tmc_event_table_name 
town_event_table = town_event_table_gdb + "\\" + town_event_table_name
overlay_events_1 = overlay_events_1_gdb + "\\" + overlay_event_table_1_name
speed_limit_event_table = speed_limit_event_table_gdb + "\\" + speed_limit_event_table_name
overlay_events_2 = overlay_events_2_gdb + "\\" + overlay_event_table_2_name
num_lanes_event_table = num_lanes_event_table_gdb + "\\" + num_lanes_event_table_name
overlay_events_3 = overlay_events_3_gdb + "\\" + overlay_event_table_3_name
output_event_table = output_events_gdb + "\\" + output_event_table_name 

# Full path of generated intermediate CSV file
#
output_csv_1 = output_csv_dir_1 + "\\" + output_csv_file_name_1
#
# Full path of generated final CSV file
output_csv_2 = output_csv_dir_2 + "\\" + output_csv_file_name_2


# Processing, per se, begins here

# Make Feature Layer "INRIX_TMCS": from INRIX TMCs, select TMCs using the INRIX_query_string
arcpy.MakeFeatureLayer_management(INRIX_MASSACHUSETTS_TMC_2019, INRIX_TMCS, INRIX_query_string, 
                                  "", "objectid objectid HIDDEN NONE;tmc tmc VISIBLE NONE;tmctype tmctype VISIBLE NONE;linrtmc linrtmc HIDDEN NONE;frc frc VISIBLE NONE;lenmiles lenmiles VISIBLE NONE;strtlat strtlat HIDDEN NONE;strtlong strtlong HIDDEN NONE;endlat endlat HIDDEN NONE;endlong endlong HIDDEN NONE;roadnum roadnum VISIBLE NONE;roadname roadname VISIBLE NONE;firstnm firstnm VISIBLE NONE;direction direction VISIBLE NONE;country country HIDDEN NONE;state state HIDDEN NONE;zipcode zipcode HIDDEN NONE;shape shape HIDDEN NONE;st_length(shape) st_length(shape) HIDDEN NONE")

# Make Feature Layer "Selected_LRSN_Route": from MASSDOT LRSN_Routes select route with MassDOT_route_id
arcpy.MakeFeatureLayer_management(MASSDOT_LRSN_Routes_19Dec2019, Selected_LRSN_Route, MassDOT_route_query_string, 
                                   "", "objectid objectid HIDDEN NONE;from_date from_date HIDDEN NONE;to_date to_date HIDDEN NONE;route_system route_system HIDDEN NONE;route_number route_number HIDDEN NONE;route_direction route_direction HIDDEN NONE;route_id route_id VISIBLE NONE;route_type route_type VISIBLE NONE;route_qualifier route_qualifier HIDDEN NONE;alternate_route_number alternate_route_number HIDDEN NONE;created_by created_by HIDDEN NONE;date_created date_created HIDDEN NONE;edited_by edited_by HIDDEN NONE;date_edited date_edited HIDDEN NONE;globalid globalid HIDDEN NONE;shape shape HIDDEN NONE;st_length(shape) st_length(shape) HIDDEN NONE")

arcpy.AddMessage("Generating TMC events.")

# Generate TMC events: "locate" TMCs along MassDOT routes
#
# NOTE: We found that the out-of-the-box ESRI 'Locate Features Along Routes' doesn't quite do the job we need.
#       The original code using the ESRI tool is reatained here as a comment, for reference.
#      The code we implmented to perform locating TMC events along the MassDOT routes is found below.
#
# *** Beginning of original code:
#
# Locate Features Along Routes: locate selected TMCs along selected MassDOT route
# Output is: tmc_event_table
# Note: An XY tolerance of ***40*** meters was found to be necessary some cases, e.g., I-95 @ new bridge over Merrimack River.
# tmc_event_table_properties = "route_id LINE from_meas to_meas"
# arcpy.LocateFeaturesAlongRoutes_lr(INRIX_TMCS, Selected_LRSN_Route, "route_id", XY_tolerance + " Meters", tmc_event_table, 
#                                    tmc_event_table_properties, "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")
# Delete un-needed fields from tmc_event_table
# arcpy.DeleteField_management(tmc_event_table, "linrtmc;frc;lenmiles;strtlat;strtlong;endlat;endlong;roadname;country;state;zipcode")
#
# *** End of original code
#
# *** Beginning of replacement code:
#
# Make a copy of the "template" TMC event table into which the raw (unsorted) TMC events will be written
arcpy.CreateTable_management(tmc_event_table_gdb, tmc_event_table_name_raw, tmc_template_event_table)

# Indices in the vector of fields (i.e., attributes) to be read in from the TMC FC
route_feat_route_id_ix = 0; route_feat_shape_ix = 1
#
# Get the geometry of the selected LRSN route
route_sc = arcpy.da.SearchCursor(Selected_LRSN_Route,['route_id', 'shape@'])
route_feat = route_sc.next()
route_feat_last_m_value = route_feat[route_feat_shape_ix].lastPoint.M


# Names of fields (i.e., attributes) read in from the TMC FC
tmc_fc_fieldnames = ['tmc', 'tmctype','roadnum', 'firstnm', 'direction', 'shape@']
# Indices in the vector of fields (i.e., attributes) read in from the TMC FC
tmc_feat_tmc_id_ix = 0;  tmc_feat_tmctype_ix = 1; tmc_feat_roadnum_ix = 2; tmc_feat_firstnm_ix = 3; 
tmc_feat_direction_ix = 4; tmc_feat_shape_ix = 5

# Names of output event table fields
et_fieldnames = ['route_id', 'from_meas', 'to_meas', 'tmc', 'tmctype', 'roadnum', 'firstnm', 'direction']
# Indices of fields in output event table (actually, this isn't needed)
et_route_id_ix = 0; et_from_meas_ix = 1; et_to_meas_ix = 2; et_tmc_ix = 3; 
et_tmctype_ix = 4; et_roadnum_ix = 5; et_firstnm_ix = 6; et_direction_ix = 7

# "Insert" cursor for output event table
out_csr = arcpy.da.InsertCursor(tmc_event_table_raw, et_fieldnames)

# Loop over the selected TMC features, which are to be located on the selected route feature
#
for tmc_feat in arcpy.da.SearchCursor(INRIX_TMCS, tmc_fc_fieldnames):
    tmc_id = tmc_feat[tmc_feat_tmc_id_ix]
 
    tmc_feat_fromPoint = tmc_feat[tmc_feat_shape_ix].firstPoint
    tmc_feat_toPoint = tmc_feat[tmc_feat_shape_ix].lastPoint

    projected_fromPtGeom = route_feat[route_feat_shape_ix].queryPointAndDistance(tmc_feat_fromPoint)
    projected_toPtGeom = route_feat[route_feat_shape_ix].queryPointAndDistance(tmc_feat_toPoint)

    # If the M-value of the "projected" point lies beyond either the beginning or the end of the route,
    # force it to the M-value of the beginning of the route (0.0) or to route_feat_last_m_value, respectively.
    if projected_fromPtGeom[0].firstPoint.M >= 0.0:
        from_meas = projected_fromPtGeom[0].firstPoint.M if (projected_fromPtGeom[0].firstPoint.M <= route_feat_last_m_value) else route_feat_last_m_value
    else:
        from_meas = 0.0
    # end_if
    
    if projected_toPtGeom[0].firstPoint.M >= 0.0:
        to_meas = projected_toPtGeom[0].firstPoint.M if (projected_toPtGeom[0].firstPoint.M <= route_feat_last_m_value) else route_feat_last_m_value
    else:
        to_meas = 0.0
    # end_if
    
    # OLD CODE:
    # from_meas = projected_fromPtGeom[0].firstPoint.M if (projected_fromPtGeom[0].firstPoint.M >= 0.0) else 0.0
    # to_meas = projected_toPtGeom[0].firstPoint.M if (projected_toPtGeom[0].firstPoint.M >= 0.0) else 0.0
    
    # debug/trace
    # print 'Processing ' + tmc_id + ', ' + str(from_meas) + ', ' + str(to_meas)      
       
    # Do not write out zero-length events
    if (from_meas >= 0.0 and to_meas > 0.0) and (from_meas != to_meas):
        roh = [route_feat[route_feat_route_id_ix], from_meas, to_meas, 
               tmc_feat[tmc_feat_tmc_id_ix], tmc_feat[tmc_feat_tmctype_ix], 
               tmc_feat[tmc_feat_roadnum_ix], tmc_feat[tmc_feat_firstnm_ix], tmc_feat[tmc_feat_direction_ix]]   
        out_csr.insertRow(roh)
        arcpy.AddMessage('Inserted event: ' + tmc_id + ', ' + str(from_meas) + ', ' + str(to_meas))
    else:
        # Zero-length event
        arcpy.AddMessage('Discarded zero-length event: ' + tmc_id + ', ' + str(from_meas) + ', ' + str(to_meas))
    # if
# for tmc_feat

# Close the insert cursor - not exactly the best choice of API name!
del out_csr 
arcpy.AddMessage('Closed insert cursor.')


# Sort the raw TMC event table in ascending order on the 'from_meas' field
arcpy.Sort_management(tmc_event_table_raw, tmc_event_table, [["from_meas", "ASCENDING"]])
#
#
# *** End of replacement code for 'Locate Features Along Routes'

arcpy.AddMessage("Generating town events.")

# Locate Features Along Routes: locate towns_pb (political boundaries) along selected MassDOT route
# output is: town_event_table
town_event_table_properties = "route_id LINE from_meas to_meas"
arcpy.LocateFeaturesAlongRoutes_lr(towns_pb_r, Selected_LRSN_Route, "route_id", "0 Meters", town_event_table, town_event_table_properties, 
                                   "FIRST", "DISTANCE", "NO_ZERO", "FIELDS", "M_DIRECTON")
                                   
# Delete un-needed fields from town_event_table
arcpy.DeleteField_management(town_event_table, "shape_leng;boundary_link_id")                                  

arcpy.AddMessage("Generating overlay #1.")
                                 
# HERE: tmc_event_table and town_event_table have been generated.
#       Generate overlay #1.
# Overlay Route Events: inputs: overlay tmc_events, town_events
#                       output: overlay_events_1
overlay_event_table_1_properties = "route_id LINE from_meas to_meas"
arcpy.OverlayRouteEvents_lr(tmc_event_table, "route_id LINE from_meas to_meas", 
                            town_event_table, "route_id LINE from_meas to_meas", "UNION", 
                            overlay_events_1, overlay_event_table_1_properties, "NO_ZERO", "FIELDS", "INDEX")

# Make Feature Layer "Speed_Limit_Layer": 
arcpy.MakeFeatureLayer_management(LRSE_Speed_Limit, Speed_Limit_Layer, "to_date IS NULL", "", "objectid objectid HIDDEN NONE;from_date from_date HIDDEN NONE;to_date to_date HIDDEN NONE;event_id event_id HIDDEN NONE;route_id route_id VISIBLE NONE;from_measure from_measure VISIBLE NONE;to_measure to_measure VISIBLE NONE;speed_lim speed_lim VISIBLE NONE;op_dir_sl op_dir_sl VISIBLE NONE;created_by created_by HIDDEN NONE;date_created date_created HIDDEN NONE;edited_by edited_by HIDDEN NONE;date_edited date_edited HIDDEN NONE;locerror locerror HIDDEN NONE;globalid globalid HIDDEN NONE;regulation regulation HIDDEN NONE;amendment amendment HIDDEN NONE;time_per time_per HIDDEN NONE;shape shape HIDDEN NONE;st_length(shape) st_length(shape) HIDDEN NONE")

# Select Layer By Location: from Speed_Limit_Layer, select records that lie WITHIN the Selected_LRSN_Route
arcpy.SelectLayerByLocation_management(Speed_Limit_Layer, "WITHIN", Selected_LRSN_Route, "", "NEW_SELECTION", "NOT_INVERT")
#
# Attribute-based selection to replace the above spatial selection, if needed
# arcpy.SelectLayerByAttribute_management(Speed_Limit_Layer, "NEW_SELECTION", MassDOT_route_query_string)

arcpy.AddMessage("Generating speed limit events.")

# Locate Features Along Routes: locate records in Speed_Limit_Layer along the Selected_LRSN_Route
# output is: speed_limit_event_table
speed_limit_event_table_properties = "route_id LINE from_meas to_meas"
arcpy.LocateFeaturesAlongRoutes_lr(Speed_Limit_Layer, Selected_LRSN_Route, "route_id", "0.0002 Meters", speed_limit_event_table, speed_limit_event_table_properties, 
                                   "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")

# Delete un-needed fields from speed_limit_event_table
arcpy.DeleteField_management(speed_limit_event_table, "from_date;to_date;event_id;route_id2;from_measure;to_measure;op_dir_sl;created_by;date_created;edited_by;date_edited;locerror;globalid;regulation;amendment;time_per")
  
arcpy.AddMessage("Generating overlay #2.")
  
# HERE: overlay_events_1 and speed_limit_events have been generated.
#       Generate overlay #2.
# Overlay Route Events: inputs: overlay overlay_events_1, speed_limit_events
#                       output: overlay_events_2
overlay_event_table_2_properties = "route_id LINE from_meas to_meas"
arcpy.OverlayRouteEvents_lr(overlay_events_1, "route_id LINE from_meas to_meas", 
                            speed_limit_event_table, "route_id LINE from_meas to_meas", "UNION", 
                            overlay_events_2, overlay_event_table_2_properties, "NO_ZERO", "FIELDS", "INDEX")


# Make Feature Layer: "Num_Lanes_Layer" (number of travel lanes layer)
arcpy.MakeFeatureLayer_management(LRSE_Number_Travel_Lanes, Num_Lanes_Layer, "to_date IS NULL", "", "objectid objectid HIDDEN NONE;from_date from_date HIDDEN NONE;to_date to_date HIDDEN NONE;event_id event_id HIDDEN NONE;route_id route_id VISIBLE NONE;from_measure from_measure VISIBLE NONE;to_measure to_measure VISIBLE NONE;num_lanes num_lanes VISIBLE NONE;opp_lanes opp_lanes HIDDEN NONE;created_by created_by HIDDEN NONE;date_created date_created HIDDEN NONE;edited_by edited_by HIDDEN NONE;date_edited date_edited HIDDEN NONE;locerror locerror HIDDEN NONE;globalid globalid HIDDEN NONE;shape shape VISIBLE NONE;st_length(shape) st_length(shape) VISIBLE NONE")

# Select Layer By Location: from Num_Lanes_Layer select records that lie WITHIN Selected_LRSN_Route
arcpy.SelectLayerByLocation_management(Num_Lanes_Layer, "WITHIN", Selected_LRSN_Route, "", "NEW_SELECTION", "NOT_INVERT")
#
# Attribute-based selection to replace the above spatial selection, if needed
# arcpy.SelectLayerByAttribute_management(Num_Lanes_Layer, "NEW_SELECTION", MassDOT_route_query_string)

arcpy.AddMessage("Generating number-of-lanes events.")

# Locate Features Along Routes: locate records in Num_Lanes_Layer along the selected LRSN_Route
# output is: num_lanes_event_table
num_lanes_event_table_properties = "route_id LINE from_meas to_meas"
arcpy.LocateFeaturesAlongRoutes_lr(Num_Lanes_Layer, Selected_LRSN_Route, "route_id", "0.0002 Meters", num_lanes_event_table, num_lanes_event_table_properties, 
                                   "FIRST", "DISTANCE", "ZERO", "FIELDS", "M_DIRECTON")

# Delete un-needed fields frm num_lanes_event_table
arcpy.DeleteField_management(num_lanes_event_table, "from_date;to_date;event_id;route_id2;from_measure;to_measure;opp_lanes;created_by;date_created;edited_by;date_edited;locerror;globalid")

arcpy.AddMessage("Generating overlay #3.")

# HERE: overlay_events_2 and num_lanes event_table have been generated
#       Generate overlay #3
# Overlay Route Events: inputs: overlay overlay_events_2, num_lanes_event_table
#                       output: overlay_events_3
overlay_event_table_3_properties = "route_id LINE from_meas to_meas"
arcpy.OverlayRouteEvents_lr(overlay_events_2, "route_id LINE from_meas to_meas", 
                            num_lanes_event_table, "route_id LINE from_meas to_meas", "UNION", 
                            overlay_events_3, overlay_event_table_3_properties, "ZERO", "FIELDS", "INDEX")

# HERE: overlay_events_3 has been generated
#       Perform miscellaneous cleanup operations, and generate intermediate CSV file

# Make Table View of overlay_events_3
overlay_events_3_View = "overlay_event_table_3_View"
arcpy.MakeTableView_management(overlay_events_3, overlay_events_3_View, "", "", "objectid objectid VISIBLE NONE;route_id route_id VISIBLE NONE;from_meas from_meas VISIBLE NONE;to_meas to_meas VISIBLE NONE;tmc tmc VISIBLE NONE;tmctype tmctype VISIBLE NONE;roadnum roadnum VISIBLE NONE;firstnm firstnm VISIBLE NONE;direction direction VISIBLE NONE;town town VISIBLE NONE;town_id town_id VISIBLE NONE;st_area_shape_ st_area_shape_ VISIBLE NONE;st_perimeter_shape_ st_perimeter_shape_ VISIBLE NONE;route_id_1 route_id_1 VISIBLE NONE;speed_lim speed_lim VISIBLE NONE;route_id_12 route_id_12 VISIBLE NONE;num_lanes num_lanes VISIBLE NONE;st_length_shape_ st_length_shape_ VISIBLE NONE")

# The MassDOT routes and events layers use TOWNS_POLYM to define town boundaries. We're using towns_pb instead (in order to inlcude water, etc. in town boundaries.)
# There is a slight difference between these, which results in an occasional overlay event with a TOWN_ID of zero. Remove these.
#
# Select records in overlay_events_3 with town_id = 0, delete them, and then clear selection
arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "NEW_SELECTION", "\"town_id\" = 0")
arcpy.DeleteRows_management(overlay_events_3_View)
arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "CLEAR_SELECTION", "")

# If a list of TMCs was specified as an input parameter, it's all but certain that some portions of the
# indicated route will have no TMC located along it. In this case, delete all records where tmc = ''.
if TMC_list_file:
    # Select records in overlay_events_3 with tmc = '', delete them, and then clear selection
    arcpy.AddMessage("Pruning records with tmc = ''.")
    arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "NEW_SELECTION", "tmc = ''")
    arcpy.DeleteRows_management(overlay_events_3_View)
    arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "CLEAR_SELECTION", "")
# end_if

# Roads and Highways allows (among other things) events with measure values < 0. In particular, we are concerned with from_measure values < 0.
# Clean these up by setting the relevant from_measures to 0.
#
# Select records in overlay_events_3 with from_meas < 0, set the from_meas of these records to 0, and clear selection
arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "NEW_SELECTION", "from_meas < 0")
arcpy.CalculateField_management(overlay_events_3_View, "from_meas", "0.0", "PYTHON_9.3", "")
arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "CLEAR_SELECTION", "")

# Remove zero-length records (i.e., records for which from_meas == to_meas), if any
arcpy.AddMessage("Pruning zero-length records.")
arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "NEW_SELECTION", "from_meas = to_meas")
arcpy.DeleteRows_management(overlay_events_3_View)
arcpy.SelectLayerByAttribute_management(overlay_events_3_View, "CLEAR_SELECTION", "")


# Sort the table in ascending order on from_meas, and add a "calc_len" (calculated length) field to each record, 
# and calculate its value appropriately.
# output is in output_event_table
# These operations could be performed in the subsequent processing of the generated CSV file, but we do them here anyway.
arcpy.Sort_management(overlay_events_3_View, output_event_table, "from_meas ASCENDING;tmc ASCENDING", "UR")

arcpy.AddMessage("Generating output event table.")

# Add a "calc_len" field to output_event_table, and calc it to (to_meas - from_meas)
arcpy.AddField_management(output_event_table, "calc_len", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.CalculateField_management(output_event_table, "calc_len", "!to_meas! - !from_meas!", "PYTHON_9.3", "")


arcpy.AddMessage("Exporting output event table to CSV file.")

# Export final_event_table to CSV file
#
# Code generated by model:
arcpy.TableToTable_conversion(output_event_table, output_csv_dir_1, output_csv_file_name_1)
#
#
# ... and if that doesn't work, the following has been known to do so in the past:
# (Source: http://gis.stackexchange.com/questions/109008/python-script-to-export-csv-tables-from-gdb)
#
# fields = arcpy.ListFields(output_event_table)
# field_names = [field.name for field in fields]
# with open(output_csv_1,'wb') as f:
#    w = csv.writer(f)
#    w.writerow(field_names)
#    for row in arcpy.SearchCursor(output_event_table):
#        field_vals = [row.getValue(field.name) for field in fields]
#        w.writerow(field_vals)
#    del row
#
arcpy.AddMessage("Finished executing phase 1: " + MassDOT_route_id + ". Intermediate output is in: " + output_csv_dir_1 + "\\" + output_csv_file_name_1)

arcpy.AddMessage("Post-processing CSV file.")
process_csv_file.main_routine(output_csv_dir_1, output_csv_file_name_1, output_csv_dir_2, output_csv_file_name_2)
arcpy.AddMessage("Finished executing phase 2: " + MassDOT_route_id + ". Final output is in: " + output_csv_dir_2 + "\\" + output_csv_file_name_2)