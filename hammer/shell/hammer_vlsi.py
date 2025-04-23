#  hammer-vlsi
#  CLI script - by default, it just uses the default CLIDriver.
#
#  See LICENSE for licence details.
'''
from hammer.vlsi import CLIDriver

def main():
    CLIDriver().main()

'''
import re
import os
import subprocess
import sys
import json

from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.models.param import Param
from airflow.utils.trigger_rule import TriggerRule
from airflow.utils.task_group import TaskGroup
from datetime import datetime
from airflow.exceptions import AirflowSkipException
from airflow.decorators import task, dag
from airflow.models import Variable

import pendulum
from pathlib import Path

# Add the parent directory to the Python path to allow imports from 'vlsi'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'vlsi')))

#from hammer.vlsi import CLIDriver

import hammer.vlsi as hammer_vlsi

from hammer.vlsi import CLIDriver, HammerTool, HammerToolHookAction, HammerDriver, HierarchicalMode

from typing import Dict, Callable, Optional, List

from hammer.utils import deepdict, get_or_else

# Decorator to add attribute to hooks preventing write_db
def nowritedb(func):
    def wrapper():
        func.write_db = False
        print("\n\nDISABLING WRITE_DB\n\n")
        return func
    return wrapper()

@nowritedb
def create_timing_arrays(x : HammerTool):
    x.append('''
        set step_name []
        set step_runtime []
    ''')
    return True

@nowritedb
def print_runtime(x : HammerTool):
    x.append('''
        # Print the header of the table
        puts "-----------------------------------------"
        puts [format "| %-15s | %-17s |" "Step" "Runtime (seconds)"]
        puts "-----------------------------------------"

        # Loop through the arrays and print the function names and runtimes
        set len [llength $step_names]
        for {set i 0} {$i < $len} {incr i} {
            set funcName [lindex $step_names $i]
            set runtime [lindex $step_runtimes $i]
            # Format the output to ensure the table looks nice
            puts [format "| %-15s | %-17s |" $funcName $runtime]
        }

        puts "-----------------------------------------"
        ''')

def unique_start_time_hook(name: str):
    @nowritedb
    def dynamic_function(x: hammer_vlsi.HammerTool) -> bool:
        x.append(f'''
            set {name}_start_time_sec [clock seconds]
        ''')
        return True

    func_name = f"{name}_start_time"

    # Change underlying function name to ensure functional
    dynamic_function.__name__ = func_name

    # Dynamically assign the function to the given name in the global namespace
    globals()[func_name] = dynamic_function
    return dynamic_function

def unique_stop_time_hook(name: str):
    @nowritedb
    def dynamic_function(x: hammer_vlsi.HammerTool) -> bool:
        x.append(f'''
            set {name}_end_time_sec [clock seconds]
            set {name}_runtime [expr ${name}_end_time_sec - ${name}_start_time_sec]
            lappend step_name "{name}"
            lappend step_runtime ${name}_runtime
            puts "{name} Total Runtime: [clock format $runtime -format %H:%M:%S]
        ''')
        return True

    # Change underlying function name to ensure functional
    dynamic_function.__name__ = f"{name}_stop_time"

    # Dynamically assign the function to the given name in the global namespace
    globals()[name] = dynamic_function
    return dynamic_function

@nowritedb
def get_runtime_start(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        set start_time_sec [clock seconds]
        ''')
    return True

@nowritedb
def report_runtime(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        set end_time_sec [clock seconds]
        set runtime [expr $end_time_sec - $start_time_sec]
        puts "Total Runtime: [clock format $runtime -format %H:%M:%S]
        ''')
    return True

# Temporary fix as top level not togeher yet DEF needs modifications
def stop_route_after_20_iterations(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        puts "Stopping routing after 20 iterations"
        set_db route_detail_end_iteration 20
        ''')

    return True


"""
    Add in 4x4 GMB DEF
"""
def add_gmb_def(x: hammer_vlsi.HammerTool) -> bool:
    # Skip routing on top level GMB, as all routing is handled in GMB DEF
    #for bump in x.get_bumps().assignments:
    #    if not bump.no_connect and bump.name not in ["vdd", "vddv", "vss"]:
    #        x.append("set_db net:Intel4x4ChipTop/{} .skip_routing true".format(bump.name))

    abs_path = os.path.abspath("./physical/def/kodiak_top_def_pre_ddr.def")
    #x.append("read_def /tools/intech22/local/shared_resources/def_util/hl_core_top_gmb_final.def")
    #x.append("read_def /tools/C/kho_t/monet/bag3_ams_intel22ffl/digital_collat/delivery_051124/hl_core_top.def")
    #x.append("read_def /bwrcq/C/kho_t/monet/bag3_ams_intel22ffl/digital_collat/delivery_051324/hl_core_top_merged.def")
    #x.append("read_def /tools/C/kho_t/monet/bag3_ams_intel22ffl/digital_collat/delivery_051324/hl_core_top_final_unmerged.def")
    x.append(f"read_def {abs_path}")
    return True

"""
    Add in vias from GMB to GMZ so power straps are connected to rails
"""
def add_gv0_via(x: hammer_vlsi.HammerTool) -> bool:
    x.append("set pll [get_db insts -if {.base_cell == *ringpll*}]")
    x.append("set pll_bbox [get_db $pll .bbox]")

    x.append("set_db generate_special_via_ignore_drc true")
    x.append("update_power_vias -add_vias 1 -bottom_layer gm0 -top_layer gmb")

    x.append("delete_obj [get_db route_blockages -if {.name == pll_blockage}]")
    #x.append("update_power_vias -area $pll_bbox -add_vias 1 -bottom_layer gmz -top_layer gmb")
    x.append("set_db generate_special_via_ignore_drc false")

    return True

"""
    Supply power for PLL
"""
def pll_power(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        set pll [get_db insts -if {.base_cell == *ringpll*}]
        set pll_bbox [get_db $pll .bbox]

        create_route_blockage -pg_nets -rect [get_computed_shapes [get_db $pll .bbox] SIZE 10] -name pll_blockage -layers {gmz gm0 gmb}

        select_obj $pll
        set_db add_rings_stacked_via_bottom_layer m7
        add_rings -type block_rings -around selected -layer {top m8 bottom m8 right m7 left m7} -nets {vddv vss vdd} -spacing 0.5 -offset 3.1 -width 0.90000 -use_wire_group 1
        reset_db add_rings_stacked_via_bottom_layer
        deselect_obj -all

        delete_obj [get_db route_blockages -if {.name == pll_blockage}]

        reset_db -category add_stripes
        set_db add_stripes_stacked_via_top_layer gmz
        set_db add_stripes_stacked_via_bottom_layer m7
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.000
        set_db add_stripes_extend_to_closest_target ring

        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m8 -block_ring_top_layer_limit m7 -direction horizontal -layer m8 -nets {vss vdd vddv} -pad_core_ring_bottom_layer_limit m7 -set_to_set_distance 13.50 -spacing 0.90 -switch_layer_over_obs 0 -width 0.9 -area $pll_bbox

        set_db add_stripes_stacked_via_top_layer gmb
        set_db add_stripes_stacked_via_bottom_layer m8
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.000
        set_db add_stripes_extend_to_closest_target ring
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit gmz -block_ring_top_layer_limit m8 -direction vertical -layer gmz -nets {vss vdd vddv} -pad_core_ring_bottom_layer_limit m8 -set_to_set_distance 15.12 -spacing 0.54 -switch_layer_over_obs 0 -width 2.70 -area $pll_bbox

        # set_db add_stripes_stacked_via_top_layer gm0
        # set_db add_stripes_stacked_via_bottom_layer gmz
        # set_db add_stripes_trim_antenna_back_to_shape {stripe}
        # set_db add_stripes_spacing_from_block 2.700
        # add_stripes -create_pins 0 -block_ring_bottom_layer_limit gm0 -block_ring_top_layer_limit gmz -direction horizontal -layer gm0 -nets {vss vdd vddv} -pad_core_ring_bottom_layer_limit gmz -set_to_set_distance 15.12 -spacing 0.54 -switch_layer_over_obs 0 -width 2.70 -area $pll_bbox

        reset_db -category add_stripes

        # Add via only over pll inside power ring ( hier block + halo)
        # Below is neccessary to constrain via creation to specified area
        set old_generate_special_via_area_only [get_db generate_special_via_area_only]
        set_db generate_special_via_area_only 1
        # Update vias (this generate a warning about how the area is specified, but seems to work. the issue is variable. if hardcode area used then no warning)
        update_power_vias -add_vias 1 -nets {vss vdd vddv} -bottom_layer gmz -top_layer gmb  -area [get_db [get_db insts -if {.base_cell == *ringpll*}] .place_halo_bbox]  -split_vias 1
        # Switch back
        set_db generate_special_via_area_only $old_generate_special_via_area_only

        # set expansion_box [get_computed_shapes $pll_bbox SIZE 9]
        # update_power_vias -add_vias 1 -nets {vss vdd vddv} -bottom_layer gmz -top_layer gmb  -area $expansion_box  -split_vias 1
        create_route_blockage -pg_nets -rect [get_computed_shapes [get_db $pll .bbox] SIZE 5] -name pll_blockage -layers {m1 m2 m3 m4 m5 m6 m7 m8 gmz}
        create_route_blockage -rect [get_computed_shapes [get_db $pll .bbox] SIZE 5] -name pll_route_blockage -layers {m7}
    ''')
    return True

def global_power(x: HammerTool) -> bool:
    x.append('''
        set_db init_power_nets {vdd vddv VDDQ VDD_PRE vddh_q1 vddh_q1_tx}
        set_db init_ground_nets {vss}
        connect_global_net vdd -type pg_pin -pin vdd -override
        connect_global_net vdd -type pg_pin -pin vcc -override
        connect_global_net vdd -type pg_pin -pin vcc_nom -override
        connect_global_net vdd -type pg_pin -pin vccdig_nom -override
        connect_global_net vdd -type pg_pin -pin vccdist_nom -override
        connect_global_net vdd -type pg_pin -pin vnnaon_nom -override
        connect_global_net vdd -type pg_pin -pin vddp -override
        connect_global_net vdd -type pg_pin -pin VDD -override
        connect_global_net vss -type pg_pin -pin vss -override
        connect_global_net vss -type pg_pin -pin vssx -override
        connect_global_net vss -type pg_pin -pin vssp -override
        connect_global_net vss -type pg_pin -pin vssb -override
        connect_global_net vss -type pg_pin -pin VSS -override
        connect_global_net vddv -type pg_pin -pin vddv -override
        connect_global_net vddv -type pg_pin -pin vccio -override
        connect_global_net vddv -type pg_pin -pin vccldo_hv -override
        connect_global_net vddv -type pg_pin -pin vddh -override
        connect_global_net VDDQ -type pg_pin -pin VDDQ -override
        connect_global_net VDD_PRE -type pg_pin -pin VDD_PRE -override
        connect_global_net vddh_q1 -type pg_pin -pin vddh_q1 -override
        connect_global_net vddh_q1_tx -type pg_pin -pin vddh_q1_tx -override
        set_db add_stripes_detailed_log true
    ''')
    return True

def group_instances(x: HammerTool) -> bool:
    x.append('''
        group -name tile_prci_domain [get_db hinst:Intel4x4ChipTop/system/tile_prci_domain] [get_db hinst:Intel4x4ChipTop/system/sbus_system_bus_noc_acd_noc_noc_router_sink_domain_4]
        group -name tile_prci_domain_1 [get_db hinst:Intel4x4ChipTop/system/tile_prci_domain_1] [get_db hinst:hinst:Intel4x4ChipTop/system/sbus_system_bus_noc_acd_noc_noc_router_sink_domain_5]
        group -name tile_prci_domain_2 [get_db hinst:Intel4x4ChipTop/system/tile_prci_domain_2] [get_db hinst:hinst:Intel4x4ChipTop/system/sbus_system_bus_noc_acd_noc_noc_router_sink_domain_6]
        group -name tile_prci_domain_3 [get_db hinst:Intel4x4ChipTop/system/tile_prci_domain_3] [get_db hinst:hinst:Intel4x4ChipTop/system/sbus_system_bus_noc_acd_noc_noc_router_sink_domain_7]
        set_db group_instance_suffix ""
    ''')
    return True

def disable_bound_opt(x: HammerTool) -> bool:
    x.append('''
        set_db [get_db design:Intel4x4ChipTop .modules *sbus_system_bus_noc_acd_noc_noc_router_sink_domain*] .boundary_opto false
        set_db [get_db design:Intel4x4ChipTop .modules *sbus_system_bus_noc_be_noc_noc_router_sink_domain*] .boundary_opto false
    ''')
    return True


def force_tieoff(x: HammerTool) -> bool:
    x.append('''
        set_db add_tieoffs_max_fanout 1
        add_tieoffs -lib_cell "b15tilo00an1n03x5 b15tihi00an1n03x5" -report_hier_ports true
    ''')
    return True

"""
    For DSP/ML tapeout Innovus was misbehaving and not adding filler
    cells at the bottom right corner of all hierarchial blocks. This
    hook is meant to resolve that issue. (It enumerates all hier blocks;
    their may bne a cleaner way, however Kevin A could not find one)
"""
def add_fillers(x: HammerTool) -> bool:
    # Generate string
    filler_str = "unflatten_ilm\n"
    hier_block_path = [constr.path for constr in x.get_placement_constraints() if "system" in constr.path]
    for block in ["/".join(i.split("/")[1:]) for i in hier_block_path]:
        filler_str += "set fill_area [get_computed_shapes [get_db [get_db insts -if {{ .name == {} }}] .place_halo_bbox] SIZE 2.5]\n".format(block)
        filler_str += "add_fillers -area $fill_area\n"
    filler_str += "flatten_ilm\n"
    x.append(filler_str)

    # PLL has a place obstruct in addition to the routing halo, so need to take care of that with extra SIZE
    x.append("unflatten_ilm")
    x.append("set pll_insts [get_db [get_db insts -if { .base_cell == *ringpll* }]]")
    x.append('''foreach pll_inst $pll_insts {
                    set fill_area [get_computed_shapes [get_db $pll_inst .place_halo_bbox] SIZE 10]
                    add_fillers -area $fill_area
                }
             ''',clean=True)

    # IO cells create a gap in the middle of the chip with one filler missing on the corner
    # Only doing this for a region for now, need to find smarter way
    x.append("add_fillers -area {180.10000 2079.60150 180.31250 2078.77150}")
    x.append("add_fillers -area {179.94750 2006.07550 180.52750 2005.13500}")
    # PRS Corner filler (Top right)
    x.append("add_fillers -area {3906.02600 4006.07200 3908.65350 4003.89700}")
    x.append("add_fillers -area {180.07800 2079.68650 180.33900 2078.91650}")
    x.append("add_fillers -area {180.04500 3492.79750 180.39700 3491.97700}")
    x.append("add_fillers -area {75.56950 4008.10150 75.76200 4007.39250}")
    x.append("add_fillers -area {3907.25400 2079.68550 3907.50450 2078.95400}")
    x.append("flatten_ilm")

    #print(filler_str)

    return True

def syn_opt_top(x: hammer_vlsi.HammerTool) -> bool:
    x.append("syn_opt")
    return True

def io_placement(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        read_io_file {io_file} -no_die_size_adjust
    '''.format(io_file=os.getcwd() + '/' + x.get_setting("dsp.io_file")), clean=True)
    #x.append("stop")
    #create_net -name vccio -physical -power
    #connect_global_net vddv -type pg_pin -pin_base_name vccio -verbose
    #connect_global_net vss -type pg_pin -pin_base_name vssp -verbose
    #connect_global_net vss -type pg_pin -pin_base_name vssb -verbose
    #connect_global_net vdd -type pg_pin -pin_base_name vcc_nom -verbose
    #connect_global_net vss -type pg_pin -pin_base_name vssx -verbose

    # if you put something like DICs outside the core the default hook is buggy
    for ring in range(x.get_setting("technology.intech22.io_rings")):
        x.append('''
            add_io_fillers -io_ring {ring_num} -side top    -cells spacer_2lego_n1 -filler_orient r0 -prefix iofill_
            add_io_fillers -io_ring {ring_num} -side bottom -cells spacer_2lego_n1 -filler_orient mx -prefix iofill_
            add_io_fillers -io_ring {ring_num} -side left   -cells spacer_2lego_e1 -filler_orient r0 -prefix iofill_
            add_io_fillers -io_ring {ring_num} -side right  -cells spacer_2lego_e1 -filler_orient my -prefix iofill_
        '''.format(ring_num=ring+1), clean=True)
    x.append("stop")
    return True

def fc_route(x: hammer_vlsi.HammerTool) -> bool:
      x.append('''
      # --- Add core rings ---
      # add_rings -type core_rings -nets {{vdd vss}} -width 5.400 -layer {{ top gm0 bottom gm0 left gmb right gmb }} -follow core -spacing 1.08 -center 1

      # --- FC Router Settings ---
      set_db flip_chip_route_width {width}
      set_db flip_chip_allow_routed_bump_edit false
      set_db flip_chip_route_style manhattan

      # --- Route VCCIO ---
      set_db flip_chip_top_layer gmb
      set_db flip_chip_bottom_layer gm0
      route_flip_chip -double_bend_route -incremental -verbose -keep_drc -target connect_bump_to_ring_stripe -nets {{ vddv }}

      # --- Route Signals ---
      select_bumps -type signal
      route_flip_chip -target connect_bump_to_pad -incremental -selected_bumps -double_bend_route -keep_drc -verbose
      deselect_bumps

      # route vcc and vss to rings
      set_db flip_chip_top_layer gmb
      set_db flip_chip_bottom_layer gm0
      #route_flip_chip -double_bend_route -incremental -verbose -keep_drc -target connect_bump_to_ring_stripe -nets {{ vdd vss }}

      # reset_db flip_chip_bottom_layer
      # reset_db flip_chip_top_layer
      '''.format(width=x.get_setting("technology.intech22.fc_route_width")), clean=True)
      #x.append("stop")
      return True

def breakpoint(x: hammer_vlsi.HammerTool) -> bool:
    x.append("stop")
    x.append("gui_show")
    return True

def change_par_clock_frequency(x: hammer_vlsi.HammerTool) -> bool:
    #x.append(f"create_clock -name clock -period 1.5 -waveform {0.0 0.75} [get_ports clock]")
    return True

def change_toplevel_par_clock_frequencies(x: hammer_vlsi.HammerTool) -> bool:
    #x.append(f"create_clock -name pll -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/pll/pll/clkpll]")
    #x.append(f"create_clock -name pll0 -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/pll/pll/clkpll0]")
    #x.append(f"create_clock -name pll1 -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/pll/pll/clkpll1]")
    #x.append(f"create_clock -name selector_uncore_clock -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/clockSelector/auto_clock_out_member_allClocks_uncore_clock]")
    #x.append(f"create_clock -name divider_uncore_clock -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/clockDivider/auto_clock_out_member_allClocks_uncore_clock]")
    #x.append(f"create_clock -name uncore_clock -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/clock_gater/auto_clock_gater_out_member_allClocks_uncore_clock]")
    pass

def shift_phy_to_absolute_coordinates(x: hammer_vlsi.HammerTool) -> bool:
    x.append("update_origin -location 1925.424 18.9")
    return True

"""
    Add in UCIe def routing on quadrant 1
"""
def add_ucieq1_def(x: hammer_vlsi.HammerTool) -> bool:
    x.append("read_def /bwrcq/C/di_wang/intech22/bag3_ams_intel22ffl/UCIe_Analog_IO_routing_Di.def")
    return True

def add_ucieq1_def_local(x: hammer_vlsi.HammerTool) -> bool:
    path = os.path.join(os.getcwd(), "ucie_analog/ip/analog_routing/analog_routing_local_lanes16_sideband.def")
    x.append(f"read_def -special_nets {path}")

    # Add vias between shielding nets and add blockages around shielding
    x.append("""
    set_db generate_special_via_cut_class_preference { Via8_400x120 }
    update_power_vias -add_vias 1 -nets vss -bottom_layer m7 -top_layer gm0
    edit_update_route_status -nets vss -to cover
    set_db generate_special_via_cut_class_preference default
    select_routes -nets vss
    foreach wire [get_db selected] {
        create_route_blockage -name ucie_shield_blockages -layers [get_db $wire .layer] -rect [get_db $wire .rect] -spacing 2.7
    }
    deselect_routes
    """)

    x.append(f"read_def {path}")

    return True

def add_ucie_shielding_vias(x: hammer_vlsi.HammerTool) -> bool:
    x.append("""
    foreach blockage [get_db route_blockages ucie_shield_blockages] {
        delete_obj $blockage
    }
    update_power_vias -add_vias 1 -nets vss -bottom_layer m7 -top_layer gm0
    """)

    return True

def write_ucie_power_spec(x: hammer_vlsi.HammerTool) -> bool:
    power_spec_file = os.path.join(x.run_dir, "power_spec.cpf")
    x.append(f'''bash -c "cat << EOF > {power_spec_file}
        # --------------------------------------------------------------------------------
        # This script was written and developed by HAMMER at UC Berkeley; however, the
        # underlying commands and reports are copyrighted by Cadence. We thank Cadence for
        # granting permission to share our research to help promote and foster the next
        # generation of innovators.
        # --------------------------------------------------------------------------------

        set_cpf_version 1.0e
        set_hierarchy_separator /
        set_design UciephyTestTL
        create_power_nets -nets vddh_q1 -voltage 0.85
        create_power_nets -nets vddh_q1_tx -voltage 0.85
        create_ground_nets -nets {{ vss }}
        create_power_domain -name AO -default
        update_power_domain -name AO -primary_power_net vddh_q1 -primary_ground_net vss
        create_global_connection -domain AO -net vddh_q1 -pins \[list vcc vcc_nom vccdig_nom vccdist_nom vnnaon_nom vddp vdd VDD\]
        create_global_connection -domain AO -net vss -pins \[list vssx vss vssp vssb VSS\]
        create_nominal_condition -name nominal -voltage 0.8
        create_power_mode -name aon -default -domain_conditions {{AO@nominal}}
        end_design
EOF"''')
    return True

def write_ucie_netlist_with_pg_pins(x: hammer_vlsi.HammerTool) -> bool:
    x.append(f"write_netlist {x.output_netlist_filename} -top_module_first -top_module UciephyTestTL -export_top_pg_nets -exclude_leaf_cells -phys -flat -exclude_insts_of_cells {{ b88xdicplyxi000xx4ulx b88xdicregx6000xx2ulx b88xdiccd0x6000xx2ulx fdk22tic2_dicrecdply_cont fdk22tic2m1_dicreg_cont b15qgbdcpah1n04x5 b15qgbdcpah1n08x5 b15qgbdcpah1n16x5 b15qgbdcpah1n32x5 b15qgbdcpah1n64x5 b15qgbdcpal1n04x5 b15qgbdcpal1n08x5 b15qgbdcpal1n16x5 b15qgbdcpal1n32x5 b15qgbdcpal1n64x5 b15qgbdcpam1n04x5 b15qgbdcpam1n08x5 b15qgbdcpam1n16x5 b15qgbdcpam1n32x5 b15qgbdcpam1n64x5 b15qgbdcpan1n04x5 b15qgbdcpan1n08x5 b15qgbdcpan1n16x5 b15qgbdcpan1n32x5 b15qgbdcpan1n64x5 b15qgbdp1ah1n00x5 b15qgbdp1al1n00x5 b15qgbdp1am1n00x5 b15qgbdp1an1n00x5 b15qgbtl1ah1n00x5 b15qgbtl1al1n00x5 b15qgbtl1am1n00x5 b15qgbtl1an1n00x5 b15ydp151an1n03x5 b15ydp251an1n03x5 b15ygnc01an1d03x5 b15zdcf11al1n04x5 b15zdcf11al1n08x5 b15zdcf11al1n16x5 b15zdcf11al1n32x5 b15zdcf11al1n64x5 b15zdcf33al1n04x5 b15zdcf33al1n08x5 b15zdcf33al1n16x5 b15zdcf33al1n32x5 b15zdcf33al1n64x5 b15zdcf55al1n04x5 b15zdcf55al1n08x5 b15zdcf55al1n16x5 b15zdcf55al1n32x5 b15zdcf55al1n64x5 fdk22tic4m1_diccd_cont fdk22tic4m1_dicreg_cont 8snf22s_tma0_a0_2x2sub4x4_c4_er_edm_prs_top_cnr uni2_2x2sub4x4_c4_er_edm_prs_top_cnr uni2_4x4_c4_er_edm_prs_top }}")
    return True

def write_ucie_lef_with_gm0_top_layer(x: hammer_vlsi.HammerTool) -> bool:
    x.append("write_lef_abstract -5.8 -top_layer gmz -stripe_pins -pg_pin_layers gmz -obs_above_top_layer gm0 UciephyTestTLILM.lef")
    return True

UCIE_LANES = 16
UCIE_IO_NETS = [
    f"auto_top_io_out_txData_{i}" for i in range(UCIE_LANES)
] + [
    f"auto_top_io_out_rxData_{i}" for i in range(UCIE_LANES)
] + [
  "auto_top_io_out_txValid",
  "auto_top_io_out_refClkP",
  "auto_top_io_out_refClkN",
  "auto_top_io_out_txClkP",
  "auto_top_io_out_txClkN",
  "auto_top_io_out_rxValid",
  "auto_top_io_out_rxClkP",
  "auto_top_io_out_rxClkN",
  "auto_top_io_out_sbTxClk",
  "auto_top_io_out_sbTxData",
  "auto_top_io_out_sbRxClk",
  "auto_top_io_out_sbRxData",
]

UCIE_DONT_TOUCH_NETS = UCIE_IO_NETS[:-2] + [
  "phy/_refClkRx_vop",
  "phy/_refClkRx_von",
  "phy/_rxClkP_io_clkout",
  "phy/_rxClkN_io_clkout",
  "phy/_clkMuxP_out",
  "phy/_clkMuxN_out",
]

UCIE_CELLS = [
  "ucie_clkmux",
  "rxclk_with_esd",
  "rxtile",
  "txclk_with_esd",
  "txdatatile_dll",
  "ucie_esd",
  "ucie_esd_routable",
  "refclkrx",
]

def ucie_dont_route(x: hammer_vlsi.HammerTool) -> bool:
    for net in UCIE_DONT_TOUCH_NETS:
      x.append(f"set_route_attributes -nets {net} -skip_routing true")
    return True

def dont_touch_phy_tiles(x: hammer_vlsi.HammerTool) -> bool:
    x.append(f"set_dont_touch {{{' '.join(UCIE_CELLS)}}} true")
    return True

def dont_touch_top_level_signals_syn(x: hammer_vlsi.HammerTool) -> bool:
    x.append("set_dont_touch [get_nets -segments {%s}] true" % " ".join(UCIE_DONT_TOUCH_NETS))
    return True

def dont_touch_top_level_signals_par(x: hammer_vlsi.HammerTool) -> bool:
    x.append("set_dont_touch [get_nets {%s}] true" % " ".join(UCIE_DONT_TOUCH_NETS))
    return True

def place_macro_blockages(x: HammerTool) -> bool:
    x.append('''
        foreach inst [get_db insts -if { .base_cell == *fdk22b82lto_b88xesdclpn6000qnxcnx}] {
            set pg_blockage_shape [get_db $inst .place_halo_polygon]

            create_route_blockage -pg_nets -layers {m1 m2 m3 m4 m5 m6} -polygon $pg_blockage_shape

        }
    ''')

    x.append(f'''
        foreach inst [get_db insts -if {{{ "||".join([f" .base_cell == *{cell} " for cell in UCIE_CELLS])}}}] {{
            set pg_blockage_shape [get_db $inst .place_halo_polygon]

            create_route_blockage -pg_nets -layers {{m1 m2 m3 m4 m5 m6 m7 m8}} -polygon $pg_blockage_shape

        }}
    ''')
    x.append(f'''
      create_route_halo -bottom_layer m1 -space 2.7 -top_layer m8 -cells {{{" ".join(UCIE_CELLS)}}}
    ''')

    # Place SRAMs (moved to Hammer)
    # x.append('''
    #     set x 1492.56
    #     foreach inst [get_db insts -if { .base_cell == *ip224* && .name == *test/inputBuffer* }] {
    #         place_inst $inst $x 240.66 r0 -fixed
    #         create_route_halo -bottom_layer m1 -space 2.7 -top_layer m4 -inst [get_db $inst .name]
    #         create_place_halo -insts [get_db $inst .name] -halo_deltas {3.0 3.0 3.0 3.0} -snap_to_site
    #         set pg_blockage_shape [get_db $inst .place_halo_polygon]
    #         create_route_blockage -pg_nets -layers {m1 m2 m3 m4} -polygon $pg_blockage_shape
    #         set x [ expr { $x + 100.44 }]
    #     }

    #     set x 1492.56
    #     foreach inst [get_db insts -if { .base_cell == *ip224* && .name == *test/outputBuffer* }] {
    #         place_inst $inst $x 60.48 r0 -fixed
    #         create_route_halo -bottom_layer m1 -space 2.7 -top_layer m4 -inst [get_db $inst .name]
    #         create_place_halo -insts [get_db $inst .name] -halo_deltas {3.0 3.0 3.0 3.0} -snap_to_site
    #         set pg_blockage_shape [get_db $inst .place_halo_polygon]
    #         create_route_blockage -pg_nets -layers {m1 m2 m3 m4} -polygon $pg_blockage_shape
    #         set x [ expr { $x + 100.44 }]
    #     }

    # ''')

    return True

def place_esd_plus_antenna_blockages(x: HammerTool) -> bool:
    x.append('''
        foreach inst [get_db insts -if { .base_cell == *ucie_esd }] {
            set pg_blockage_shape [get_db $inst .place_halo_polygon]
            create_route_blockage -layers {m1 m2 m3 m4 m5 m6 m7 m8} -polygon $pg_blockage_shape
        }
        foreach inst [get_db insts -if { .base_cell == *ucie_esd_routable }] {
            set pg_blockage_shape [get_db $inst .place_halo_polygon]
            create_route_blockage -pg_nets -layers {m1 m2 m3 m4 m5 m6 m7 m8} -polygon $pg_blockage_shape
            create_route_blockage -except_pg_nets -layers {m1 m2 m3 m4 m5 m6 m7} -polygon $pg_blockage_shape
        }
        foreach inst [get_db insts -if { .base_cell == *ucie_antenna_diode }] {
            set route_blockage_shape [get_db $inst .place_halo_polygon]
            create_route_blockage -except_pg_nets -layers {m1 m2 m3 m4 m5 m6 m7 m8} -polygon $route_blockage_shape
            create_route_blockage -pg_nets -layers {m1 m2} -polygon $route_blockage_shape
        }
    ''')

    return True

def assign_ucie_io_pins(x: HammerTool) -> bool:
    x.append(f'''
        set_db assign_pins_edit_in_batch true
        set_db assign_pins_promoted_macro_bottom_layer m1
        set_db assign_pins_promoted_macro_top_layer c4
        edit_pin -fixed_pin -pin auto_in* -hinst UciephyTestTL -pattern fill_optimised -layer {{ m5 m7 }} -side top -end {{ 1977.264 997.272 }} -start {{ 1377.0 997.272 }}
        edit_pin -fixed_pin -pin auto_uciTL* -hinst UciephyTestTL -pattern fill_optimised -layer {{ m5 m7 }} -side top -end {{ 1377.0 997.272 }} -start {{ 776.952 997.272 }}
        edit_pin -fixed_pin -pin auto_clock* -hinst UciephyTestTL -spread_type range -layer {{ m7 }} -side top -end {{ 776.952 997.272 }} -start {{ 773.952 997.272 }}
        edit_pin -fixed_pin -pin auto_uciTL_clock* -hinst UciephyTestTL -spread_type range -layer {{ m5 }} -side top -end {{ 773.952 997.272 }} -start {{ 770.952 997.272 }}
        set_db assign_pins_edit_in_batch false
        set_promoted_macro_pin -insts *txLane* -pins dout
        set_promoted_macro_pin -insts *rxLane* -pins din
        set_promoted_macro_pin -insts *txClk* -pins clkout
        set_promoted_macro_pin -insts *rxClk* -pins clkin
        set_promoted_macro_pin -insts *refClkRx* -pins vi*
        set_promoted_macro_pin -insts *sbTx* -pins clkout
        set_promoted_macro_pin -insts *sbRx* -pins term
        assign_io_pins -pins {{ {" ".join(UCIE_IO_NETS)} }}
    ''')

    return True

def ucie_block_power_straps(x: HammerTool) -> bool:
    x.append('''
        # Power strap definition for layer m3:

        set_db add_stripes_stacked_via_top_layer m3
        set_db add_stripes_stacked_via_bottom_layer m2
        set_db add_stripes_trim_antenna_back_to_shape {none}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m3 -block_ring_top_layer_limit m2 -direction vertical -layer m3 -nets {vss vddh_q1} -pad_core_ring_bottom_layer_limit m2 -set_to_set_distance 1.80 -spacing 0.226 -switch_layer_over_obs 0 -width 0.044 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 1.058]

        # Power strap definition for layer m4:

        set_db add_stripes_stacked_via_top_layer m4
        set_db add_stripes_stacked_via_bottom_layer m3
        set_db add_stripes_trim_antenna_back_to_shape {none}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m4 -block_ring_top_layer_limit m3 -direction horizontal -layer m4 -nets {vss vddh_q1} -pad_core_ring_bottom_layer_limit m3 -set_to_set_distance 1.80 -spacing 0.226 -switch_layer_over_obs 0 -width 0.044 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 1] + 1.058]

        # Power strap definition for layer m5:

        set_db add_stripes_stacked_via_top_layer m5
        set_db add_stripes_stacked_via_bottom_layer m4
        set_db add_stripes_trim_antenna_back_to_shape {none}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m5 -block_ring_top_layer_limit m4 -direction vertical -layer m5 -nets {vss vddh_q1} -pad_core_ring_bottom_layer_limit m4 -set_to_set_distance 3.15 -spacing 0.164 -switch_layer_over_obs 0 -width 0.16 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 0.262]

        # Power strap definition for layer m6:

        set_db add_stripes_stacked_via_top_layer m6
        set_db add_stripes_stacked_via_bottom_layer m5
        set_db add_stripes_trim_antenna_back_to_shape {none}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m6 -block_ring_top_layer_limit m5 -direction horizontal -layer m6 -nets {vss vddh_q1} -pad_core_ring_bottom_layer_limit m5 -set_to_set_distance 3.60 -spacing 0.1 -switch_layer_over_obs 0 -width 0.2 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 1] + 1.113]

        # Power strap definition for layer m7:

        set_db add_stripes_stacked_via_top_layer m7
        set_db add_stripes_stacked_via_bottom_layer m6
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m7 -block_ring_top_layer_limit m6 -direction vertical -layer m7 -nets {vss vddh_q1} -pad_core_ring_bottom_layer_limit m6 -set_to_set_distance 7.20 -spacing 0.18 -switch_layer_over_obs 0 -width 0.54 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 4.05]

        # Power strap definition for layer m8:

        set_db add_stripes_stacked_via_top_layer m8
        set_db add_stripes_stacked_via_bottom_layer m7
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 0 -block_ring_bottom_layer_limit m8 -block_ring_top_layer_limit m7 -direction horizontal -layer m8 -nets {vss vddh_q1 vddh_q1_tx} -pad_core_ring_bottom_layer_limit m7 -set_to_set_distance 7.20 -spacing 0.18 -switch_layer_over_obs 0 -width 0.54 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 1] + 13.05]

        # Power strap definition for layer gmz:

        set_db add_stripes_stacked_via_top_layer gmz
        set_db add_stripes_stacked_via_bottom_layer m8
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.700
        add_stripes -create_pins 1 -block_ring_bottom_layer_limit gmz -block_ring_top_layer_limit m8 -direction vertical -layer gmz -nets {vss vddh_q1 vddh_q1_tx} -pad_core_ring_bottom_layer_limit m8 -set_to_set_distance 2.16 -spacing 0.54 -switch_layer_over_obs 0 -width 0.54 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 12.15]
    ''')

    return True

def ucie_top_power_straps(x: HammerTool) -> bool:
    x.append('''
        # This area is bottom left PRS corner
        set bl_prs_corner {17.28 18.9 75.60 76.86}

        # Power strap definition for layer gm0 over UCIe
        set uciephy [get_db insts -if {.base_cell == *UciephyTestTL*}]
        set uciephy_bbox [get_db $uciephy .bbox]
        set_db add_stripes_stacked_via_top_layer gm0
        set_db add_stripes_stacked_via_bottom_layer gmz
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.700

        # Add stripes but not over bottom left PRS corner
        add_stripes -area_blockage $bl_prs_corner -create_pins 1 -block_ring_bottom_layer_limit gm0 -block_ring_top_layer_limit gmz -direction horizontal -layer gm0 -nets {vss vddh_q1 vddh_q1_tx} -pad_core_ring_bottom_layer_limit gmz -set_to_set_distance 7.56 -spacing 2.70 -switch_layer_over_obs 0 -width 2.70 -area $uciephy_bbox -start [expr [lindex [lindex $uciephy_bbox 0] 1] + 12.15]
    ''')

    return True

def convert_ucie_sb_rx_to_regular_nets(x: HammerTool) -> bool:
    x.append("""
    select_routes -net *sbRxData*
    set sbRxData_rects [get_db [get_db selected] .rect]
    set sbRxData_layers [get_db [get_db selected] .layer]
    delete_obj [get_db selected]
    select_routes -net *sbRxClk*
    set sbRxClk_rects [get_db [get_db selected] .rect]
    set sbRxClk_layers [get_db [get_db selected] .layer]
    delete_obj [get_db selected]
    """)

    return True

def add_back_ucie_sb_rx_special_net_geometry(x: HammerTool) -> bool:
    x.append("""
    foreach rect $sbRxData_rects layer $sbRxData_layers {
        create_shape -net auto_top_io_out_sbRxData -rect $rect -layer [get_db $layer .name]
    }
    foreach rect $sbRxClk_rects layer $sbRxClk_layers {
        create_shape -net auto_top_io_out_sbRxClk -rect $rect -layer [get_db $layer .name]
    }
    """)

    return True

def syn_opt_top(x: hammer_vlsi.HammerTool) -> bool:
    x.append("syn_opt")
    return True

def io_placement(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        read_io_file {io_file} -no_die_size_adjust
    '''.format(io_file=os.getcwd() + '/' + x.get_setting("dsp.io_file")), clean=True)
    #x.append("stop")
    #create_net -name vccio -physical -power
    #connect_global_net vddv -type pg_pin -pin_base_name vccio -verbose
    #connect_global_net vss -type pg_pin -pin_base_name vssp -verbose
    #connect_global_net vss -type pg_pin -pin_base_name vssb -verbose
    #connect_global_net vdd -type pg_pin -pin_base_name vcc_nom -verbose
    #connect_global_net vss -type pg_pin -pin_base_name vssx -verbose

    # if you put something like DICs outside the core the default hook is buggy
    for ring in range(x.get_setting("technology.intech22.io_rings")):
        x.append('''
            add_io_fillers -io_ring {ring_num} -side top    -cells spacer_2lego_n1 -filler_orient r0 -prefix iofill_
            add_io_fillers -io_ring {ring_num} -side bottom -cells spacer_2lego_n1 -filler_orient mx -prefix iofill_
            add_io_fillers -io_ring {ring_num} -side left   -cells spacer_2lego_e1 -filler_orient r0 -prefix iofill_
            add_io_fillers -io_ring {ring_num} -side right  -cells spacer_2lego_e1 -filler_orient my -prefix iofill_
        '''.format(ring_num=ring+1), clean=True)
    x.append("stop")
    return True

def fc_route(x: hammer_vlsi.HammerTool) -> bool:
      x.append('''
      # --- Add core rings ---
      # add_rings -type core_rings -nets {{vdd vss}} -width 5.400 -layer {{ top gm0 bottom gm0 left gmb right gmb }} -follow core -spacing 1.08 -center 1

      # --- FC Router Settings ---
      set_db flip_chip_route_width {width}
      set_db flip_chip_allow_routed_bump_edit false
      set_db flip_chip_route_style manhattan

      # --- Route VCCIO ---
      set_db flip_chip_top_layer gmb
      set_db flip_chip_bottom_layer gm0
      route_flip_chip -double_bend_route -incremental -verbose -keep_drc -target connect_bump_to_ring_stripe -nets {{ vddv }}

      # --- Route Signals ---
      select_bumps -type signal
      route_flip_chip -target connect_bump_to_pad -incremental -selected_bumps -double_bend_route -keep_drc -verbose
      deselect_bumps

      # route vcc and vss to rings
      set_db flip_chip_top_layer gmb
      set_db flip_chip_bottom_layer gm0
      #route_flip_chip -double_bend_route -incremental -verbose -keep_drc -target connect_bump_to_ring_stripe -nets {{ vdd vss }}

      # reset_db flip_chip_bottom_layer
      # reset_db flip_chip_top_layer
      '''.format(width=x.get_setting("technology.intech22.fc_route_width")), clean=True)
      #x.append("stop")
      return True

def breakpoint(x: hammer_vlsi.HammerTool) -> bool:
    x.append("stop")
    x.append("gui_show")
    return True

def change_par_clock_frequency(x: hammer_vlsi.HammerTool) -> bool:
    #x.append(f"create_clock -name clock -period 1.5 -waveform {0.0 0.75} [get_ports clock]")
    return True

def change_toplevel_par_clock_frequencies(x: hammer_vlsi.HammerTool) -> bool:
    #x.append(f"create_clock -name pll -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/pll/pll/clkpll]")
    #x.append(f"create_clock -name pll0 -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/pll/pll/clkpll0]")
    #x.append(f"create_clock -name pll1 -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/pll/pll/clkpll1]")
    #x.append(f"create_clock -name selector_uncore_clock -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/clockSelector/auto_clock_out_member_allClocks_uncore_clock]")
    #x.append(f"create_clock -name divider_uncore_clock -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/clockDivider/auto_clock_out_member_allClocks_uncore_clock]")
    #x.append(f"create_clock -name uncore_clock -period 1.5 -waveform {0.0 0.75} [get_pins system/chipyard_prcictrl_domain/clock_gater/auto_clock_gater_out_member_allClocks_uncore_clock]")
    return True

def dont_touch_ddr(x: hammer_vlsi.HammerTool) -> bool:
    x.append( "set_dont_touch inst:Intel4x4ChipTop/system/chipyard_prcictrl_domain/ddrctrl/ddrclk true")
    return True

def set_dont_route(x: HammerTool) -> bool:
    ucie_clock = ['bump_48_14_net', 'bump_47_13_net', 'bump_48_12_net', 'bump_47_11_net','bump_48_10_net' ]
    ucie_debug = ['bump_48_22_net', 'bump_47_21_net', 'bump_48_20_net', 'bump_47_19_net',
                  'bump_48_18_net', 'bump_47_17_net', 'bump_48_16_net', 'bump_47_15_net']
    uciephy0 = ['bump_43_4_net', 'bump_27_2_net', 'bump_43_2_net',
                'bump_27_4_net', 'bump_31_8_net', 'bump_31_10_net', 'bump_39_10_net',
                'bump_39_8_net', 'bump_49_12_net', 'bump_42_1_net', 'bump_41_4_net',
                'bump_41_2_net', 'bump_40_3_net', 'bump_42_7_net', 'bump_41_10_net',
                'bump_41_8_net', 'bump_40_9_net', 'bump_38_9_net', 'bump_37_10_net',
                'bump_37_8_net', 'bump_36_7_net', 'bump_38_3_net', 'bump_37_4_net',
                'bump_37_2_net', 'bump_36_1_net', 'bump_39_2_net', 'bump_28_3_net',
                'bump_29_2_net', 'bump_29_4_net', 'bump_30_1_net', 'bump_28_9_net',
                'bump_29_8_net', 'bump_29_10_net', 'bump_30_7_net', 'bump_32_7_net',
                'bump_33_8_net', 'bump_33_10_net', 'bump_34_9_net', 'bump_32_1_net',
                'bump_33_2_net', 'bump_33_4_net', 'bump_34_3_net', 'bump_31_4_net',
                'bump_30_2_net', 'bump_38_4_net']
    uciephy1 = ['bump_6_4_net', 'bump_22_2_net', 'bump_6_2_net', 'bump_22_4_net',
                'bump_10_10_net', 'bump_10_8_net', 'bump_18_8_net', 'bump_18_10_net',
                'bump_7_1_net', 'bump_8_4_net', 'bump_8_2_net', 'bump_9_3_net',
                'bump_7_7_net', 'bump_8_10_net', 'bump_8_8_net', 'bump_9_9_net',
                'bump_11_9_net', 'bump_12_10_net', 'bump_12_8_net', 'bump_13_7_net',
                'bump_11_3_net', 'bump_12_4_net', 'bump_12_2_net', 'bump_13_1_net',
                'bump_10_4_net', 'bump_10_2_net', 'bump_21_3_net', 'bump_20_2_net',
                'bump_20_4_net', 'bump_19_1_net', 'bump_21_9_net', 'bump_20_8_net',
                'bump_20_10_net', 'bump_19_7_net', 'bump_17_7_net', 'bump_16_8_net',
                'bump_16_10_net', 'bump_15_9_net', 'bump_17_1_net', 'bump_16_2_net',
                'bump_16_4_net', 'bump_15_3_net', 'bump_18_2_net', 'bump_18_4_net']
    ddr = []
    power = ['VDD_PRE', 'VDDQ']

    manually_routed_nets = power + ucie_clock + ucie_debug + uciephy0 + uciephy1 + ddr

    x.append("flatten_ilm")
    for net in manually_routed_nets:
        x.append(f"set_route_attributes -nets {net} -skip_routing true")
    x.append("unflatten_ilm")
    return True

def ucie_reset_distribution(x: HammerTool) -> bool:
    setup_uncertainty = 0.08
    hold_uncertainty = 0.04
    margin = 1.02
    x.append("set_interactive_constraint_modes my_constraint_mode")

    def txlane(i):
        if i == 0:
            return "phy/txLane"
        else:
            return f"phy/txLane_{i}"
    def rxlane(i):
        if i == 0:
            return "phy/rxLane"
        else:
            return f"phy/rxLane_{i}"

    for i in range(UCIE_LANES+1):
        for j in range(UCIE_LANES+1):
            if i == j:
                continue
            x.append(f"set_data_check -from [get_pins {txlane(i)}/io_reset] -to [get_pins {txlane(j)}/io_reset] -clock [get_clocks auto_clock_in_clock] -setup {margin*setup_uncertainty}")
            x.append(f"set_data_check -from [get_pins {txlane(i)}/io_reset] -to [get_pins {txlane(j)}/io_reset] -clock [get_clocks auto_clock_in_clock] -hold {margin*hold_uncertainty}")
            x.append(f"set_data_check -from [get_pins {rxlane(i)}/io_resetb] -to [get_pins {rxlane(j)}/io_resetb] -clock [get_clocks auto_clock_in_clock] -setup {margin*setup_uncertainty}")
            x.append(f"set_data_check -from [get_pins {rxlane(i)}/io_resetb] -to [get_pins {rxlane(j)}/io_resetb] -clock [get_clocks auto_clock_in_clock] -hold {margin*hold_uncertainty}")

    x.append("set_interactive_constraint_modes {}")
    return True

def place_sio_blockages(x: HammerTool) -> bool:
    x.append('''
        create_route_blockage -rect {2002.32 3704.398 3747.601 3705.658 } -name q2_sio_blockage -layers {m4}
        create_route_blockage -rect {180.144 379.26 1925.424 380.52} -name q3_sio_blockage -layers {m4}
    ''')
    return True

"""
    Add route blockage for IO
"""
def route_blk_io(x: hammer_vlsi.HammerTool) -> bool:
    x.append('''
        # Q3 route blockage
        create_route_blockage -rect {180.144 379.26 1925.424 380.52}  -name q3_sio_blockage -layers {m4}
        # Q2 route blockage
        create_route_blockage -rect {2002.32 3704.398 3747.601 3705.658 }  -name q2_sio_blockage -layers {m4}
    ''')
    return True

def ucie_effort(x: HammerTool) -> bool:
    x.append('''
        set_db design_cong_effort high
        set_db place_global_cong_effort high
    ''')
    return True

def ucie_power(x: HammerTool) -> bool:
    x.append('''
        set_db add_stripes_via_using_exact_crossover_size false
        set_db add_stripes_split_vias false
        set_db init_power_nets {vddh_q1 vddh_q1_tx}
        set_db init_ground_nets {vss}
        connect_global_net vddh_q1 -type pg_pin -pin vdd -override
        connect_global_net vddh_q1 -type pg_pin -pin vcc -override
        connect_global_net vddh_q1 -type pg_pin -pin vcc_nom -override
        connect_global_net vddh_q1 -type pg_pin -pin vccdig_nom -override
        connect_global_net vddh_q1 -type pg_pin -pin vccdist_nom -override
        connect_global_net vddh_q1 -type pg_pin -pin vnnaon_nom -override
        connect_global_net vddh_q1 -type pg_pin -pin vddp -override
        connect_global_net vddh_q1 -type pg_pin -pin VDD -override
        connect_global_net vddh_q1 -type pg_pin -pin vdd -override
        connect_global_net vss -type pg_pin -pin vss -override
        connect_global_net vss -type pg_pin -pin vssx -override
        connect_global_net vss -type pg_pin -pin vssp -override
        connect_global_net vss -type pg_pin -pin vssb -override
        connect_global_net vss -type pg_pin -pin VSS -override
        foreach inst [get_db [get_db insts -if { .base_cell == *txdatatile_dll || .base_cell == *txclk_with_esd }] .name] {
            connect_global_net vddh_q1_tx -type pg_pin -pin vdd -sinst $inst -override
        }
        set_db add_stripes_detailed_log true
    ''')
    return True

def ucie_m2_staples(x: HammerTool) -> bool:
    x.append('''
        set_db add_stripes_use_fgc true
        set_db add_stripes_stacked_via_top_layer m2
        set_db add_stripes_stacked_via_bottom_layer m2
        set_db add_stripes_trim_antenna_back_to_shape {stripe}
        set_db add_stripes_spacing_from_block 2.7
        # Draw first set of m1 stripes
        add_stripes -layer m1 -nets { vss vddh_q1 } -block_ring_bottom_layer_limit m1 -block_ring_top_layer_limit m1 -pad_core_ring_bottom_layer_limit m1 -pad_core_ring_top_layer_limit m1 -direction horizontal -width 0.044 -start_offset 0.608 -spacing 0.586 -set_to_set_distance 1.26
        # Next draw m2 pg stripes directly over m1 stripes and place vias
        set pullback(m2) 0.080
        set v1_pitch 0.216
        # Offset if core area is not exact multiple of 0.108
        set core_os [convert_dbu_to_um [expr [convert_um_to_dbu [get_db designs .core_bbox.ll.x]] % [convert_um_to_dbu 0.108]]]
        foreach net { vss vddh_q1 } {
            set m2_net_bboxes [get_db [get_db [get_db nets $net] .special_wires -if {.layer.name == m1}] .rect]
            if { [llength $m2_net_bboxes] > 0 } {
                foreach m2_net_bbox $m2_net_bboxes {
                    create_shape -layer m2 -net $net -rect $m2_net_bbox -shape stripe
                    set llx [lindex $m2_net_bbox 0]
                    set lly [lindex $m2_net_bbox 1]
                    set urx [lindex $m2_net_bbox 2]
                    set ury [lindex $m2_net_bbox 3]
                    set x [expr $llx - $pullback(m2) + $v1_pitch - 0.028]
                    set x [expr [convert_um_to_dbu $x] / [convert_um_to_dbu $v1_pitch]]
                    set x [expr [expr $x * $v1_pitch] - $pullback(m2) + $v1_pitch + $v1_pitch - 0.028 + $core_os]
                    set y [expr $lly + 0.022]
                    while { $x <= [ expr [lindex $m2_net_bbox 2] - $v1_pitch] } {
                        create_via -location "{$x $y}" -net $net -via_def via1_60Sx44_68V_44H
                        set x [expr {$x + $v1_pitch}]
                    }
                }
            } else {}
        }
        select_routes -layer { m2 m3 } -nets { vss vddh_q1 } -shapes stripe
        update_power_vias -add_vias 1 -between_selected_wires 1 -skip_via_on_pin {}
        deselect_routes
        add_power_mesh_colors
        # Reset antenna trimming
        set_db add_stripes_trim_antenna_back_to_shape {none}
    ''')
    return True

# FOR TMA2 places blockage to prevent filler placement which results in DRC
# violations in corner of two SRAMs
def rockettile_placement_blockage(x: HammerTool) -> bool:
    x.append('''
        create_place_blockage -rects {208.872 107.73 311.904 108.36}
    ''')
    return True

def shuttletile_placement_blockage(x: HammerTool) -> bool:
    x.append('''
        create_place_blockage -rects {991.008 386.82 1094.04 387.45}
    ''')
    return True


# def example_place_tap_cells(x: HammerTool) -> bool:
#     if x.get_setting("vlsi.core.technology") == "asap7":
#         x.append('''
# # TODO
# # Place custom TCL here
# ''')
#     return True

# def example_add_fillers(x: HammerTool) -> bool:
#     if x.get_setting("vlsi.core.technology") == "asap7":
#         x.append('''
# # TODO
# # Place custom TCL here
# ''')
#     return True

# def example_tool_settings(x: HammerTool) -> bool:
#     if x.get_setting("vlsi.core.technology") == "asap7":
#         x.append('''
# # TODO
# # Place custom TCL here
# set_db route_design_bottom_routing_layer 2
# set_db route_design_top_routing_layer 7
# ''')
#     return True



def time_par_steps(module_step_dict):
    top_steps = ['init_design', 'floorplan_design', 'place_bumps', 'place_tap_cells', 'power_straps', 'place_pins', 'place_opt_design', 'clock_tree', 'add_fillers', 'route_opt_design', 'write_regs', 'write_design', 'assemble_design']
    hierachial_steps = ['init_design', 'floorplan_design', 'place_bumps', 'place_tap_cells', 'power_straps', 'place_pins', 'place_opt_design', 'clock_tree', 'add_fillers', 'route_opt_design', 'write_regs', 'write_design', 'write_ilm']
    for key in module_step_dict.keys():
        steps = top_steps if key == "Intel4x4ChipTop" else hierachial_steps

        time_hooks = []
        for step in steps[:1]:
            time_hooks.append(HammerTool.make_pre_insertion_hook(step, get_runtime_start))
            time_hooks.append(HammerTool.make_post_insertion_hook(step, report_runtime))

        module_step_dict[key].extend(time_hooks)

    return module_step_dict




class KodiakDriver(CLIDriver):


    def get_extra_hierarchical_synthesis_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        # driver.load_synthesis_tool(get_or_else(self.syn_rundir, ""))
        # print(dir(driver.syn_tool.steps[0]))
        # print(driver.syn_tool.steps[0].name)

        # Example usage:
        # unique_start_time_hook("syn_map")


        # print(f"\n\nsyn_map_start_time write_db - {syn_map_start_time.write_db}\n\n")

        extra_hooks = dict({
            "ScratchpadBank": [
                # HammerTool.make_pre_insertion_hook("syn_generic", unique_start_time_hook("syn_generic")),
                # HammerTool.make_pre_insertion_hook("syn_map",     unique_start_time_hook("syn_map")),
                # HammerTool.make_post_insertion_hook("syn_generic", unique_stop_time_hook("syn_generic")),
                # HammerTool.make_post_insertion_hook("syn_map",     unique_stop_time_hook("syn_map")),
            ],
            "RocketTile": [
                HammerTool.make_pre_insertion_hook("init_environment", get_runtime_start),
            ],
            "ShuttleTile": [

            ],
            "ShuttleTile_4": [

            ],
            "InclusiveCacheBankScheduler": [

            ],
            "UciephyTestTL": [
                HammerTool.make_pre_insertion_hook("syn_generic", dont_touch_phy_tiles),
                HammerTool.make_pre_insertion_hook("syn_generic", dont_touch_top_level_signals_syn),
                HammerTool.make_pre_insertion_hook("syn_generic", ucie_reset_distribution)
            ],
            "Intel4x4ChipTop": [
                #HammerTool.make_post_insertion_hook("syn_map", syn_opt_top)
#                HammerTool.make_post_insertion_hook("init_environment", dont_touch_ddr)
                #HammerTool.make_post_insertion_hook("init_environment", disable_bound_opt)

            ]
        })

        return extra_hooks


    def get_extra_hierarchical_par_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        # driver.load_par_tool(get_or_else(self.par_rundir, ""))
        # print([x.name for x in driver.par_tool.steps])
        hooks = dict({
            ## This is required for any hier block which has SRAM macros
            "ScratchpadBank": [
                HammerTool.make_post_insertion_hook("place_opt_design", force_tieoff)
            ],
            "RocketTile": [
                HammerTool.make_post_insertion_hook("place_opt_design", force_tieoff),
                HammerTool.make_post_insertion_hook("floorplan_design", rockettile_placement_blockage)
            ],
            "ShuttleTile": [
                HammerTool.make_post_insertion_hook("place_opt_design", force_tieoff),
                HammerTool.make_post_insertion_hook("intech22_add_fillers", stop_route_after_20_iterations),
                HammerTool.make_post_insertion_hook("floorplan_design", shuttletile_placement_blockage)
                #HammerTool.make_post_insertion_hook("init_design", change_par_clock_frequency)
            ],
            "ShuttleTile_4": [
                HammerTool.make_post_insertion_hook("place_opt_design", force_tieoff),
                #HammerTool.make_post_insertion_hook("init_design", change_par_clock_frequency)
            ],
            "InclusiveCacheBankScheduler": [
                HammerTool.make_post_insertion_hook("place_opt_design", force_tieoff),
                #HammerTool.make_post_insertion_hook("init_design", change_par_clock_frequency)
            ],
            "UciephyTestTL": [
                HammerTool.make_post_insertion_hook("place_pins", assign_ucie_io_pins),
                HammerTool.make_removal_hook("place_pins"),
                HammerTool.make_pre_insertion_hook("floorplan_design", ucie_effort),
                HammerTool.make_pre_insertion_hook("floorplan_design", ucie_dont_route),
                HammerTool.make_pre_insertion_hook("floorplan_design", dont_touch_top_level_signals_par),
                HammerTool.make_pre_insertion_hook("floorplan_design", write_ucie_power_spec),
                HammerTool.make_post_insertion_hook("floorplan_design", ucie_power),
                HammerTool.make_post_insertion_hook("floorplan_design", place_esd_plus_antenna_blockages),
                HammerTool.make_post_insertion_hook("floorplan_design", place_macro_blockages),
                HammerTool.make_post_insertion_hook("floorplan_design", add_ucieq1_def_local),
                HammerTool.make_pre_insertion_hook("intech22_m2_staples", ucie_m2_staples),
                HammerTool.make_removal_hook("intech22_m2_staples"),
                HammerTool.make_pre_insertion_hook("power_straps", ucie_block_power_straps),
                HammerTool.make_post_insertion_hook("power_straps", add_ucie_shielding_vias),
                HammerTool.make_removal_hook("power_straps"),
                # HammerTool.make_post_insertion_hook("floorplan_design", add_ucieq1_macro_local),
                HammerTool.make_post_insertion_hook("place_opt_design", force_tieoff),
                HammerTool.make_pre_insertion_hook("route_opt_design", convert_ucie_sb_rx_to_regular_nets),
                HammerTool.make_post_insertion_hook("route_opt_design", add_back_ucie_sb_rx_special_net_geometry),
                HammerTool.make_post_insertion_hook("write_design", write_ucie_netlist_with_pg_pins),
                HammerTool.make_post_insertion_hook("write_ilm", write_ucie_lef_with_gm0_top_layer)
            ],
            "Intel4x4ChipTop": [
                # HammerTool.make_pre_insertion_hook("route_opt_design", rtmltop_bump_routes),
                HammerTool.make_post_insertion_hook("floorplan_design", global_power),
                #HammerTool.make_post_insertion_hook("floorplan_design", add_ucieq1_macro_absolute),
                HammerTool.make_post_insertion_hook("floorplan_design", route_blk_io),
                #HammerTool.make_post_insertion_hook("floorplan_design", place_sio_blockages),
                #HammerTool.make_pre_insertion_hook("floorplan_design", io_placement),
                #HammerTool.make_post_insertion_hook("place_bumps", fc_route),
                HammerTool.make_removal_hook("place_pins"),
                HammerTool.make_pre_insertion_hook("place_bumps", add_gmb_def),
                HammerTool.make_pre_insertion_hook("place_bumps", set_dont_route),
                #HammerTool.make_pre_insertion_hook("place_bumps", add_ucieq1_def),
                HammerTool.make_pre_insertion_hook("power_straps", ucie_top_power_straps),
                HammerTool.make_pre_insertion_hook("power_straps", pll_power),

                HammerTool.make_post_insertion_hook("intech22_add_fillers", stop_route_after_20_iterations),

                HammerTool.make_post_insertion_hook("route_opt_design", add_gv0_via),
                HammerTool.make_post_insertion_hook("route_opt_design", add_fillers)
            ]
        })

        # hooks = time_par_steps(hooks)
        return hooks

#if __name__ == '__main__':
#    KodiakDriver().main()


class SledgeHammerKodiak:
    def __init__(self):
        # minimal flow configuration variables
        self.design = os.getenv('design', 'kodiak')
        self.pdk = os.getenv('pdk', 'intech22')
        self.tools = os.getenv('tools', 'cm')
        self.env = os.getenv('env', 'bwrc')
        self.extra = os.getenv('extra', '')  # extra configs
        self.args = os.getenv('args', '')  # command-line args (including step flow control)
        self.top = os.getenv('top', 'Intel4x4ChipTop')  # top module name
        
        # Directory structure
        self.vlsi_dir = os.path.abspath('../e2e/')
        self.specs_abs = os.path.abspath('../../specs')
        self.tech_dir = os.path.abspath('../tech')
        self.e2e_dir = os.getenv('e2e_dir', self.vlsi_dir)
        self.specs_dir = os.getenv('specs_dir', self.specs_abs) #Point to specs directory for intel2x2 yml files
        self.OBJ_DIR = os.getenv('OBJ_DIR', f"{self.e2e_dir}/build-{self.pdk}-{self.tools}/{self.design}")
        
        # non-overlapping default configs
        self.ENV_YML = os.getenv('ENV_YML', f"{self.specs_dir}/{self.env}-env.yml") #bwrc-env.yml
        self.TECH_CONF = os.getenv('TECH_CONF', f"{self.specs_dir}/{self.env}-tech.yml") #bwrc-tech.yml
        self.TOOLS_CONF = os.getenv('TOOLS_CONF', f"{self.e2e_dir}/configs-tool/{self.tools}.yml") #Can keep the same for genus/innovus

        # design-specific overrides of default configs
        self.DESIGN_CONF = os.getenv('DESIGN_CONF', f"{self.specs_dir}/{self.design}-design.yml") #kodiak-design.yml
        #self.DESIGN_PDK_CONF = os.getenv('DESIGN_PDK_CONF', f"{self.specs_dir}/rockettile-design.yml") #Point to rockettile-design.yml, which contains same info as syn.yml (intel2x2)
        
        # synthesis and par configurations
        #self.SYN_CONF = os.getenv('SYN_CONF', f"{self.specs_dir}/rockettile-design.yml") #Point to rockettile-design.yml, which contains same info as syn.yml (intel2x2)
        #self.PAR_CONF = os.getenv('PAR_CONF', f"{self.e2e_dir}/configs-design/{self.design}/par.yml")
        
        # This should be your target, build is passed in
        
        #self.makecmdgoals = os.getenv('MAKECMDGOALS', "build")
        
        ## simulation and power configurations
        #self.SIM_CONF = os.getenv('SIM_CONF',
        #    f"{self.e2e_dir}/configs-design/{self.design}/sim-rtl.yml" if '-rtl' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/sim-syn.yml" if '-syn' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/sim-par.yml" if '-par' in self.makecmdgoals else ''
        #)
        #self.POWER_CONF = os.getenv('POWER_CONF',
        #    f"{self.e2e_dir}/configs-design/{self.design}/power-rtl-{self.pdk}.yml" if 'power-rtl' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/power-syn-{self.pdk}.yml" if 'power-syn' in self.makecmdgoals else
        #    f"{self.e2e_dir}/configs-design/{self.design}/power-par-{self.pdk}.yml" if 'power-par' in self.makecmdgoals else ''
        #)
        
        # create project configuration
        '''
        self.PROJ_YMLS = [
            self.PDK_CONF, 
            #self.TOOLS_CONF, 
            self.DESIGN_CONF, 
            #self.DESIGN_PDK_CONF,
            #self.SYN_CONF, 
            #self.SIM_CONF, 
            #self.POWER_CONF, 
            self.extra
        ]
        '''
        self.SOURCES = list(Path(f"{self.specs_dir}/constr").rglob(f"{self.design}*.yml"))
        self.INPUT_CONFS = f'-p {self.TECH_CONF} ' + ' '.join([f"-p {conf}" for conf in self.SOURCES if conf])
        self.HAMMER_EXTRA_ARGS = ' '.join([f"-p {conf}" for conf in self.extra]) + f" {self.args}"
        self.HAMMER_D_MK = os.getenv('HAMMER_D_MK', f"{self.OBJ_DIR}/hammer.d")
        self.SRAM_GENERATOR_CONF = (f"{self.OBJ_DIR}/sram_generator-input.yml") #Point to sram_generator-input.yml
        self.SRAM_CONF = (f"{self.OBJ_DIR}/sram_generator-output.json") #Point to sram_generator-output.yml

        # Comment out if you do not want to update IP
        subprocess.run(f"source {os.path.abspath('../../update_ip.sh')}", shell=True, check=True)
        

        # Set up system arguments
        
        #airflow_command = sys.argv[1]
        #sys.argv = []
        #for arg in [airflow_command, self.makecmdgoals, '--obj_dir', self.OBJ_DIR, '-e', self.ENV_YML]:
        #    sys.argv.append(arg)
        #for arg in self.HAMMER_EXTRA_ARGS.split():
        #    sys.argv.append(arg)

    def build(self):
        print("Executing build")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        #print(f"{INPUT_CONF} " for INPUT_CONF in self.INPUT_CONFS)
        #print(f"{EXTAR_ARG}") for EXTAR_ARG in self.HAMMER_EXTRA_ARGS
        #print(f"PDK_CONF: {self.PDK_CONF}")
        #print(f"TOOLS_CONF: {self.TOOLS_CONF}")
        #print(f"DESIGN_CONF: {self.DESIGN_CONF}")
        #print(f"DESIGN_PDK_CONF: {self.DESIGN_PDK_CONF}")
        
        #SRAM_GENERATOR_CONF = (f"{self.OBJ_DIR}/sram_generator-input.yml") #Point to sram_generator-input.yml
        
        sys.argv = [
            'hammer-vlsi',
            'build',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.SRAM_CONF
        ]
        
        sys.argv.extend(self.INPUT_CONFS.split())
        #sys.argv.append(f"-p {SRAM_GENERATOR_CONF}")

        #if self.extra:
        #    sys.argv.extend(['-p', self.extra])
        
        #if self.args:
        #    sys.argv.extend(self.args.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    # Copy over hammer.d hammer-vlsi commands
    # Create task groups for sram_generator, syn, syn-to-par, & par targets
    # Replicate these task groups for all 7 targets - This needs to be automated to replace hammer.d
    # Future step would be to take the dependency_graph generated and use that to determine the dependency graph wihtin SledgeHammer
    # Then map the dependencies to a task group for each design @ syn
    #   Intel4x4ChipTop: start >> build >> TaskGroup[UceiphyTestTL, sram_generator >> syn] >> syn-to-par >> par >> [hier-par-to-syn, exit]
    #   UciephyTestTL: start >> build >> TaskGroup[RocketTile, sram_generator >> syn] >> syn-to-par >> par >> [par-to-syn, exit]
    #   RocketTile: start >> build >> TaskGroup[ShuttleTile, sram_generator >> syn] >> syn-to-par >> par >> [par-to-syn, exit]
    #   ShuttleTile: start >> build >> TaskGroup[InclusiveCacheBankScheduler, sram_generator >> syn] >> syn-to-par >> par >> [par-to-syn, exit]
    #   InclusiveCacheBankScheduler: start >> build >> TaskGroup[ScratchpadBank_1, sram_generator >> syn] >> syn-to-par >> par >> [par-to-syn, exit]
    #   ScratchpadBank_1: start >> build >> TaskGroup[ScratchpadBank, sram_generator >> syn] >> syn-to-par >> par >> [par-to-syn, exit]
    #   ScratchpadBank: start >> build >> sram_generator >> syn >> syn-to-par >> par >> exit
    #
    # Logic needed for TaskGroup to determine whether hierarchical module needs to be ran
    #   If par-to-syn output is not present, run par-to-syn or rerun lower stage
    #   Can niavely just run everything w/o logic since I need to run from scratch anyways, and implement logic later
    #
    # Can probably skip sram_generator for submodules, and only do it for the top level
    # Should be possible to jump directly to a submodule from start


    #-e /bwrcq/C/andre_green/kodiak-cy/vlsi/specs/bwrc-env.yml 
    #-p /bwrcq/C/andre_green/kodiak-cy/vlsi/build/chipyard.harness.TestHarness.KodiakChipConfig-Intel4x4ChipTop/syn-Intel4x4ChipTop-input.json 
    #$(HAMMER_EXTRA_ARGS) 
    #--obj_dir /bwrcq/C/andre_green/kodiak-cy/vlsi/build/chipyard.harness.TestHarness.KodiakChipConfig-Intel4x4ChipTop 
    #syn-Intel4x4ChipTop

    def syn(self, target=None, args=None):
        if (target == None):
            target = self.top
        
        print("Executing synthesis")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        #print(f"{INPUT_CONF} ") for INPUT_CONF in self.INPUT_CONFS
        #print(f"{EXTAR_ARG}") for EXTAR_ARG in self.HAMMER_EXTRA_ARGS
        
        # Add synthesis config
        #self.SYN_CONF = (f"{self.specs_dir}/rockettile-inputs.yml") #Point to rockettile-inputs.yml
        #self.SRAM_CONF = (f"{self.OBJ_DIR}/sram_generator-output.json") #Point to sram_generator-output.json
        #print(f"SRAM_CONF: {self.SRAM_CONF}")
        
        sys.argv = [
            'hammer-vlsi',
            f'syn-{target}',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', f"{self.OBJ_DIR}syn-{target}-input.json",
            '-p', self.SRAM_CONF
        ]
        
        if args:
            sys.argv.extend(args.split())

        #sys.argv.extend(self.HAMMER_EXTRA_ARGS.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def sram_generator(self):
        print("Executing sram_generator")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
        #print(f"{INPUT_CONF} " for INPUT_CONF in self.INPUT_CONFS)
        
        print(f"SRAM_GENERATOR_CONF: {self.SRAM_GENERATOR_CONF}")

        # Add synthesis config
        self.SRAM_CONF = (f"{self.OBJ_DIR}/sram_generator-output.json") #Point to sram_generator-output.json
        
        sys.argv = [
            'hammer-vlsi',
            'sram_generator',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', self.SRAM_GENERATOR_CONF
        ]
        
        sys.argv.extend(self.INPUT_CONFS.split())
        
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    #-e /bwrcq/C/andre_green/kodiak-cy/vlsi/specs/bwrc-env.yml 
    #-p /bwrcq/C/andre_green/kodiak-cy/vlsi/build/chipyard.harness.TestHarness.KodiakChipConfig-Intel4x4ChipTop/syn-Intel4x4ChipTop/syn-output-full.json 
    #$(HAMMER_EXTRA_ARGS) 
    #-o /bwrcq/C/andre_green/kodiak-cy/vlsi/build/chipyard.harness.TestHarness.KodiakChipConfig-Intel4x4ChipTop/par-Intel4x4ChipTop-input.json 
    #--obj_dir /bwrcq/C/andre_green/kodiak-cy/vlsi/build/chipyard.harness.TestHarness.KodiakChipConfig-Intel4x4ChipTop syn-to-par

    def syn_to_par(self, target=None, args=None):
        if target == None:
            target = self.top
        """
        Generate par-input.json from synthesis outputs if it doesn't exist
        """
        #par_input_json = f"{self.OBJ_DIR}/par-input.json"
        #par_input_json = f"{self.OBJ_DIR}/par-RocketTile-input.json"
        
        print("Executing syn-to-par")
        print(f"Using config files:")
        print(f"ENV_YML: {self.ENV_YML}")
    
        syn_output = f"{self.OBJ_DIR}/syn-{target}/syn-output-full.json"
        par_input = f"{self.OBJ_DIR}/par-{target}-input.json"

        sys.argv = [
            'hammer-vlsi',
            'syn-to-par',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', syn_output,
            '-o', par_input,
        ]
        
        sys.argv.extend(self.HAMMER_EXTRA_ARGS.split())
            
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()
        
        
        '''
        # Only generate if file doesn't exist
        if not os.path.exists(par_input_json):
            print("Generating par-input.json")
            par_config = {
                "vlsi.inputs.placement_constraints": [],
                "vlsi.inputs.gds_merge": True,
                "par.inputs": {
                    #"top_module": self.design,
                    "top_module": "RocketTile",
                    "input_files": [f"{self.OBJ_DIR}/syn-rundir/RocketTile.mapped.v"]
                }
            }
            
            # Write configuration to par-input.json
            with open(par_input_json, 'w') as f:
                json.dump(par_config, f, indent=2)
        '''        
        return par_input_json

    def par(self, target=None):
        """Execute PAR flow."""
        if (target == None):
            target = self.top
        
        par_input = f"{self.OBJ_DIR}/par-{target}-input.json"
        
        # Set up command line arguments
        sys.argv = [
            'hammer-vlsi',
            f'par-{target}',
            '--obj_dir', self.OBJ_DIR,
            '-e', self.ENV_YML,
            '-p', par_input
        ]
        
        
        print(f"Running command: {' '.join(sys.argv)}")
        CLIDriver().main()

    def clean(self):
        print("Executing clean")
        if os.path.exists(self.OBJ_DIR):
            subprocess.run(f"rm -rf {self.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)


@dag(
    dag_id='Kodiak',
    start_date=pendulum.datetime(2024, 1, 1, tz="America/Los_Angeles"),
    schedule=None,
    catchup=False,
    tags=["kodiak"],
    params={
        'clean': Param(
            default=False,
            type='boolean',
            title='Clean Build Directory',
            description='Clean the build directory before running'
        ),
        'build': Param(
            default=False,
            type='boolean',
            title='Build Design',
            description='Run the build step'
        ),
        'sram_generator': Param(
            default=False,
            type='boolean',
            title='SRAM Generator',
            description='Generate SRAM macros'
        ),
        'syn': Param(
            default=False,
            type='boolean',
            title='Synthesis',
            description='Run logic synthesis'
        ),
        'par': Param(
            default=False,
            type='boolean',
            title='Place and Route',
            description='Run place and route'
        )
    },
    render_template_as_native_obj=True
)
def create_hammer_dag_kodiak():
    
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def start(**context):
        """Start task"""
        if context['dag_run'].conf.get('clean', False):
            return "Intel4x4ChipTop.clean"
        elif (context['dag_run'].conf.get('build', False) or 
            context['dag_run'].conf.get('sram_generator', False) or
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return "Intel4x4ChipTop.build_decider"
        else:
            return "Intel4x4ChipTop.exit_"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def build_decider(**context):
        """Decide whether to run build"""
        if context['dag_run'].conf.get('build', True):
            return 'Intel4x4ChipTop.build'
        elif (context['dag_run'].conf.get('sram_generator', False) or
            context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return "Intel4x4ChipTop.sram_decider"
        return 'Intel4x4ChipTop.exit_'
    
    @task
    def build(**context):
        """Execute build task"""
        print("Starting build task")
        if context['dag_run'].conf.get('build', False):
            print("Build parameter is True, executing build")
            flow = SledgeHammerKodiak()
            flow.build()
        else:
            print("Build parameter is False, skipping")
            raise AirflowSkipException("Build task skipped")
    
    @task
    def clean(**context):
        """Clean the build directory"""
        print("Starting clean task")
        flow = SledgeHammerKodiak()
        if os.path.exists(flow.OBJ_DIR):
            subprocess.run(f"rm -rf {flow.OBJ_DIR} hammer-vlsi-*.log", shell=True, check=True)

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def sram_decider(**context):
        """Decide whether to run sram generator"""
        if context['dag_run'].conf.get('sram_generator', False):
            return 'Intel4x4ChipTop.sram_generator'
        elif (context['dag_run'].conf.get('syn', False) or
            context['dag_run'].conf.get('par', False)):
            return 'Intel4x4ChipTop.syn_decider'
        return 'Intel4x4ChipTop.exit_'
    
    @task
    def sram_generator(**context):
        """Execute sram generator task"""
        print("Starting sram task")
        if context['dag_run'].conf.get('sram_generator', False):
            print("SRAM parameter is True, executing sram_generator")
            flow = SledgeHammerKodiak()
            flow.sram_generator()
        else:
            print("SRAM parameter is False, skipping")
            raise AirflowSkipException("SRAM task skipped")

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('Intel4x4ChipTop', '-p syn-Intel4x4ChipTop-input.json')
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('Intel4x4ChipTop')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('Intel4x4ChipTop')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'UciephyTestTL.syn_decider_ucie'
            #return 'syn'
        elif (context['dag_run'].conf.get('par', False)):
            return "Intel4x4ChipTop.par_decider"
        else:
            return "Intel4x4ChipTop.exit_"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'Intel4x4ChipTop.Intel4x4ChipTop_par.syn_to_par'
        return 'Intel4x4ChipTop.exit_'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_():
        """Exit task"""
        print("Exiting")
        sys.exit(0)
    ###
    # UciephyTestTL
    ###
    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_ucie(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('UciephyTestTL', self.INPUT_CONFS)
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par_ucie(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('UciephyTestTL')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par_ucie(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('UciephyTestTL')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider_ucie(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'RocketTile.syn_decider_rocket'
        elif (context['dag_run'].conf.get('par', False)):
            return "UciephyTestTL.par_decider_ucie"
        else:
            return "UciephyTestTL.exit_ucie"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider_ucie(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'UciephyTestTL.UciephyTestTL_par.syn_to_par_ucie'
        return 'UciephyTestTL.exit_ucie'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_ucie():
        """Exit task"""
        print("Exiting")
        sys.exit(0)
    ###
    # RocketTile
    ###
    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_rocket(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('RocketTile', self.INPUT_CONFS)
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par_rocket(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('RocketTile')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par_rocket(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('RocketTile')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider_rocket(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'InclusiveCacheBankScheduler.syn_decider_cache'
        elif (context['dag_run'].conf.get('par', False)):
            return "RocketTile.par_decider_rocket"
        else:
            return "RocketTile.exit_rocket"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider_rocket(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'RocketTile.RocketTile_par.syn_to_par_rocket'
        return 'RocketTile.exit_rocket'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_rocket():
        """Exit task"""
        print("Exiting")
        sys.exit(0) 
    ###
    # InclusiveCacheBankScheduler
    ###
    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_cache(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('InclusiveCacheBankScheduler', self.INPUT_CONFS)
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par_cache(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('InclusiveCacheBankScheduler')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par_cache(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('InclusiveCacheBankScheduler')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider_cache(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'ShuttleTile.syn_decider_shuttle'
        elif (context['dag_run'].conf.get('par', False)):
            return "InclusiveCacheBankScheduler.par_decider_cache"
        else:
            return "InclusiveCacheBankScheduler.exit_cache"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider_cache(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'InclusiveCacheBankScheduler.InclusiveCacheBankScheduler_par.syn_to_par_cache'
        return "InclusiveCacheBankScheduler.exit_cache"

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_cache():
        """Exit task"""
        print("Exiting")
        sys.exit(0)
    ###
    # ShuttleTile
    ###
    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_shuttle(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('ShuttleTile', self.INPUT_CONFS)
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par_shuttle(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('ShuttleTile')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par_shuttle(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('ShuttleTile')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider_shuttle(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'ScratchpadBank_1.syn_decider_scratch1'
        elif (context['dag_run'].conf.get('par', False)):
            return "ShuttleTile.par_decider_shuttle"
        else:
            return "ShuttleTile.exit_shuttle"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider_shuttle(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'ShuttleTile.ShuttleTile.syn_to_par_shuttle'
        return 'ShuttleTile.exit_shuttle'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_shuttle():
        """Exit task"""
        print("Exiting")
        sys.exit(0)
    ###
    # ScratchpadBank_1
    ###
    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_scratch1(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('ScratchpadBank_1', self.INPUT_CONFS)
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par_scratch1(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('ScratchpadBank_1')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par_scratch1(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('ScratchpadBank_1')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider_scratch1(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'ScratchpadBank.syn_decider_scratch'
        elif (context['dag_run'].conf.get('par', False)):
            return "ScratchpadBank_1.par_decider_scratch1"
        else:
            return "ScratchpadBank_1.exit_scratch1"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider_scratch1(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'ScratchpadBank_1.ScratchpadBank_1_par.syn_to_par_scratch1'
        return 'ScratchpadBank_1.exit_scratch1'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_scratch1():
        """Exit task"""
        print("Exiting")
        sys.exit(0)
    ###
    # ScratchpadBank
    ###
    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def syn_scratch(**context):
        """Execute synthesis task"""
        print("Starting syn task")
        if (context['dag_run'].conf.get('sram_generator', False) or
         context['dag_run'].conf.get('syn', False)):
            print("Synthesis parameter is True, executing syn")
            flow = SledgeHammerKodiak()
            flow.syn('ScratchpadBank', self.INPUT_CONFS)
        else:
            print("Synthesis parameter is False, skipping")
            raise AirflowSkipException("Synthesis task skipped")

    @task
    def syn_to_par_scratch(**context):
        """Execute PAR task"""
        print("Starting syn-to-par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing syn-to-par")
            flow = SledgeHammerKodiak()
            flow.syn_to_par('ScratchpadBank')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")
    
    @task
    def par_scratch(**context):
        """Execute PAR task"""
        print("Starting par task")
        if context['dag_run'].conf.get('par', False):
            print("PAR parameter is True, executing par")
            flow = SledgeHammerKodiak()
            flow.par('ScratchpadBank')
        else:
            print("PAR parameter is False, skipping")
            raise AirflowSkipException("PAR task skipped")

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.ALL_SUCCESS)
    def syn_decider_scratch(**context):
        """Decide whether to run synthesis"""
        if context['dag_run'].conf.get('syn', False):
            return 'ScratchpadBank.syn_scratch'
        elif (context['dag_run'].conf.get('par', False)):
            return "ScratchpadBank.par_decider_scratch"
        else:
            return "ScratchpadBank.exit_scratch"

    #@task.branch(trigger_rule=TriggerRule.NONE_FAILED)
    @task.branch(trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    def par_decider_scratch(**context):
        """Decide whether to run par"""
        if context['dag_run'].conf.get('par', False):
            return 'ScratchpadBank.ScratchpadBank_par.syn_to_par_scratch'
        return 'ScratchpadBank.exit_scratch'

    @task(trigger_rule=TriggerRule.NONE_FAILED)
    def exit_scratch():
        """Exit task"""
        print("Exiting")
        sys.exit(0)   
    ###

    ### Intel4x4ChipTop
    with TaskGroup(group_id='Intel4x4ChipTop') as Intel4x4ChipTop:
        start = start()
        clean = clean()
        build_decide = build_decider()
        build = build()
        sram_decide = sram_decider()
        sram_generator = sram_generator()
        syn_decide = syn_decider()
        syn = syn()
        par_decide = par_decider()
    
        with TaskGroup(group_id='Intel4x4ChipTop_par') as Intel4x4ChipTop_par:
            syn_to_par = syn_to_par()
            par = par()

        _exit_ = exit_()

        #Intel4x4ChipTop 
        start >> [clean, build_decide, _exit_]
        clean >> _exit_
        build_decide >> [build, sram_decide, _exit_]
        build >> sram_decide
        sram_decide >> [sram_generator, syn_decide, _exit_]
        sram_generator >> syn_decide
        syn_decide >> [syn, par_decide, _exit_]
        syn >> par_decide
        par_decide >> syn_to_par
        syn_to_par >> par
        par >> _exit_

    ### UciephyTestTL
    with TaskGroup(group_id='UciephyTestTL') as UciephyTestTL:
        syn_decide_ucie = syn_decider_ucie()
        syn_ucie = syn_ucie()
        par_decide_ucie = par_decider_ucie()
    
        with TaskGroup(group_id='UciephyTestTL_par') as UciephyTestTL_par:
            syn_to_par_ucie = syn_to_par_ucie()
            par_ucie = par_ucie()

        exit_ucie = exit_ucie()

    syn_decide_ucie >> [syn_ucie, par_decide_ucie, exit_ucie]
    syn_ucie >> par_decide_ucie
    par_decide_ucie >> syn_to_par_ucie
    syn_to_par_ucie >> par_ucie
    par_ucie >> exit_ucie

    ### RocketTile
    with TaskGroup(group_id='RocketTile') as RocketTile:
        syn_decide_rocket = syn_decider_rocket()
        syn_rocket = syn_rocket()
        par_decide_rocket = par_decider_rocket()
        
        with TaskGroup(group_id='RocketTile_par') as RocketTile_par:
            syn_to_par_rocket = syn_to_par_rocket()
            par_rocket = par_rocket()

        exit_rocket = exit_rocket()

    syn_decide_rocket >> [syn_rocket, par_decide_rocket, exit_rocket]
    syn_rocket >> par_decide_rocket
    par_decide_rocket >> syn_to_par_rocket
    syn_to_par_rocket >> par_rocket
    par_rocket >> exit_rocket
  
    ### InclusiveCacheBankScheduler
    with TaskGroup(group_id='InclusiveCacheBankScheduler') as InclusiveCacheBankScheduler:
        syn_decide_cache = syn_decider_cache()
        syn_cache = syn_cache()
        par_decide_cache = par_decider_cache()
    
        with TaskGroup(group_id='InclusiveCacheBankScheduler_par') as InclusiveCacheBankScheduler_par:
            syn_to_par_cache = syn_to_par_cache()
            par_cache = par_cache()

        exit_cache = exit_cache()

    syn_decide_cache >> [syn_cache, par_decide_cache, exit_cache]
    syn_cache >> par_decide_cache
    par_decide_cache >> syn_to_par_cache
    syn_to_par_cache >> par_cache
    par_cache >> exit_cache

    ### ShuttleTile
    with TaskGroup(group_id='ShuttleTile') as ShuttleTile:
        syn_decide_shuttle = syn_decider_shuttle()
        syn_shuttle = syn_shuttle()
        par_decide_shuttle = par_decider_shuttle()
    
        with TaskGroup(group_id='ShuttleTile_par') as ShuttleTile_par:
            syn_to_par_shuttle = syn_to_par_shuttle()
            par_shuttle = par_shuttle()

        exit_shuttle = exit_shuttle()

    syn_decide_shuttle >> [syn_shuttle, par_decide_shuttle, exit_shuttle]
    syn_shuttle >> par_decide_shuttle
    par_decide_shuttle >> syn_to_par_shuttle
    syn_to_par_shuttle >> par_shuttle
    par_shuttle >> exit_shuttle

    ### ScratchpadBank_1
    with TaskGroup(group_id='ScratchpadBank_1') as ScratchpadBank_1:
        syn_decide_scratch1 = syn_decider_scratch1()
        syn_scratch1 = syn_scratch1()
        par_decide_scratch1 = par_decider_scratch1()
    
        with TaskGroup(group_id='ScratchpadBank_1_par') as ScratchpadBank_1_par:
            syn_to_par_scratch1 = syn_to_par_scratch1()
            par_scratch1 = par_scratch1()

        exit_scratch1 = exit_scratch1()

    syn_decide_scratch1 >> [syn_scratch1, par_decide_scratch1, exit_scratch1]
    syn_scratch1 >> par_decide_scratch1
    par_decide_scratch1 >> syn_to_par_scratch1
    syn_to_par_scratch1 >> par_scratch1
    par_scratch1 >> exit_scratch1
    
    ### ScratchpadBank
    with TaskGroup(group_id='ScratchpadBank') as ScratchpadBank:
        syn_decide_scratch = syn_decider_scratch()
        syn_scratch = syn_scratch()
        par_decide_scratch = par_decider_scratch()
    
        with TaskGroup(group_id='ScratchpadBank_par') as ScratchpadBank_par:
            syn_to_par_scratch = syn_to_par_scratch()
            par_scratch = par_scratch()

        exit_scratch = exit_scratch()
    
    syn_decide_scratch >> [syn_scratch, par_decide_scratch, exit_scratch]
    syn_scratch >> par_decide_scratch
    par_decide_scratch >> syn_to_par_scratch
    syn_to_par_scratch >> par_scratch
    par_scratch >> exit_scratch
    

    ### Hierarchical Dependency Management
    syn_decide >> UciephyTestTL
    exit_ucie >> syn
    syn_decide_ucie >> RocketTile
    exit_rocket >> syn_ucie
    syn_decide_rocket >> ShuttleTile
    exit_shuttle >> syn_rocket
    syn_decide_shuttle >> InclusiveCacheBankScheduler
    exit_cache >> syn_shuttle
    syn_decide_cache >> ScratchpadBank
    exit_scratch >> syn_cache
    syn_decide_scratch >> ScratchpadBank_1
    exit_scratch1 >> syn_scratch
    

    return {
        #Intel4x4ChipTop
        'Intel4x4ChipTop.clean': clean,
        'Intel4x4ChipTop.build_decide_': build_decide,
        'Intel4x4ChipTop.Intel4x4ChipTop.build': build,
        'Intel4x4ChipTop.syn_decide': syn_decide,
        'Intel4x4ChipTop.sram_decide': sram_decide,
        'Intel4x4ChipTop.sram_generator': sram_generator,
        'Intel4x4ChipTop.syn': syn,
        'Intel4x4ChipTop.par_decide': par_decide,
        'Intel4x4ChipTop.Intel4x4ChipTop_par.syn_to_par': syn_to_par,
        'Intel4x4ChipTop.Intel4x4ChipTop_par.par': par,
        #UCIEphyTestTL
        'UciephyTestTL.syn_decide_ucie': syn_decide_ucie,
        'UciephyTestTL.syn_ucie': syn_ucie,
        'UciephyTestTL.par_decide_ucie': par_decide_ucie,
        'UciephyTestTL.UciephyTestTL_par.syn_to_par_ucie': syn_to_par_ucie,
        'UciephyTestTL.UciephyTestTL_par.par_ucie': par_ucie,
        #RocketTile
        'RocketTile.syn_decide_rocket': syn_decide_rocket,
        'RocketTile.syn_rocket': syn_rocket,
        'RocketTile.par_decide_rocket': par_decide_rocket,
        'RocketTile.RocketTile_par.syn_to_par_rocket': syn_to_par_rocket,
        'RocketTile.RocketTile_par.par_rocket': par_rocket,
        #InclusiveCacheBankScheduler
        'InclusiveCacheBankScheduler.syn_decide_cache': syn_decide_cache,
        'InclusiveCacheBankScheduler.syn_cache': syn_cache,
        'InclusiveCacheBankScheduler.par_decide_cache': par_decide_cache,
        'InclusiveCacheBankScheduler.InclusiveCacheBankScheduler_par.syn_to_par_cache': syn_to_par_cache,
        'InclusiveCacheBankScheduler.InclusiveCacheBankScheduler_par.par_cache': par_cache,
        #ShuttleTile
        'ShuttleTile.syn_decide_shuttle': syn_decide_shuttle,
        'ShuttleTile.syn_shuttle': syn_shuttle,
        'ShuttleTile.par_decide_shuttle': par_decide_shuttle,
        'ShuttleTile.ShuttleTile_par.syn_to_par_shuttle': syn_to_par_shuttle,
        'ShuttleTile.ShuttleTile_par.par_shuttle': par_shuttle,
        #ScratchpadBank_1
        'ScracthpadBank_1.syn_decide_scratch1': syn_decide_scratch1,
        'ScracthpadBank_1.syn_scratch1': syn_scratch1,
        'ScracthpadBank_1.par_decide_scratch1': par_decide_scratch1,
        'ScracthpadBank_1.ScratchpadBank_1_par.syn_to_par_scratch1': syn_to_par_scratch1,
        'ScracthpadBank_1.ScratchpadBank_1_par.par_scratch1': par_scratch1,
        #ScratchpadBank
        'ScratchpadBank.syn_decide_scratch': syn_decide_scratch,
        'ScratchpadBank.syn_scratch': syn_scratch,
        'ScratchpadBank.par_decide_scratch': par_decide_scratch,
        'ScratchpadBank.ScratchpadBank_par.syn_to_par_scratch': syn_to_par_scratch,
        'ScratchpadBank.ScratchpadBank_par.par_scratch': par_scratch
    }

# Create the DAG
hammer_dag_kodiak = create_hammer_dag_kodiak()

#def main():
#    CLIDriver().main()

if __name__ == '__main__':
    KodiakDriver().main()