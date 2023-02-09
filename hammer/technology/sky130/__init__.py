#  SKY130 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os, shutil
from pathlib import Path
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any
import importlib

import hammer.tech
from hammer.tech import HammerTechnology
from hammer.vlsi import HammerTool, HammerPlaceAndRouteTool, TCLTool, HammerDRCTool, HammerLVSTool, HammerToolHookAction

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
        self.use_openram = os.path.exists(self.get_setting("technology.sky130.openram_lib"))
        self.use_nda_files = os.path.exists(self.get_setting("technology.sky130.sky130_nda"))
        self.setup_cdl()
        self.setup_verilog()
        self.setup_techlef()
        self.setup_lvs_deck()
        print('Loaded Sky130 Tech')


    # Copy and hack the cdl, replacing pfet_01v8_hvt/nfet_01v8 with phighvt/nshort
    def setup_cdl(self) -> None:
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        source_path = setting_dir / 'libs.ref' / self.library_name / 'cdl' / f'{self.library_name}.cdl'
        if not source_path.exists():
            raise FileNotFoundError(f"CDL not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / f'{self.library_name}.cdl'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying CDL netlist: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    line = line.replace('pfet_01v8_hvt', 'phighvt')
                    line = line.replace('nfet_01v8'    , 'nshort')
                    df.write(line)

    # Copy and hack the verilog
    #   - <library_name>.v: remove 'wire 1' and one endif line to fix syntax errors
    #   - primitives.v: set default nettype to 'wire' instead of 'none'
    #           (the open-source RTL sim tools don't treat undeclared signals as errors)
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

    # Remove conflicting specification statements found in PDK LVS decks
    def setup_lvs_deck(self) -> None:
        if not self.use_nda_files: return
        pattern = '.*({}).*\n'.format('|'.join(LVS_DECK_SCRUB_LINES))
        matcher = re.compile(pattern)

        source_paths = self.get_setting('technology.sky130.lvs_deck_sources')
        lvs_decks = self.config.lvs_decks
        if not lvs_decks:
            return
        for i in range(len(lvs_decks)):
            deck = lvs_decks[i]
            try:
                source_path = Path(source_paths[i])
            except IndexError:
                self.logger.error(
                    'No corresponding source for LVS deck {}'.format(deck))
            if not source_path.exists():
                raise FileNotFoundError(f"LVS deck not found: {source_path}")
            dest_path = self.expand_tech_cache_path(str(deck.path))
            self.ensure_dirs_exist(dest_path)
            with open(source_path, 'r') as sf:
                with open(dest_path, 'w') as df:
                    self.logger.info("Modifying LVS deck: {} -> {}".format
                        (source_path, dest_path))
                    df.write(matcher.sub("", sf.read()))
                    df.write(LVS_DECK_INSERT_LINES)

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {
            "openroad": [
            HammerTool.make_pre_insertion_hook("detailed_placement",   sky130_set_wire_rc)
            ],
            "innovus": [
            HammerTool.make_post_insertion_hook("init_design",      sky130_innovus_settings),
            HammerTool.make_pre_insertion_hook("place_tap_cells",   sky130_add_endcaps),
            HammerTool.make_pre_insertion_hook("power_straps",      sky130_connect_nets),
            HammerTool.make_pre_insertion_hook("write_design",      sky130_connect_nets2)
            ]}
        return hooks.get(tool_name, [])

    def get_tech_drc_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        if not self.use_openram: return []
        hooks = {"calibre": [
            HammerTool.make_post_insertion_hook("generate_drc_run_file", drc_blackbox_openram_srams)
            ]}
        return hooks.get(tool_name, [])

    def get_tech_lvs_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        if not self.use_openram: return []
        hooks = {"calibre": [
            HammerTool.make_post_insertion_hook("generate_lvs_run_file", lvs_blackbox_openram_srams)
            ]}
        return hooks.get(tool_name, [])

    @staticmethod
    def openram_sram_names() -> List[str]:
        """ Return a list of cell-names of the OpenRAM SRAMs (that we'll use). """
        return [
            "sky130_sram_1kbyte_1rw1r_32x256_8",
            "sky130_sram_1kbyte_1rw1r_8x1024_8",
            "sky130_sram_2kbyte_1rw1r_32x512_8"
        ]


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

# black-box SRAMs during LVS
for name in SKY130Tech.openram_sram_names():
    LVS_DECK_INSERT_LINES += f"LVS BOX {name} \n"
    LVS_DECK_INSERT_LINES += f"LVS FILTER {name} OPEN \n"

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
set_db route_design_bottom_routing_layer 2

set_db route_design_high_freq_search_repair true
set_db route_design_detail_post_route_spread_wire true
set_db route_design_with_si_driven true
set_db route_design_with_timing_driven true
set_db route_design_concurrent_minimize_via_count_effort high
set_db opt_consider_routing_congestion true
set_db route_design_detail_use_multi_cut_via_effort medium
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

def sky130_set_wire_rc(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "set wire rc only for par"
    assert isinstance(ht, TCLTool), "set wire rc can only run on TCL tools"
    rc_file=importlib.resources.files("hammer.technology.sky130") / "extra/sky130hd.rc"
    ht.append(f"""
################################################################
# Repair max slew/cap/fanout violations and normalize slews
source {rc_file}
set_wire_rc -signal -layer "met2"
set_wire_rc -clock  -layer "met5"
    """)
    return True

def drc_blackbox_openram_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "Exlude SRAMs only in DRC"
    drc_box = ''
    for name in SKY130Tech.openram_sram_names():
        drc_box += f"\nEXCLUDE CELL {name}"
    run_file = ht.drc_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(drc_box)
    return True

def lvs_blackbox_openram_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Blackbox and filter SRAMs only in LVS"
    lvs_box = ''
    for name in SKY130Tech.openram_sram_names():
        lvs_box += f"\nLVS BOX {name}"
        lvs_box += f"\nLVS FILTER {name} OPEN "
    run_file = ht.lvs_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(lvs_box)
    return True

tech = SKY130Tech()
