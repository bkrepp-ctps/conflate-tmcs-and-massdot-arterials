# regenerate_LRSE_FCs.py - script to re-generate selected LRSE feature classes from LRSN route geometry and LRSE event tables
#
# This script was written to deal with MassDOT LRSE FC's becoming out-of-sync with the LRSN route layer because of changes (edits)
# to LRSN route geometry. This was found to be the case, for example, for SR2 EB and WB in the "LRSN + LRSE" data copied from
# MassDOT on 19 December 2019.
#
# This script performs the conversion one 'route' at a time; the result are two sets of FC's, each set to be subsequently combined
# into a single FC using the 'Merge' tool.
#
# Ben Krepp, attending metaphysician
# 02/20/2020 - what a cool-looking date string, YOWSAH!

import arcpy

# Single (optional) parameter, specifying a file containing a newline-delimited list of MassDOT route_ids.  
route_list_file_name = arcpy.GetParameterAsText(0)  
if route_list_file_name != '':
    f = open(route_list_file_name, 'r')
    s = f.read()
    route_list = s.split('\n')
    for route_id in route_list:
        arcpy.AddMessage(route_id)
    # for   
else:
    route_list = [ 'SR107 NB', 'SR107 SB', 'SR109 EB' , 'SR109 WB', 'SR114 EB', 'SR114 WB', 'SR115 NB', 'SR115 SB',
                   'SR117 EB', 'SR117 WB', 'SR119 EB', 'SR119 WB', 'SR123 EB','SR123 WB', 'SR126 NB', 'SR126 SB',
                   'SR135 EB', 'SR135 SB', 'SR138 NB', 'SR138 SB', 'SR139 EB', 'SR139 WB', 'SR140 EB', 'SR140 WB',
                   'SR16 EB', 'SR16 WB', 'SR18 NB', 'SR18 SB', 'SR1A NB', 'SR1A SB',                    
                   'SR203 EB', 'SR203 WB', 'SR228 NB', 'SR228 SB', 'SR27 NB', 'SR27 SB', 'SR28 NB', 'SR28 SB',
                   'SR2A EB', 'SR2A WB', 'SR30 EB', 'SR30 WB', 'SR37 NB', 'SR37 SB', 'SR38 NB', 'SR38 SB',
                   'SR3A NB', 'SR3A SB', 
                   'SR4 NB', 'SR4 SB', 'SR225 EB', 'SR225 WB',
                   'SR53 NB', 'SR53 SB', 'SR60 EB', 'SR60 WB', 'SR62 EB', 'SR62 WB', 'SR85 NB', 'SR85 SB',
                   'SR9 EB', 'SR8 WB', 'SR99 NB', 'SR99 SB', 'SR129 EB', 'SR129 WB', 
                   'SR3A NB', 'SR3A SB',
                   'US1 NB', 'US1 SB', 'US20 EB', 'US20 WB' ]
# end_if

# MassDOT LRSN_Routes - the route geometry here is assumed to be definitive
#
MASSDOT_LRSN_Routes_19Dec2019 = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.MASSDOT_LRSN_Routes_19Dec2019'

# MassDOT speed limit LRSE - geometry here may be out of sync w.r.t. LRSN_Routes; event table data is assumed to be OK.
#
LRSE_Speed_Limit = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.LRSE_Speed_Limit'

# Layer containing data selected from the above
#
Speed_Limit_Layer = "Speed_Limit_Layer"

# MassDOT number of travel lanes LRSE - geometry here may be out of sync w.r.t. LRSN_Routes; event table data is assumed to be OK.
#
LRSE_Number_Travel_Lanes = r'\\lindalino\users\Public\Documents\Public ArcGIS\CTPS data from database servers for ITS\SDE 10.6.sde\mpodata.mpodata.CTPS_RoadInventory_for_INRIX_2019\mpodata.mpodata.LRSE_Number_Travel_Lanes'
# Layer containing data selected from the above

Num_Lanes_Layer = "Num_Lanes_Layer"
               
# Path to "base directory"
base_dir = r'\\lilliput\groups\Data_Resources\conflate-tmcs-and-massdot-arterials'

# Path to GDB for event tables extracted from MassDOT LRSE Speed Limit FC
speed_limit_events_gdb = base_dir + '\\LRSE_Speed_Limit_events.gdb'

# Path to GDB for event tables extracted from MassDOT Number of Travel Lanes FC
num_lanes_events_gdb = base_dir + '\\LRSE_Number_Travel_Lanes_events.gdb'

# Path to GDB for regenerated LRSE_Speed_Limit FCs
speed_limit_gdb = base_dir + '\\LRSE_Speed_Limit_FC_redux.gdb'

# Path to GDB for regenerated LRSE_Number_Travel_Lanes FCs
num_lanes_gdb = base_dir + '\\LRSE_Number_Travel_Lanes_FC_redux.gdb'


# Layers for raw MassDOT LRSE Speed Limit FC and raw MassDOT LRSE Number of Travel Lanes FC
arcpy.MakeFeatureLayer_management(LRSE_Speed_Limit, Speed_Limit_Layer)
arcpy.MakeFeatureLayer_management(LRSE_Number_Travel_Lanes, Num_Lanes_Layer)

for route_id in route_list:
    arcpy.AddMessage("Processing " + route_id)
    
    MassDOT_route_query_string = "route_id = " + "'" + route_id + "'"   
    normalized_route_id = route_id.replace(' ', '_')    
    sl_et_name = normalized_route_id + '_sl_events'
    sl_layer_name = normalized_route_id + '_sl_layer'
    sl_fc_name = normalized_route_id + '_sl_fc'    
    nl_et_name = normalized_route_id + '_nl_events'
    nl_layer_name = normalized_route_id + '_nl_layer'
    nl_fc_name = normalized_route_id + '_nl_fc'
      
    arcpy.AddMessage('    Generating speed limit FC.')
    arcpy.SelectLayerByAttribute_management(Speed_Limit_Layer, "NEW_SELECTION", MassDOT_route_query_string)
    arcpy.TableToTable_conversion("Speed_Limit_Layer", speed_limit_events_gdb, sl_et_name)  
    arcpy.MakeRouteEventLayer_lr(MASSDOT_LRSN_Routes_19Dec2019, "route_id", 
                                 speed_limit_events_gdb + '\\' + sl_et_name, "route_id LINE from_measure to_measure", sl_layer_name)
    arcpy.CopyFeatures_management(sl_layer_name, speed_limit_gdb + '\\' + sl_fc_name)
    
    arcpy.AddMessage('    Generating number of travel lanes FC.')
    arcpy.SelectLayerByAttribute_management(Num_Lanes_Layer, "NEW_SELECTION", MassDOT_route_query_string)
    arcpy.TableToTable_conversion("Num_Lanes_Layer", num_lanes_events_gdb, nl_et_name)
    arcpy.MakeRouteEventLayer_lr(MASSDOT_LRSN_Routes_19Dec2019, "route_id", 
                                 num_lanes_events_gdb + '\\' + nl_et_name, "route_id LINE from_measure to_measure", nl_layer_name)                                   
    arcpy.CopyFeatures_management(nl_layer_name, num_lanes_gdb + '\\' + nl_fc_name )
# end_for over route_list