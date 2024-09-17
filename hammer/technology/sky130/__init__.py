#  SKY130 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os, shutil
from pathlib import Path
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any
import importlib
import importlib.resources
import json

import hammer.tech
from hammer.tech import HammerTechnology
from hammer.vlsi import HammerTool, HammerPlaceAndRouteTool, TCLTool, HammerDRCTool, HammerLVSTool, \
    HammerToolHookAction, HierarchicalMode

import hammer.tech.specialcells as specialcells
from hammer.tech.specialcells import CellType, SpecialCell

class SKY130Tech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """
    def post_install_script(self) -> None:
        self.library_name = 'sky130_fd_sc_hd'
        # check whether variables were overriden to point to a valid path
        self.use_sram22 = os.path.exists(self.get_setting("technology.sky130.sram22_sky130_macros"))
        self.setup_cdl()
        self.setup_verilog()
        self.setup_techlef()
        # self.setup_io_lefs()
        self.logger.info('Loaded Sky130 Tech')


    def setup_cdl(self) -> None:
        ''' Copy and hack the cdl, replacing pfet_01v8_hvt/nfet_01v8 with
            respective names in LVS deck
        '''
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        source_path = setting_dir / 'libs.ref' / self.library_name / 'cdl' / f'{self.library_name}.cdl'
        if not source_path.exists():
            raise FileNotFoundError(f"CDL not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / f'{self.library_name}.cdl'

        # device names expected in LVS decks
        pmos = 'pfet_01v8_hvt'
        nmos = 'nfet_01v8'
        if (self.get_setting('vlsi.core.lvs_tool') == "hammer.lvs.calibre"):
            pmos = 'phighvt'
            nmos = 'nshort'
        elif (self.get_setting('vlsi.core.lvs_tool') == "hammer.lvs.netgen"):
            pmos = 'sky130_fd_pr__pfet_01v8_hvt'
            nmos = 'sky130_fd_pr__nfet_01v8'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying CDL netlist: {} -> {}".format
                    (source_path, dest_path))
                df.write("*.SCALE MICRON\n")
                for line in sf:
                    line = line.replace('pfet_01v8_hvt', pmos)
                    line = line.replace('nfet_01v8'    , nmos)
                    df.write(line)

    # Copy and hack the verilog
    #   - <library_name>.v: remove 'wire 1' and one endif line to fix syntax errors
    #   - primitives.v: set default nettype to 'wire' instead of 'none'
    #           (the open-source RTL sim tools don't treat undeclared signals as errors)
    #   - Deal with numerous inconsistencies in timing specify blocks.
    def setup_verilog(self) -> None:
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)

        # <library_name>.v
        source_path = setting_dir / 'libs.ref' / self.library_name / 'verilog' / f'{self.library_name}.v'
        if not source_path.exists():
            raise FileNotFoundError(f"Verilog not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / f'{self.library_name}.v'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying Verilog netlist: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    line = line.replace('wire 1','// wire 1')
                    line = line.replace('`endif SKY130_FD_SC_HD__LPFLOW_BLEEDER_FUNCTIONAL_V','`endif // SKY130_FD_SC_HD__LPFLOW_BLEEDER_FUNCTIONAL_V')
                    df.write(line)
                    
        # Additionally hack out the specifies
        sl = []
        with open(dest_path, 'r') as sf:
            sl = sf.readlines()

            # Find timing declaration
            start_idx = [idx for idx, line in enumerate(sl) if "`ifndef SKY130_FD_SC_HD__LPFLOW_BLEEDER_1_TIMING_V" in line][0]

            # Search for the broken statement
            search_range = range(start_idx+1, len(sl))
            broken_specify_idx = len(sl)-1
            broken_substr = "(SHORT => VPWR) = (0:0:0,0:0:0,0:0:0,0:0:0,0:0:0,0:0:0);"

            broken_specify_idx = [idx for idx in search_range if broken_substr in sl[idx]][0]
            endif_idx = [idx for idx in search_range if "`endif" in sl[idx]][0]

            # Now, delete all the specify statements if specify exists before an endif.
            if broken_specify_idx < endif_idx:
                self.logger.info("Removing incorrectly formed specify block.")
                cell_def_range = range(start_idx+1, endif_idx)
                start_specify_idx = [idx for idx in cell_def_range if "specify" in sl[idx]][0]
                end_specify_idx = [idx for idx in cell_def_range if "endspecify" in sl[idx]][0]
                sl[start_specify_idx:end_specify_idx+1] = [] # Dice

        # Deal with the nonexistent net tactfully (don't code in brittle replacements)
        self.logger.info("Fixing broken net references with select specify blocks.")
        pattern = r"^\s*wire SLEEP.*B.*delayed;"
        capture_pattern = r".*(SLEEP.*?B.*?delayed).*"
        pattern_idx = [(idx, re.findall(capture_pattern, value)[0]) for idx, value in enumerate(sl) if re.search(pattern, value)]
        for list_idx, pattern_tuple in enumerate(pattern_idx):
            if list_idx != len(pattern_idx)-1:
                search_range = range(pattern_tuple[0]+1, pattern_idx[list_idx+1][0])
            else: 
                search_range = range(pattern_tuple[0]+1, len(sl))
            for idx in search_range:
                list = re.findall(capture_pattern, sl[idx])
                for elem in list:
                    if elem != pattern_tuple[1]:
                        sl[idx] = sl[idx].replace(elem, pattern_tuple[1])
                        self.logger.info(f"Incorrect reference `{elem}` to be replaced with: `{pattern_tuple[1]}` on raw line {idx}.")
                    
        # Write back into destination 
        with open(dest_path, 'w') as df:
            df.writelines(sl)

        # primitives.v
        source_path = setting_dir / 'libs.ref' / self.library_name / 'verilog' / 'primitives.v'
        if not source_path.exists():
            raise FileNotFoundError(f"Verilog not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / 'primitives.v'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying Verilog netlist: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    line = line.replace('`default_nettype none','`default_nettype wire')
                    df.write(line)

    # Copy and hack the tech-lef, adding this very important `licon` section
    def setup_techlef(self) -> None:
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        source_path = setting_dir / 'libs.ref' / self.library_name / 'techlef' / f'{self.library_name}__nom.tlef'
        if not source_path.exists():
            raise FileNotFoundError(f"Tech-LEF not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / f'{self.library_name}__nom.tlef'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying Technology LEF: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    df.write(line)
                    if line.strip() == 'END pwell':
                        df.write(_the_tlef_edit)

    # Power pins for clamps must be CLASS CORE
    # connect/disconnect spacers must be CLASS PAD SPACER, not AREAIO
    # Current version has two errors in MACRO class definitions that break lef parser.
    def setup_io_lefs(self) -> None:
        sky130A_path = Path(self.get_setting('technology.sky130.sky130A'))
        source_path = sky130A_path / 'libs.ref' / 'sky130_fd_io' / 'lef' / 'sky130_ef_io.lef'
        if not source_path.exists():
            raise FileNotFoundError(f"IO LEF not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / 'sky130_ef_io.lef'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying IO LEF: {} -> {}".format
                    (source_path, dest_path))
                sl = sf.readlines()
                for net in ['VCCD1', 'VSSD1']:
                    start = [idx for idx,line in enumerate(sl) if 'PIN ' + net in line]
                    end = [idx for idx,line in enumerate(sl) if 'END ' + net in line]
                    intervals = zip(start, end)
                    for intv in intervals:
                        port_idx = [idx for idx,line in enumerate(sl[intv[0]:intv[1]]) if 'PORT' in line]
                        for idx in port_idx:
                            sl[intv[0]+idx]=sl[intv[0]+idx].replace('PORT', 'PORT\n      CLASS CORE ;')
                for cell in [
                    'sky130_ef_io__connect_vcchib_vccd_and_vswitch_vddio_slice_20um',
                    'sky130_ef_io__disconnect_vccd_slice_5um',
                    'sky130_ef_io__disconnect_vdda_slice_5um',
                ]:
                    # force class to spacer
                    start = [idx for idx, line in enumerate(sl) if f'MACRO {cell}' in line]
                    sl[start[0] + 1] = sl[start[0] + 1].replace('AREAIO', 'SPACER')

                # Current version has two one-off error that break lef parser.
                self.logger.info("Fixing broken sky130_ef_io__analog_esd_pad LEF definition.")
                start_broken_macro_list = ["MACRO sky130_ef_io__analog_esd_pad\n", "MACRO sky130_ef_io__analog_pad\n"]
                end_broken_macro_list = ["END sky130_ef_io__analog_pad\n", "END sky130_ef_io__analog_noesd_pad\n"]
                end_fixed_macro_list = ["END sky130_ef_io__analog_esd_pad\n", "END sky130_ef_io__analog_pad\n"]

                for start_broken_macro, end_broken_macro, end_fixed_macro in zip(start_broken_macro_list, end_broken_macro_list, end_fixed_macro_list):
                    # Get all start indices to be checked
                    start_check_indices = [idx for idx, line in enumerate(sl) if line == start_broken_macro]

                    # Extract broken macro
                    for idx_broken_macro in  start_check_indices:
                        # Find the start of the next_macro
                        idx_start_next_macro = [idx for idx in range(idx_broken_macro+1, len(sl)) if "MACRO" in sl[idx]][0]
                        # Find the broken macro ending
                        idx_end_broken_macro = len(sl)
                        idx_end_broken_macro = [idx for idx in range(idx_broken_macro+1, len(sl)) if end_broken_macro in sl[idx]][0]

                        # Fix
                        if idx_end_broken_macro < idx_start_next_macro:
                            sl[idx_end_broken_macro] = end_fixed_macro
                
                df.writelines(sl)

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {
            "innovus": [
            HammerTool.make_post_insertion_hook("init_design",      sky130_innovus_settings),
            HammerTool.make_pre_insertion_hook("place_tap_cells",   sky130_add_endcaps),
            HammerTool.make_pre_insertion_hook("power_straps",      sky130_connect_nets),
            HammerTool.make_pre_insertion_hook("write_design",      sky130_connect_nets2)
            ]}
        return hooks.get(tool_name, [])

    def get_tech_drc_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        calibre_hooks = []
        pegasus_hooks = []
        if self.get_setting("technology.sky130.drc_blackbox_srams"):
            calibre_hooks.append(HammerTool.make_post_insertion_hook("generate_drc_run_file", calibre_drc_blackbox_srams))
            pegasus_hooks.append(HammerTool.make_post_insertion_hook("generate_drc_ctl_file", pegasus_drc_blackbox_srams))
        hooks = {"calibre": calibre_hooks,
                "pegasus": pegasus_hooks
                 }
        return hooks.get(tool_name, [])

    def get_tech_lvs_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        calibre_hooks = [HammerTool.make_post_insertion_hook("generate_lvs_run_file", setup_calibre_lvs_deck)]
        pegasus_hooks = []
        if self.use_sram22:
            calibre_hooks.append(HammerTool.make_post_insertion_hook("generate_lvs_run_file", sram22_lvs_recognize_gates_all))
        if self.get_setting("technology.sky130.lvs_blackbox_srams"):
            calibre_hooks.append(HammerTool.make_post_insertion_hook("generate_lvs_run_file", calibre_lvs_blackbox_srams))
            pegasus_hooks.append(HammerTool.make_post_insertion_hook("generate_lvs_ctl_file", pegasus_lvs_blackbox_srams))
        hooks = {"calibre": calibre_hooks,
                "pegasus": pegasus_hooks
                 }
        return hooks.get(tool_name, [])

    @staticmethod
    def openram_sram_names() -> List[str]:
        """ Return a list of cell-names of the OpenRAM SRAMs (that we'll use). """
        return [
            "sky130_sram_1kbyte_1rw1r_32x256_8",
            "sky130_sram_1kbyte_1rw1r_8x1024_8",
            "sky130_sram_2kbyte_1rw1r_32x512_8"
        ]

    @staticmethod
    def sky130_sram_names() -> List[str]:
        sky130_sram_names = []
        sram_cache_json = importlib.resources.files("hammer.technology.sky130").joinpath("sram-cache.json").read_text()
        dl = json.loads(sram_cache_json)
        for d in dl:
            sky130_sram_names.append(d['name'])
        return sky130_sram_names


_the_tlef_edit = '''
LAYER licon
  TYPE CUT ;
END licon
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

##########################################################
# Clock attributes  [get_db -category cts]
##########################################################
#-------------------------------------------------------------------------------
set_db cts_target_skew 0.03
set_db cts_max_fanout 10
#set_db cts_target_max_transition_time .3
set_db opt_setup_target_slack 0.10
set_db opt_hold_target_slack 0.10

##########################################################
# Routing attributes  [get_db -category route]
##########################################################
#-------------------------------------------------------------------------------
set_db route_design_antenna_diode_insertion 1
set_db route_design_antenna_cell_name "sky130_fd_sc_hd__diode_2"

set_db route_design_high_freq_search_repair true
set_db route_design_detail_post_route_spread_wire true
set_db route_design_with_si_driven true
set_db route_design_with_timing_driven true
set_db route_design_concurrent_minimize_via_count_effort high
set_db opt_consider_routing_congestion true
set_db route_design_detail_use_multi_cut_via_effort medium
    '''
    )
    if ht.hierarchical_mode in {HierarchicalMode.Top, HierarchicalMode.Flat}:
        ht.append(
            '''
# For top module: snap die to manufacturing grid, not placement grid
set_db floorplan_snap_die_grid manufacturing
        '''
        )
    return True

def sky130_connect_nets(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "connect global nets only for par"
    assert isinstance(ht, TCLTool), "connect global nets can only run on TCL tools"
    for pwr_gnd_net in (ht.get_all_power_nets() + ht.get_all_ground_nets()):
            if pwr_gnd_net.tie is not None:
                ht.append("connect_global_net {tie} -type pg_pin -pin_base_name {net} -all -auto_tie -netlist_override".format(tie=pwr_gnd_net.tie, net=pwr_gnd_net.name))
                ht.append("connect_global_net {tie} -type net    -net_base_name {net} -all -netlist_override".format(tie=pwr_gnd_net.tie, net=pwr_gnd_net.name))
    return True

# Pair VDD/VPWR and VSS/VGND nets
#   these commands are already added in Innovus.write_netlist,
#   but must also occur before power straps are placed
def sky130_connect_nets2(ht: HammerTool) -> bool:
    sky130_connect_nets(ht)
    return True


def sky130_add_endcaps(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "endcap insertion only for par"
    assert isinstance(ht, TCLTool), "endcap insertion can only run on TCL tools"
    endcap_cells=ht.technology.get_special_cell_by_type(CellType.EndCap)
    endcap_cell=endcap_cells[0].name[0]
    ht.append(
        f'''
set_db add_endcaps_boundary_tap     true
set_db add_endcaps_left_edge        {endcap_cell}
set_db add_endcaps_right_edge       {endcap_cell}
add_endcaps
    '''
    )
    return True

def efabless_ring_io(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "IO ring instantiation only for par"
    assert isinstance(ht, TCLTool), "IO ring instantiation can only run on TCL tools"
    io_file = ht.get_setting("technology.sky130.io_file")
    ht.append(f"read_io_file {io_file} -no_die_size_adjust")
    p_nets = list(map(lambda s: s.name, ht.get_independent_power_nets()))
    g_nets = list(map(lambda s: s.name, ht.get_independent_ground_nets()))
    ht.append(f'''
# Global net connections
connect_global_net VDDA -type pg_pin -pin_base_name VDDA -verbose
connect_global_net VDDIO -type pg_pin -pin_base_name VDDIO* -verbose
connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VCCD* -verbose
connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VCCHIB -verbose
connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VSWITCH -verbose
connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSA -verbose
connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSIO* -verbose
connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSD* -verbose
    ''')
    ht.append('''
# IO fillers
set io_fillers {sky130_ef_io__connect_vcchib_vccd_and_vswitch_vddio_slice_20um sky130_ef_io__com_bus_slice_10um sky130_ef_io__com_bus_slice_5um sky130_ef_io__com_bus_slice_1um}
add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side top -filler_orient r0
add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side right -filler_orient r270
add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side bottom -filler_orient r180
add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side left -filler_orient r90
# Fix placement
set io_filler_insts [get_db insts IO_FILLER_*]
set_db $io_filler_insts .place_status fixed
    ''')
    # An offset of 40um is used to place the core ring inside the core area. It
    # can be decreased down to 5um as desired, but will require additional
    # routing / settings to connect the core power stripes to the ring.
    ht.append(f'''
# Core ring
add_rings -follow io -layer met5 -nets {{ {p_nets[0]} {g_nets[0]} }} -offset 40 -width 13 -spacing 3
route_special -connect pad_pin -nets {{ {p_nets[0]} {g_nets[0]} }} -detailed_log
    ''')
    ht.append('''
# Prevent buffering on TIE_LO_ESD and TIE_HI_ESD
set_dont_touch [get_db [get_db pins -if {.name == *TIE*ESD}] .net]
    ''')
    return True

def calibre_drc_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "Exlude SRAMs only in DRC"
    drc_box = ''
    for name in SKY130Tech.sky130_sram_names():
        drc_box += f"\nEXCLUDE CELL {name}"
    run_file = ht.drc_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(drc_box)
    return True

def pegasus_drc_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "Exlude SRAMs only in DRC"
    drc_box = ''
    for name in SKY130Tech.sky130_sram_names():
        drc_box += f"\nexclude_cell {name}"
    run_file = ht.drc_ctl_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(drc_box)
    return True

def calibre_lvs_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Blackbox and filter SRAMs only in LVS"
    lvs_box = ''
    for name in SKY130Tech.sky130_sram_names():
        lvs_box += f"\nLVS BOX {name}"
        lvs_box += f"\nLVS FILTER {name} OPEN "
    run_file = ht.lvs_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(lvs_box)
    return True

def pegasus_lvs_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Blackbox and filter SRAMs only in LVS"
    lvs_box = ''
    for name in SKY130Tech.sky130_sram_names():
        lvs_box += f"\nlvs_black_box {name} -gray"
    run_file = ht.lvs_ctl_file  # type: ignore
    with open(run_file, "r+") as f:
        # Remove SRAM SPICE file includes.
        pattern = 'schematic_path.*({}).*spice;\n'.format('|'.join(SKY130Tech.sky130_sram_names()))
        matcher = re.compile(pattern)
        contents = f.read()
        fixed_contents = matcher.sub("", contents) + lvs_box
        f.seek(0)
        f.write(fixed_contents)
    return True

def sram22_lvs_recognize_gates_all(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Change 'LVS RECOGNIZE GATES' from 'NONE' to 'ALL' for SRAM22"
    run_file = ht.lvs_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write("LVS RECOGNIZE GATES ALL")
    return True


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

def setup_calibre_lvs_deck(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Modify Calibre LVS deck for LVS only"
    # Remove conflicting specification statements found in PDK LVS decks
    pattern = '.*({}).*\n'.format('|'.join(LVS_DECK_SCRUB_LINES))
    matcher = re.compile(pattern)

    source_paths = ht.get_setting('technology.sky130.lvs_deck_sources')
    lvs_decks = ht.technology.config.lvs_decks
    if not lvs_decks:
        return True
    for i,deck in enumerate(lvs_decks):
        if deck.tool_name != 'calibre': continue
        try:
            source_path = Path(source_paths[i])
        except IndexError:
            ht.logger.error(
                'No corresponding source for LVS deck {}'.format(deck))
            continue
        if not source_path.exists():
            raise FileNotFoundError(f"LVS deck not found: {source_path}")
        dest_path = deck.path
        ht.technology.ensure_dirs_exist(dest_path)
        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                ht.logger.info("Modifying LVS deck: {} -> {}".format
                    (source_path, dest_path))
                df.write(matcher.sub("", sf.read()))
                df.write(LVS_DECK_INSERT_LINES)
    return True


tech = SKY130Tech()
