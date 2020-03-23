# regenerate_LRSE_FCs_for_arterials_pass_2.py - script to re-generate selected LRSE feature classes 
#                                               from LRSN route geometry and LRSE event tables
#                                               for ARTERIAL routes.
#
# This script was written to deal with MassDOT LRSE FC's becoming out-of-sync with the LRSN
# route layer because of changes (edits) to LRSN route geometry. This was found to be the case, 
# for example, for SR2 EB and WB in the "LRSN + LRSE" data copied fro MassDOT on 19 December 2019.
#
# This script is  regenerate_LRSE_FCs.py but differs from it in that it needs to deal
# with the peculiar nature of MassDOT event tables for arterial routes - some parts of which
# are divided (have a median) and some parts of which are un-divided (have no median.)
# MassDOT practice has been to NOT code events on the secondary direction of routes when the
# two directions are co-incident, but in this situation code an "opposing direction" attribute
# on the in the primary direction event table.
#
# The process of regenerating these FCs is a two-pass process.
# This script forms "PASS 2" of this process. It assumes that 
#     1.the "PASS 1" script has been run
#     2. the multiple speed limit FCs have been combined into a single "master" speed limit FC 
#     3. the multiple num travel lanes FC have been combined into a single "master" num lanes FC
#
# Ben Krepp, attending metaphysician
# 03/12/2020, 03/16/2020, 03/17/2020

import arcpy
import pydash

# Single (optional) parameter, specifying a file containing a newline-delimited list of MassDOT route_ids  
#
route_list_file_name = arcpy.GetParameterAsText(0)  
if route_list_file_name != '':
    f = open(route_list_file_name, 'r')
    s = f.read()
    route_list = s.split('\n')
    for route_id in route_list:
        arcpy.AddMessage(route_id)
    # for   
else:
    route_list = [ 'SR107 NB', 'SR107 SB', 
                   'SR109 EB', 'SR109 WB', 
                   'SR114 EB', 'SR114 WB', 
                   'SR115 NB', 'SR115 SB',
                   'SR117 EB', 'SR117 WB', 
                   'SR119 EB', 'SR119 WB', 
                   'SR123 EB', 'SR123 WB', 
                   'SR126 NB', 'SR126 SB',
                   'SR129 EB', 'SR129 WB',
                   'SR135 EB', 'SR135 SB', 
                   'SR138 NB', 'SR138 SB', 
                   'SR139 EB', 'SR139 WB', 
                   'SR140 EB', 'SR140 WB',
                   'SR16 EB',  'SR16 WB',
                   'SR18 NB',  'SR18 SB', 
                   'SR1A NB',  'SR1A SB',                    
                   'SR203 EB', 'SR203 WB', 
                   'SR225 EB', 'SR225 WB',
                   'SR228 NB', 'SR228 SB', 
                   'SR27 NB',  'SR27 SB', 
                   'SR28 NB',  'SR28 SB',
                   'SR2A EB',  'SR2A WB', 
                   'SR30 EB',  'SR30 WB', 
                   'SR37 NB',  'SR37 SB', 
                   'SR38 NB',  'SR38 SB',
                   'SR3A NB',  'SR3A SB', 
                   'SR4 NB',   'SR4 SB',                   
                   'SR53 NB',  'SR53 SB', 
                   'SR60 EB',  'SR60 WB', 
                   'SR62 EB',  'SR62 WB', 
                   'SR85 NB',  'SR85 SB',
                   'SR9 EB',   'SR9 WB', 
                   'SR99 NB',  'SR99 SB',                     
                   'US1 NB',   'US1 SB', 
                   'US20 EB',  'US20 WB' ]
# end_if

# MassDOT LRSN_Routes - the route geometry here is assumed to be definitive
#
MASSDOT_LRSN_Routes_19Dec2019 = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.MASSDOT_LRSN_Routes_19Dec2019'
#
# Layer containing data to be selected from the above
Routes_Layer = "LRSN_Routes_Layer"
arcpy.MakeFeatureLayer_management(MASSDOT_LRSN_Routes_19Dec2019, Routes_Layer)


#
# *** The following 4 definitions should NOT be used in Pass 2!!!
# *** They have been retained here for the time being for reference purpposes only.
#
# MassDOT speed limit LRSE - geometry here may be out of sync w.r.t. LRSN_Routes; event table data is assumed to be OK.
#
LRSE_Speed_Limit_MassDOT = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.LRSE_Speed_Limit'
# Layer containing data selected from the above
#
Speed_Limit_Layer_MassDOT = "Speed_Limit_Layer_MassDOT"
# MassDOT number of travel lanes LRSE - geometry here may be out of sync w.r.t. LRSN_Routes; event table data is assumed to be OK.
#
LRSE_Number_Travel_Lanes_MassDOT = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.LRSE_Number_Travel_Lanes'
# Layer containing data selected from the above
Num_Lanes_Layer_MassDOT = "Num_Lanes_Layer_MassDOT"


               
# Path to "base directory"
base_dir = r'\\lilliput\groups\Data_Resources\conflate-tmcs-and-massdot-arterials'

#
# Data from pass 1 (previous pass)
#

# Path to GDB for event tables extracted from MassDOT LRSE Speed Limit FC
# *** PROBABLY NOT NEEDED
speed_limit_events_pass_1_gdb = base_dir + '\\LRSE_Speed_Limit_events_pass_1.gdb'
# Path to GDB for event tables extracted from MassDOT Number of Travel Lanes FC
# *** PROBABLY NOT NEEDED
num_lanes_events_pass_1_gdb = base_dir + '\\LRSE_Number_Travel_Lanes_events_pass_1.gdb'

# Path to the regenerated LRSE_Speed_Limit FC produced in Pass 1.
LRSE_Speed_Limit_Pass_1 = base_dir + '\\LRSE_Speed_Limit_FC_pass_1.gdb\\LRSE_Speed_Limit'

# Path to the regenerated LRSE_Number_Travel_Lanes FCs produced in Pass 1.
LRSE_Number_Travel_Lanes_Pass_1 = base_dir + '\\LRSE_Number_Travel_Lanes_FC_pass_1.gdb\\LRSE_Number_Travel_Lanes'


# Create layers for LRSE Speed Limit FC and LRSE Number of Travel Lanes FC that were
# re-generated "from scratch" (i.e., from LRSN_Routes and the relevant event tables)
# in Pass 1.
#
Speed_Limit_Layer_Pass_1 = "Speed_Limit_Layer_Pass_1"
Num_Lanes_Layer_Pass_1 = "Num_Lanes_Layer_Pass_1"
arcpy.MakeFeatureLayer_management(LRSE_Speed_Limit_Pass_1, Speed_Limit_Layer_Pass_1)
arcpy.MakeFeatureLayer_management(LRSE_Number_Travel_Lanes_Pass_1, Num_Lanes_Layer_Pass_1)


#
# Data produced by pass 2 (this pass)
#
# Path to GDB for speed limit events produced in pass 2
speed_limit_events_pass_2_gdb = base_dir + '\\LRSE_Speed_Limit_events_pass_2.gdb'

# Path to GDB for "num lanes" events produced in pass 2
num_lanes_events_pass_2_gdb = base_dir + '\\LRSE_Number_Travel_Lanes_events_pass_2.gdb'

# Path to GDB for regenerated LRSE_Speed_Limit FCs produced in pass 2
speed_limit_pass_2_gdb = base_dir + '\\LRSE_Speed_Limit_FC_pass_2.gdb'

# Path to GDB for regenerated LRSE_Number_Travel_Lanes FCs produeced in pass2
num_lanes_pass_2_gdb = base_dir + '\\LRSE_Number_Travel_Lanes_FC_pass_2.gdb'

# Extract list of *primary* route_ids: 
primary_route_list = pydash.collections.filter_(route_list, lambda x: x.endswith("NB") or x.endswith("EB"))

# We iterate over the list of MassDOT *primary* route_ids.
# 
# The process is as follows:
#   1. Select records for primary AND associated secondary route from LRSN_Routes_Layer
#   2. Select records for primary AND associated secondary route from "Pass 1" Speed Limit Layer
#   3. Locate selected features [2] along selected route-pair [1];
#      this produces and event table whose path is given by the variable sl_et_name.
#      ==> This event table will (should?) contain a sequence of 'speed limit' events for the 
#          full length of the route in both primary and secondary directions.
#          These records for the primary and secondary directions can be disambiguated by the 
#          value of the "RID" field: 
#               <route_num> + ' NB' or <route_num> + ' EB' for the primary direction
#               <route_num> + ' SB" or <route_num> + ' WB' for the secondary direction
#   4. Make a feature layer from the event table produced by [3];
#      the name of this layer is given by the variable sl_events_layer_name
#   5. Select records for the primary route from sl_events_layer_name,
#      and export them to the "Pass 2" speed limit FC GDB.
#   6. Select records for the *secondary* route from sl_events_layer_name,
#      do some ***TBD*** special processing on them,
#      and export them to the "Pass 2" speed limit FC GDB.
#
for primary_route_id in primary_route_list:
    parts = primary_route_id.split(' ')
    route_num = parts[0]
    primary_dir = parts[1]
    secondary_dir = 'SB' if primary_dir == 'NB' else 'WB'
    secondary_route_id = route_num + ' ' + secondary_dir
    arcpy.AddMessage("Processing " + primary_route_id + " and " + secondary_route_id)
    
    MassDOT_route_query_string = "route_id = " + "'" + primary_route_id + "'" + " OR " + "route_id = " + "'" + secondary_route_id  + "'"
    arcpy.AddMessage('MassDOT_route_query_string = ' + MassDOT_route_query_string)
    
    normalized_primary_route_id = primary_route_id.replace(' ', '_')    
    normalized_secondary_route_id = secondary_route_id.replace(' ', '_')  
    
    sl_et_path = speed_limit_events_pass_2_gdb + '\\' +  route_num + '_sl_events'
    sl_events_layer_name = route_num + '_sl_events_layer'
    
    nl_et_path = num_lanes_events_pass_2_gdb + '\\' +  route_num + '_nl_events'
    nl_events_layer_name = route_num + '_nl_events_layer'   
    
    # Strings for querying events layer for records for primary or secondary direction
    primary_dir_query_str = "RID = " + "'" + primary_route_id + "'" 
    secondary_dir_query_str = "RID = " + "'" + secondary_route_id + "'" 
    
    primary_sl_fc_path   = speed_limit_pass_2_gdb + '\\' + normalized_primary_route_id + '_sl_fc'   
    secondary_sl_fc_path = speed_limit_pass_2_gdb + '\\' + normalized_secondary_route_id + '_sl_fc'
    
    primary_nl_fc_path   = num_lanes_pass_2_gdb + '\\' + normalized_primary_route_id + '_nl_fc'   
    secondary_nl_fc_path = num_lanes_pass_2_gdb + '\\' + normalized_secondary_route_id + '_nl_fc'    
    
    # First, the speed limit FC's:
    #
    arcpy.AddMessage('    Generating speed limit FCs...')
    
    arcpy.SelectLayerByAttribute_management(Routes_Layer, "NEW_SELECTION", MassDOT_route_query_string)   
    arcpy.SelectLayerByAttribute_management(Speed_Limit_Layer_Pass_1, "NEW_SELECTION", MassDOT_route_query_string)
    
    # locate selected speed limit features against selected routes
    arcpy.LocateFeaturesAlongRoutes_lr(Speed_Limit_Layer_Pass_1, Routes_Layer, "route_id", 0.0002,
                                       sl_et_path, "RID LINE from_meas to_meas")
                                          
    # make a route event layer out of the results of this operation
    arcpy.MakeRouteEventLayer_lr(Routes_Layer, "route_id", sl_et_path, 
                                 "RID LINE from_meas to_meas", sl_events_layer_name)
                                 
    # select records from the route event layer for the *primary* route (the "RID" field will disambiguate),
    # and export it to a FC
    arcpy.AddMessage('        for the primary direction, ...')
    arcpy.SelectLayerByAttribute_management(sl_events_layer_name, "NEW_SELECTION", primary_dir_query_str)
    arcpy.CopyFeatures_management(sl_events_layer_name, primary_sl_fc_path)

    # select records from the route event layer for the *secondary* route (the "RID" field will disambiguate),
    # and export it to a FC
    #
    # NOTE: For the secondary direction:
    #           if route_id != RID ==> harvest speed_limit attribute (divided road)
    #           if route_id == RID ==> harvest "opposing" speed_limit attribute (non-divided road)  
    arcpy.AddMessage('        and for the secondary direction.')    
    arcpy.SelectLayerByAttribute_management(sl_events_layer_name, "NEW_SELECTION", secondary_dir_query_str)
    arcpy.CopyFeatures_management(sl_events_layer_name, secondary_sl_fc_path)
    

    # Second, the number of lanes FCs:
    #
    arcpy.AddMessage('    Generating number-of-lanes FCs...')
    
    arcpy.SelectLayerByAttribute_management(Routes_Layer, "NEW_SELECTION", MassDOT_route_query_string)   
    arcpy.SelectLayerByAttribute_management(Num_Lanes_Layer_Pass_1, "NEW_SELECTION", MassDOT_route_query_string)
    
    # locate selected speed limit features against selected routes
    arcpy.LocateFeaturesAlongRoutes_lr(Num_Lanes_Layer_Pass_1, Routes_Layer, "route_id", 0.0002,
                                       nl_et_path, "RID LINE from_meas to_meas")
                                          
    # make a route event layer out of the results of this operation
    arcpy.MakeRouteEventLayer_lr(Routes_Layer, "route_id", nl_et_path, 
                                 "RID LINE from_meas to_meas", nl_events_layer_name)
                                 
    # select records from the route event layer for the *primary* route (the "RID" field will disambiguate),
    # and export it to a FC
    arcpy.AddMessage('        for the primary direction, ...')
    arcpy.SelectLayerByAttribute_management(nl_events_layer_name, "NEW_SELECTION", primary_dir_query_str)
    arcpy.CopyFeatures_management(nl_events_layer_name, primary_nl_fc_path)

    # select records from the route event layer for the *secondary* route (the "RID" field will disambiguate),
    # and export it to a FC
    #
    # NOTE: For the secondary direction:
    #           if route_id != RID ==> harvest speed_limit attribute (divided road)
    #           if route_id == RID ==> harvest "opposing" speed_limit attribute (non-divided road)  
    arcpy.AddMessage('        and for the secondary direction.')    
    arcpy.SelectLayerByAttribute_management(nl_events_layer_name, "NEW_SELECTION", secondary_dir_query_str)
    arcpy.CopyFeatures_management(nl_events_layer_name, secondary_nl_fc_path)
# end_for over primary_route_list