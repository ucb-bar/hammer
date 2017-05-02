#!/usr/bin/env python3

import argparse
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--floorplan_json", dest="floorplan_json", required=True)
parser.add_argument("-o", "--output", dest="output", required=True)
parser.add_argument("-t", "--top", dest="top", required=True)
args = parser.parse_args()
args_dict = vars(args)

input=json.loads("".join(open(args.floorplan_json, "r").readlines()))
output=open(args.output, "w")

# Write a header
output.write("# Automatically generated with {script_name} -f {floorplan_json} -o {output} -t {top}\n\n".format(script_name=sys.argv[0], **args_dict))

output.write("source -echo generated-scripts/constraints.tcl\n")

output.write("create_floorplan -control_type aspect_ratio -core_aspect_ratio 1 -core_utilization 0.7 -left_io2core 3 -bottom_io2core 3 -right_io2core 3 -top_io2core 3 -start_first_row\n")

output.write("set_fp_placement_strategy -macros_on_edge auto\n")
if len(input) > 0:
    output.write("set_fp_macro_options [all_macro_cells] -legal_orientation {W E FW FE}\n")
output.write("set_keepout_margin -type hard -north -outer {5 5 5 5} [all_macro_cells]\n")

output.write("set_attribute [all_macro_cells] is_fixed false\n")
output.write("set_attribute [all_macro_cells] dont_touch false\n")

for entry in input:
    if "anchor_to_macro" in entry:
        output.write("set_fp_relative_location -name %s -target_cell %s -target_orientation %s -target_corner %s -anchor_corner %s -x_offset %s -y_offset %s -anchor_object %s" % (entry["macro"], entry["macro"], entry["orientation"], entry["corner_on_macro_to_match"], entry["corner_on_anchor_macro_to_match"], entry["offset_x"], entry["offset_y"], entry["anchor_to_macro"]))

    if "anchor_to_cell" in entry:
        if entry["anchor_to_cell"] != args.top:
           print("floorplan2tcl error: anchor_to_cell is not equal to top '%s'!" % args.top)
           exit(1)
        output.write("set_fp_relative_location -name %s -target_cell %s -target_orientation %s -target_corner %s -anchor_corner %s -x_offset %s -y_offset %s" % (entry["macro"], entry["macro"], entry["orientation"], entry["corner_on_macro_to_match"], entry["corner_on_anchor_cell_to_match"], entry["offset_x"], entry["offset_y"]))

    output.write('\n')

output.write("create_fp_placement -no_legalize\n")

output.write("set_attribute [all_macro_cells] is_fixed true\n")
output.write("set_attribute [all_macro_cells] dont_touch true\n")

output.write("save_mw_cel -as floorplan\n")

output.write("create_fp_placement -effort high -timing_driven -optimize_pins\n")

# Power and Ground floorplanning
output.write("derive_pg_connection -power_net VDD -power_pin VDD -create_port top\n")
output.write("derive_pg_connection -ground_net VSS -ground_pin VSS -create_port top\n")
output.write("set_power_plan_strategy core -nets {VDD VSS} -core -template saed_32nm.tpl:m45_mesh(0.5,1.0)\n")
output.write("synthesize_fp_rings -nets {VDD VSS} -layers {M4 M5} -width {1.25 1.25} -space {0.5 0.5} -offset {1 1} -core\n")
output.write("compile_power_plan\n")

output.write("insert_stdcell_filler -connect_to_power {VDD} -connect_to_ground {VSS}\n")
output.write("preroute_standard_cells -do_not_route_over_macros -extend_for_multiple_connections\n")
output.write("remove_stdcell_filler -stdcell\n")

output.write("verify_pg_nets\n")
output.write("save_mw_cel -as power\n")

output.write("echo Floorplanning Done\n")

output.close
