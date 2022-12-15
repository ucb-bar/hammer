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
from types import new_class
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

from hammer.tech import HammerTechnology
from hammer.vlsi import HammerTool, HammerPlaceAndRouteTool, HammerDRCTool, MentorCalibreTool, TCLTool, HammerToolHookAction

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
        self.generate_multi_vt_gds()
        self.fix_icg_libs()

    def generate_multi_vt_gds(self) -> None:
        """
        PDK GDS only contains RVT cells.
        This patch will generate the other 3(LVT, SLVT, SRAM) VT GDS files.
        """
        try:
            os.makedirs(os.path.join(self.cache_dir, "GDS"))
        except:
            self.logger.info("Multi-VT GDS's already created")
            return None

        try:
            self.logger.info("Generating GDS for Multi-VT cells using {}...".format(self.gds_tool.__name__))

            stdcell_dir = self.get_setting("technology.asap7.stdcell_install_dir")
            orig_gds = os.path.join(stdcell_dir, "GDS/asap7sc7p5t_27_R_201211.gds")

            if self.gds_tool.__name__ == 'gdstk':
                # load original GDS
                asap7_original_gds = self.gds_tool.read_gds(infile=orig_gds)
                original_cells = asap7_original_gds.cells
                cell_list = list(map(lambda c: c.name, original_cells))
                # required libs
                multi_libs = {
                    "L": {
                        "lib": self.gds_tool.Library(),
                        "mvt_layer": 98
                        },
                    "SL": {
                        "lib": self.gds_tool.Library(),
                        "mvt_layer": 97
                        },
                    "SRAM": {
                        "lib": self.gds_tool.Library(),
                        "mvt_layer": 110
                        },
                }
                # create new libs
                for vt, multi_lib in multi_libs.items():
                    multi_lib['lib'].name = asap7_original_gds.name.replace('R', vt)

                for cell in original_cells:
                    # extract polygon from layer 100(the boundary for cell)
                    boundary_polygon = next(filter(lambda p: p.layer==100, cell.polygons))
                    for vt, multi_lib in multi_libs.items():
                        new_cell_name = cell.name.rstrip('R') + vt
                        cell_list.append(new_cell_name)
                        mvt_layer = multi_lib['mvt_layer']
                        # copy boundary_polygon to mvt_layer to mark the this cell is a mvt cell.
                        mvt_polygon = self.gds_tool.Polygon(boundary_polygon.points, multi_lib['mvt_layer'], 0)
                        mvt_cell = cell.copy(name=new_cell_name, deep_copy=True).add(mvt_polygon)
                        # add mvt_cell to corresponding multi_lib
                        multi_lib['lib'].add(mvt_cell)

                for vt, multi_lib in multi_libs.items():
                    # write multi_lib
                    new_gds = os.path.basename(orig_gds).replace('R', vt)
                    multi_lib['lib'].write_gds(os.path.join(self.cache_dir, 'GDS', new_gds))

            elif self.gds_tool.__name__ == 'gdspy':
                # load original GDS
                asap7_original_gds = self.gds_tool.GdsLibrary().read_gds(infile=orig_gds, units='import')
                original_cells = asap7_original_gds.cell_dict
                cell_list = list(map(lambda c: c.name, original_cells.values()))
                # required libs
                multi_libs = {
                    "L": {
                        "lib": self.gds_tool.GdsLibrary(),
                        "mvt_layer": 98
                        },
                    "SL": {
                        "lib": self.gds_tool.GdsLibrary(),
                        "mvt_layer": 97
                        },
                    "SRAM": {
                        "lib": self.gds_tool.GdsLibrary(),
                        "mvt_layer": 110
                        },
                }
                # create new libs
                for vt, multi_lib in multi_libs.items():
                    multi_lib['lib'].name = asap7_original_gds.name.replace('R', vt)

                for cell in original_cells.values():
                    poly_dict = cell.get_polygons(by_spec=True)
                    # extract polygon from layer 100(the boundary for cell)
                    boundary_polygon = poly_dict[(100, 0)]
                    for vt, multi_lib in multi_libs.items():
                        new_cell_name = cell.name.rstrip('R') + vt
                        cell_list.append(new_cell_name)
                        mvt_layer = multi_lib['mvt_layer']
                        # copy boundary_polygon to mvt_layer to mark the this cell is a mvt cell.
                        mvt_polygon = self.gds_tool.PolygonSet(boundary_polygon, multi_lib['mvt_layer'], 0)
                        mvt_cell = cell.copy(name=new_cell_name, exclude_from_current=True, deep_copy=True).add(mvt_polygon)
                        # add mvt_cell to corresponding multi_lib
                        multi_lib['lib'].add(mvt_cell)

                for vt, multi_lib in multi_libs.items():
                    # write multi_lib
                    new_gds = os.path.basename(orig_gds).replace('R', vt)
                    multi_lib['lib'].write_gds(os.path.join(self.cache_dir, 'GDS', new_gds))

            # Write out cell list for scaling script
            with open(os.path.join(self.cache_dir, 'stdcells.txt'), 'w') as f:
                f.writelines('{}\n'.format(cell) for cell in cell_list)

        except:
            os.rmdir(os.path.join(self.cache_dir, "GDS"))
            self.logger.error("GDS patching failed! Check your gdstk, gdspy, and/or ASAP7 PDK installation.")
            sys.exit()

    def fix_icg_libs(self) -> None:
        """
        ICG cells are missing statetable.
        """
        try:
            os.makedirs(os.path.join(self.cache_dir, "LIB/NLDM"))
        except:
            self.logger.info("ICG LIBs already fixed")
            return None

        try:
            self.logger.info("Fixing ICG LIBs...")
            statetable_text = "\\n".join([
               '\    statetable ("CLK ENA SE", "IQ") {',
                '      table : "L L L : - : L ,  L L H : - : H , L H L : - : H , L H H : - : H , H - - : - : N ";',
                '    }'])
            gclk_func = "CLK & IQ"
            lib_dir = os.path.join(self.get_setting("technology.asap7.stdcell_install_dir"), "LIB/NLDM")
            old_libs = glob.glob(os.path.join(lib_dir, "*SEQ*"))
            new_libs = list(map(lambda l: os.path.join(self.cache_dir, "LIB/NLDM", os.path.basename(l)), old_libs))

            for olib, nlib in zip(old_libs, new_libs):
                # Use gzip and sed directly rather than gzip python module
                # Add the statetable to ICG cells
                # Change function to state_function for pin GCLK
                subprocess.call(["gzip -cd {olib} | sed '/ICGx*/a {stbl}' | sed '/CLK & IQ/s/function/state_function/g' | gzip > {nlib}".format(olib=olib, stbl=statetable_text, nlib=nlib)], shell=True)
        except:
            os.rmdir(os.path.join(self.cache_dir, "LIB/NLDM"))
            os.rmdir(os.path.join(self.cache_dir, "LIB"))
            self.logger.error("Failed to fix ICG LIBs. Check your ASAP7 installation!")
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
    # This is from the Cadence tools
    cadence_output_gds_name = ht.output_gds_filename  # type: ignore

    ht.append('''
# Innovus <19.1 appends some bad LD_LIBRARY_PATHS, so remove them before executing python
set env(LD_LIBRARY_PATH) [join [lsearch -not -all -inline [split $env(LD_LIBRARY_PATH) ":"] "*INNOVUS*"] ":"]
asap7_gds_scale {stdcells_file} {gds_file}
'''.format(stdcells_file = os.path.join(ht.technology.cache_dir, 'stdcells.txt'),
           gds_file = cadence_output_gds_name))
    return True

def asap7_generate_drc_run_file(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "asap7_generate_drc_run_file can only run on drc"
    assert isinstance(ht, MentorCalibreTool), "asap7_generate_drc_run_file can only run on a Calibre tool"
    """
    Replace drc_run_file to prevent conflicting SVRF statements
    Symlink DRC GDS to test.gds as expected by deck and results directories
    """
    # These are from the Calibre tools
    ht_drc_run_file = ht.drc_run_file  # type: ignore
    ht_max_drc_results = ht.max_drc_results  # type: ignore
    ht_virtual_connect_colon = ht.virtual_connect_colon  # type: ignore

    new_layout_file = os.path.join(ht.run_dir, 'test.gds')
    if not os.path.lexists(new_layout_file):
        os.symlink(os.path.splitext(ht.layout_file)[0] + '_drc.gds', new_layout_file)
    ht.layout_file = new_layout_file

    with open(ht_drc_run_file, "w") as f:
        f.write(textwrap.dedent("""
        // Generated by HAMMER

        DRC MAXIMUM RESULTS {max_results}
        DRC MAXIMUM VERTEX 4096

        DRC CELL NAME YES CELL SPACE XFORM

        VIRTUAL CONNECT COLON {virtual_connect}
        VIRTUAL CONNECT REPORT NO
        """).format(
            max_results=ht_max_drc_results,
            virtual_connect="YES" if ht_virtual_connect_colon else "NO"
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
