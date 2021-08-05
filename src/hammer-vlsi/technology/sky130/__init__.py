#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  SKY130 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os, shutil
from pathlib import Path 
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

import hammer_tech
from hammer_tech import HammerTechnology
from hammer_vlsi import HammerTool, HammerPlaceAndRouteTool, TCLTool, HammerToolHookAction

class SKY130Tech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """
    def post_install_script(self) -> None:
        self.library_name = 'sky130_fd_sc_hd'
        self.use_openram = (self.get_setting("technology.sky130.openram_lib") is not "")
        self.setup_sram_cdl()
        self.setup_cdl()
        self.setup_verilog()
        self.setup_techlef()
        self.setup_lvs_deck()
        print('Loaded Sky130 Tech')

    # Helper functions
    # TODO: add to HammerTechnology
    def expand_tech_cache_path(self, path) -> str:
        """ Replace occurrences of the cache directory's basename with
            the full path to the cache dir."""
        cache_dir_basename = os.path.basename(self.cache_dir)
        return path.replace(cache_dir_basename, self.cache_dir)

    def ensure_dirs_exist(self, path) -> None:
        dir_name = os.path.dirname(path)
        if not os.path.exists(dir_name):
            self.logger.info('Creating directory: {}'.format(dir_name))
            os.makedirs(dir_name)

    # Tech setup steps
    def setup_cdl(self) -> None:
        """ Copy and hack the cdl, replacing pfet_01v8_hvt/nfet_01v8 with phighvt/nshort """
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        cdl_old_path = setting_dir / 'libs.ref' / self.library_name / 'cdl' / f'{self.library_name}.cdl'
        if not cdl_old_path.exists():
            raise FileNotFoundError(f"CDL not found: {cdl_old_path}")

        cache_tech_dir_path = Path(self.cache_dir) 
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        cdl_new_path = cache_tech_dir_path / f'{self.library_name}.cdl' 

        f_old = open(cdl_old_path,'r')
        f_new = open(cdl_new_path,'w')
        for line in f_old:
            line = line.replace('pfet_01v8_hvt','phighvt')
            line = line.replace('nfet_01v8',    'nshort')
            f_new.write(line)
        f_old.close()
        f_new.close()
    
    def setup_verilog(self) -> None:
        """ Copy and hack the verilog """
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        verilog_old_path = setting_dir / 'libs.ref' / self.library_name / 'verilog' / f'{self.library_name}.v'
        if not verilog_old_path.exists():
            raise FileNotFoundError(f"Verilog not found: {verilog_old_path}")

        cache_tech_dir_path = Path(self.cache_dir) 
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        verilog_new_path = cache_tech_dir_path / f'{self.library_name}.v' 

        f_old = open(verilog_old_path,'r')
        f_new = open(verilog_new_path,'w')
        for line in f_old:
            line = line.replace('wire 1','// wire 1')
            f_new.write(line)
        f_old.close()
        f_new.close()

    def setup_techlef(self) -> None:
        """ Copy and hack the tech-lef, adding this very important `licon` section """
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        tlef_old_path = setting_dir / 'libs.ref' / self.library_name / 'techlef' / f'{self.library_name}.tlef'
        if not tlef_old_path.exists():
            raise FileNotFoundError(f"Tech-LEF not found: {tlef_old_path}")

        cache_tech_dir_path = Path(self.cache_dir) 
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        tlef_new_path = cache_tech_dir_path / f'{self.library_name}.tlef' 

        f_old = open(tlef_old_path,'r')
        f_new = open(tlef_new_path,'w')
        for line in f_old:
            f_new.write(line)
            if line.strip() == 'END pwell':
                f_new.write(_the_tlef_edit)
        f_old.close()
        f_new.close()

    def setup_lvs_deck(self) -> None:
        """Remove conflicting specification statements found in PDK LVS decks."""

        # if using OpenRAM SRAMs, LVS BOX these to ignore in LVS check
        # if self.use_openram:
        #     for name in SKY130Tech.openram_sram_names():
        #         LVS_DECK_INSERT_LINES += f"LVS BOX {name} \n"
        #         LVS_DECK_INSERT_LINES += f"LVS FILTER {name} OPEN \n"

        pattern = '.*({}).*\n'.format('|'.join(LVS_DECK_SCRUB_LINES))
        matcher = re.compile(pattern)

        source_paths = self.get_setting('technology.sky130.lvs_deck_sources')
        lvs_decks = list(self.config.lvs_decks)
        for i in range(len(lvs_decks)):
            deck = lvs_decks[i]
            try:
                source_path = source_paths[i]
            except IndexError:
                self.logger.error(
                    'No corresponding source for LVS deck {}'.format(deck))
            dest_path = self.expand_tech_cache_path(str(deck.path))
            self.ensure_dirs_exist(dest_path)
            with open(source_path, 'r') as sf:
                with open(dest_path, 'w') as df:
                    self.logger.info("Modifying LVS deck: {} -> {}".format
                        (source_path, dest_path))
                    df.write(matcher.sub("", sf.read()))  
                    df.write(LVS_DECK_INSERT_LINES)

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {"innovus": [
            HammerTool.make_post_insertion_hook("init_design",      sky130_innovus_settings),
            HammerTool.make_pre_insertion_hook("place_tap_cells",   sky130_add_endcaps),
            HammerTool.make_pre_insertion_hook("power_straps",      sky130_power_nets),
            HammerTool.make_post_insertion_hook("place_opt_design", sky130_add_tieoffs),
            HammerTool.make_pre_insertion_hook("write_design",     sky130_connect_nets),
            ]}
        return hooks.get(tool_name, [])

    ''' >>>>>>>> OpenRAM SRAM-specific functions '''
    @staticmethod
    def openram_sram_names() -> List[str]:
        """ Return a list of cell-names of the OpenRAM SRAMs (that we'll use). """
        return [
            "sky130_sram_1kbyte_1rw1r_32x256_8",
            "sky130_sram_1kbyte_1rw1r_8x1024_8",
            "sky130_sram_2kbyte_1rw1r_32x512_8"
        ]

    def setup_sram_cdl(self) -> None:
        if not self.use_openram: return
        for sram_name in self.openram_sram_names():
            old_path = Path(self.get_setting("technology.sky130.openram_lib")) / sram_name / f"{sram_name}.lvs.sp"
            new_path = self.expand_tech_cache_path(f'tech-sky130-cache/{sram_name}/{sram_name}.lvs.sp')
            self.ensure_dirs_exist(new_path)
            with open(old_path,'r') as f_old:
                with open(new_path,'w') as f_new:
                    for line in f_old:
                        line = line.replace('sky130_fd_pr__pfet_01v8','pshort')
                        line = line.replace('sky130_fd_pr__nfet_01v8','nshort')
                        f_new.write(line)
    ''' <<<<<<< END OpenRAM SRAM-specific functions '''

_the_tlef_edit = '''
LAYER licon
  TYPE CUT ;
END licon
'''

LVS_DECK_SCRUB_LINES = [
    "VIRTUAL CONNECT REPORT",
    "SOURCE PRIMARY",
    "SOURCE SYSTEM SPICE",
    "SOURCE PATH",
    "ERC",
    "LVS REPORT"
]

LVS_DECK_INSERT_LINES = '''
LVS FILTER D  OPEN  SOURCE
LVS FILTER D  OPEN  LAYOUT
'''

# various Innovus database settings
def sky130_innovus_settings(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    """Settings for every tool invocation"""
    ht.append(
        '''  

##########################################################
# Placement attributes  [get_db -category place]
##########################################################
#-------------------------------------------------------------------------------
set_db place_global_place_io_pins  true

set_db opt_honor_fences true
set_db place_detail_dpt_flow true
set_db place_detail_color_aware_legal true
set_db place_global_solver_effort high
set_db place_detail_check_cut_spacing true
set_db place_global_cong_effort high

##########################################################
# Optimization attributes  [get_db -category opt]
##########################################################
#-------------------------------------------------------------------------------

set_db opt_fix_fanout_load true
set_db opt_clock_gate_aware false
set_db opt_area_recovery true
set_db opt_post_route_area_reclaim setup_aware
set_db opt_fix_hold_verbose true
# set_db opt_fix_hold_lib_cells "BUFFD0BWP30P140HVT BUFFD1BWP30P140HVT BUFFD2BWP30P140HVT BUFFD3BWP30P140HVT BUFFD4BWP30P140HVT BUFFD6BWP30P140HVT BUFFD8BWP30P140HVT BUFFD12BWP30P140HVT BUFFD16BWP30P140HVT BUFFD20BWP30P140HVT BUFFD24BWP30P140HVT DEL025D1BWP30P140HVT"


##########################################################
# Clock attributes  [get_db -category cts]
##########################################################
#-------------------------------------------------------------------------------
#set_db cts_target_skew                .15
#set_db cts_target_max_transition_time .3
#set_db cts_update_io_latency false

# set_db cts_use_inverters true
# set_db cts_buffer_cells               "clkbuf clkdlybuf4s15 clkdlybuf4s18 clkdlybuf4s25 clkdlybuf4s50"
# set_db cts_inverter_cells             "clkinv clkinvlp"
# set_db cts_clock_gating_cells         "CKLHQD1BWP30P140HVT CKLHQD2BWP30P140HVT CKLHQD3BWP30P140HVT CKLHQD4BWP30P140HVT CKLHQD6BWP30P140HVT CKLHQD8BWP30P140HVT CKLHQD12BWP30P140HVT CKLHQD16BWP30P140HVT CKLHQD20BWP30P140HVT CKLHQD24BWP30P140HVT CKLNQD1BWP30P140HVT CKLNQD2BWP30P140HVT CKLNQD3BWP30P140HVT CKLNQD4BWP30P140HVT CKLNQD6BWP30P140HVT CKLNQD8BWP30P140HVT CKLNQD12BWP30P140HVT CKLNQD16BWP30P140HVT CKLNQD20BWP30P140HVT CKLNQD24BWP30P140HVT"


##########################################################
# Routing attributes  [get_db -category route]
##########################################################
#-------------------------------------------------------------------------------
set_db route_design_antenna_diode_insertion 1
set_db route_design_antenna_cell_name "sky130_fd_sc_hd__diode_2"
set_db route_design_bottom_routing_layer 2

set_db route_design_high_freq_search_repair true
set_db route_design_detail_post_route_spread_wire true
set_db route_design_with_si_driven true
set_db route_design_with_timing_driven true
set_db route_design_concurrent_minimize_via_count_effort high
set_db opt_consider_routing_congestion true
set_db route_design_detail_use_multi_cut_via_effort medium

set_db cts_target_skew 0.03
set_db cts_max_fanout 10
set_db opt_setup_target_slack 0.10
set_db opt_hold_target_slack 0.10
    '''
    )
    return True   



# TODO: move to Innovus plugin
def sky130_add_endcaps(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    ht.append(
        '''  
set_db add_endcaps_boundary_tap        true
set_db add_endcaps_left_edge sky130_fd_sc_hd__tap_1
set_db add_endcaps_right_edge sky130_fd_sc_hd__tap_1
add_endcaps
    '''
    )
    return True

# Pair VDD/VPWR and VSS/VGND nets
#   these commands are already added in Innovus.write_netlist,
#   but must also occur before power straps are placed
# TODO: move to Innovus plugin
def sky130_power_nets(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    ht.append(
        '''  
connect_global_net VDD -type net -net_base_name VPWR
connect_global_net VSS -type net -net_base_name VGND
    '''
    )
    return True

# TODO: add these two functions into Hammer Innovus plugin
def sky130_add_tieoffs(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    ht.append(
        '''  
set_db add_tieoffs_cells sky130_fd_sc_hd__conb_1
add_tieoffs 
    '''
    )
    return True

def sky130_connect_nets(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    ht.append(
        '''  
connect_global_net VDD -type pg_pin -pin_base_name VPWR -all
connect_global_net VDD -type pg_pin -pin_base_name VPB  -all
connect_global_net VSS -type pg_pin -pin_base_name VGND -all
connect_global_net VSS -type pg_pin -pin_base_name VNB  -all
    '''
    )
    return True

tech = SKY130Tech()

