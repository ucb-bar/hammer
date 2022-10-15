#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  asap7 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os
import shutil
import glob
import subprocess
import textwrap
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

from hammer_tech import HammerTechnology
from hammer_vlsi import HammerTool, HammerPlaceAndRouteTool, HammerDRCTool, MentorCalibreTool, TCLTool, HammerToolHookAction

class ASAP7Tech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """
    def post_install_script(self) -> None:
        try:
            # Prioritize gdstk
            self.gds_tool = __import__('gdstk')
        except ImportError:
            self.logger.info("gdstk not found, falling back to gdspy...")
            try:
                self.gds_tool = __import__('gdspy')
                assert('1.4' in self.gds_tool.__version__)
            except (ImportError, AssertionError):
                self.logger.error("Check your gdspy v1.4 installation! Unable to hack ASAP7 PDK.")
                shutil.rmtree(self.cache_dir)
                sys.exit()

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {"innovus": [
            HammerTool.make_post_persistent_hook("init_design", asap7_innovus_settings),
            HammerTool.make_post_insertion_hook("floorplan_design", asap7_update_floorplan),
            HammerTool.make_post_insertion_hook("write_design", asap7_scale_final_gds)
            ]}
        return hooks.get(tool_name, [])

    def get_tech_drc_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {"calibre": [
            HammerTool.make_replacement_hook("generate_drc_run_file", asap7_generate_drc_run_file)
            ]}
        return hooks.get(tool_name, [])

def asap7_innovus_settings(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    """Settings that may need to be reapplied at every tool invocation
    Note that the particular routing layer settings here will persist in Innovus;
    this hook only serves as an example of what commands may need to persist."""
    ht.append('''
set_db route_design_bottom_routing_layer 2
set_db route_design_top_routing_layer 7

# Ignore 1e+31 removal arcs for ASYNC DFF cells
set_db timing_analysis_async_checks no_async

# Via preferences for stripes
set_db generate_special_via_rule_preference { M7_M6widePWR1p152 M6_M5widePWR1p152 M5_M4widePWR0p864 M4_M3widePWR0p864 M3_M2widePWR0p936 }

# Prevent extending M1 pins in cells
set_db route_design_with_via_in_pin true
    ''')
    return True

def asap7_update_floorplan(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "asap7_update_floorplan can only run on par"
    assert isinstance(ht, TCLTool), "asap7_update_floorplan can only run on TCL tools"
    """
    This is needed to block top/bottom site rows and re-do wiring tracks.
    This resolves many DRCs and removes the need for the user to do it in placement constraints.
    """
    ht.append('''
# Need to delete and recreate tracks based on tech LEF pitches but overriding offsets
add_tracks -honor_pitch -offsets { M4 horiz 0.048 M5 vert 0.048 M6 horiz 0.064 M7 vert 0.064 }

# Create place blockage on top & bottom row, fixes wiring issue + power vias for DRC/LVS
set core_lly [get_db current_design .core_bbox.ll.y]
set core_ury [expr [get_db current_design .core_bbox.ur.y] - 1.08]
set botrow [get_db rows -if {.rect.ll.y == $core_lly}]
set toprow [get_db rows -if {.rect.ur.y > $core_ury}]
create_place_blockage -area [get_db $botrow .rect] -name ROW_BLOCK_BOT
create_place_blockage -area [get_db $toprow .rect] -name ROW_BLOCK_TOP
''')
    return True

def asap7_scale_final_gds(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "asap7_scale_final_gds can only run on par"
    assert isinstance(ht, TCLTool), "asap7_scale_final_gds can only run on TCL tools"
    """
    Scale the final GDS by a factor of 4
    scale_gds_script writes the actual Python script to execute from the Tcl interpreter
    """
    ht.append('''
# Innovus <19.1 appends some bad LD_LIBRARY_PATHS, so remove them before executing python
set env(LD_LIBRARY_PATH) [join [lsearch -not -all -inline [split $env(LD_LIBRARY_PATH) ":"] "*INNOVUS*"] ":"]
{scale_script} {stdcells_file} {gds_file}
'''.format(scale_script = os.path.join(os.path.dirname(__file__), 'gds_scale.py'),
           stdcells_file = os.path.join(ht.technology.cache_dir, 'stdcells.txt'),
           gds_file = ht.output_gds_filename))
    return True

def asap7_generate_drc_run_file(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "asap7_generate_drc_run_file can only run on drc"
    assert isinstance(ht, MentorCalibreTool), "asap7_generate_drc_run_file can only run on a Calibre tool"
    """
    Replace drc_run_file to prevent conflicting SVRF statements
    Symlink DRC GDS to test.gds as expected by deck and results directories
    """
    new_layout_file = os.path.join(ht.run_dir, 'test.gds')
    if not os.path.lexists(new_layout_file):
        os.symlink(os.path.splitext(ht.layout_file)[0] + '_drc.gds', new_layout_file)
    ht.layout_file = new_layout_file

    with open(ht.drc_run_file, "w") as f:
        f.write(textwrap.dedent("""
        // Generated by HAMMER

        DRC MAXIMUM RESULTS {max_results}
        DRC MAXIMUM VERTEX 4096

        DRC CELL NAME YES CELL SPACE XFORM

        VIRTUAL CONNECT COLON {virtual_connect}
        VIRTUAL CONNECT REPORT NO
        """).format(
            max_results=ht.max_drc_results,
            virtual_connect="YES" if ht.virtual_connect_colon else "NO"
        )
        )
        # Include paths to all supplied decks
        for rule in ht.get_drc_decks():
            f.write("INCLUDE \"{}\"\n".format(rule.path))
        # Note that an empty list means run all, and Calibre conveniently will do just that
        # if we don't specify any individual checks to run.
        if len(ht.drc_rules_to_run()) > 0:
            f.write("\nDRC SELECT CHECK\n")
        for check in ht.drc_rules_to_run():
            f.write("\t\"{}\"\n".format(check))
        f.write("\nDRC ICSTATION YES\n")
        f.write(ht.get_additional_drc_text())
    return True

tech = ASAP7Tech()
