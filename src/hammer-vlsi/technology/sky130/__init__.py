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
        # maybe run open_pdks for the user and install in tech cache...?
        # this takes a while and ~7Gb
        self.library_name = 'sky130_fd_sc_hd'
        self.setup_cdl()
        self.setup_techlef()
        self.setup_layermap()
        self.setup_lvs_deck()
        print('Loaded Sky130 Tech')

    # Helper functions - copied from TSMC28 plugin
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
            new_line = line.replace('pfet_01v8_hvt','phighvt')
            new_line = new_line.replace('nfet_01v8',    'nshort')
            f_new.write(new_line)
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

    def setup_layermap(self) -> None:
        """ Copy the layer-map into `self.cache_dir` """
        nda_dir = self.get_setting("technology.sky130.sky130_nda")
        nda_dir = Path(nda_dir)
        layermap = nda_dir / "s8/V2.0.1/VirtuosoOA/libs/technology_library/technology_library.layermap"
        if not layermap.exists():
            raise FileNotFoundError(f"Layer-map not found: {layermap}")
        cache_path = Path(self.cache_dir) 
        os.makedirs(cache_path, exist_ok=True)
        shutil.copy(layermap, cache_path)

    def setup_lvs_deck(self) -> None:
        """Remove conflicting specification statements found in PDK LVS decks."""
        pattern = '.*({}).*\n'.format('|'.join(LVS_DECK_SCRUB_LINES))
        matcher = re.compile(pattern)

        source_paths = self.get_setting('technology.sky130.lvs_deck_sources')
        lvs_decks = list(self.config.lvs_decks)
        for i in range(len(lvs_decks)):
            deck = lvs_decks[i]
            try:
                source_path = source_paths[i]
            except IndexError:
                self.logging.error(
                    'No corresponding source for LVS deck {}'.format(deck))
            dest_path = self.expand_tech_cache_path(str(deck.path))
            self.ensure_dirs_exist(dest_path)
            with open(source_path, 'r') as sf:
                with open(dest_path, 'w') as df:
                    self.logger.info("Modifying LVS deck: {} -> {}".format
                        (source_path, dest_path))
                    df.write(matcher.sub("", sf.read()))  

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {"innovus": [
            HammerTool.make_post_insertion_hook("init_design",      sky130_innovus_settings),
            HammerTool.make_pre_insertion_hook("place_tap_cells",   sky130_place_endcaps),
            HammerTool.make_pre_insertion_hook("power_straps",      sky130_power_nets),
            #HammerTool.make_replacement_hook("power_straps", intech22_innovus.intech22_reference_power_straps),
            # HammerTool.make_post_insertion_hook("power_straps", intech22_innovus.intech22_m2_staples),
            # HammerTool.make_pre_insertion_hook("clock_tree", intech22_innovus.intech22_cts_options),
            # HammerTool.make_replacement_hook("add_fillers", intech22_innovus.intech22_add_fillers),
            ]}
        return hooks.get(tool_name, [])



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

# various Innovus database settings
def sky130_innovus_settings(ht: HammerTool) -> bool:
    assert isinstance(
        ht, HammerPlaceAndRouteTool
    ), "Innovus settings can only run on par"
    """Settings for every tool invocation"""
    ht.append(
        '''  
##########################################################
# Routing attributes  [get_db -category route]
##########################################################
#-------------------------------------------------------------------------------
set_db route_design_antenna_diode_insertion 1
set_db route_design_antenna_cell_name "sky130_fd_sc_hd__diode_2"
set_db route_design_bottom_routing_layer 2
    '''
    )
    return True   

# Pair VDD/VPWR and VSS/VGND nets
#   these commands are already added in Innovus.write_netlist,
#   but must also occur before power straps are placed
def sky130_power_nets(ht: HammerTool) -> bool:
    assert isinstance(
        ht, HammerPlaceAndRouteTool
    ), "Innovus settings can only run on par"
    """Settings for every tool invocation"""
    ht.append(
        '''  
connect_global_net VDD -type net -net_base_name VPWR
connect_global_net VSS -type net -net_base_name VGND
    '''
    )
    return True

# reference: /tools/commercial/skywater/swtech130/skywater-src-nda/scs8hd/V0.0.2/scripts
def sky130_place_endcaps(ht: HammerTool) -> bool:
    assert isinstance(
        ht, HammerPlaceAndRouteTool
    ), "endcap insertion can only run on par"
    ht.append(
        '''  
set_db add_endcaps_boundary_tap        true
set_db add_endcaps_left_edge sky130_fd_sc_hd__tap_1
set_db add_endcaps_right_edge sky130_fd_sc_hd__tap_1
add_endcaps
    '''
    )
    return True

tech = SKY130Tech()

