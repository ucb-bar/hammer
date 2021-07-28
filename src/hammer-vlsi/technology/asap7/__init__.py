#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  asap7 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os
import tempfile
import shutil
import glob
import subprocess
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

from hammer_tech import HammerTechnology
from hammer_vlsi import HammerTool, HammerPlaceAndRouteTool, TCLTool, HammerToolHookAction

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
            statetable_text = """\    statetable ("CLK ENA SE", "IQ") {\\n      table : "L L L : - : L ,  L L H : - : H , L H L : - : H , L H H : - : H , H - - : - : N ";\\n    }"""
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


    def scale_gds_script(self, gds_file: str) -> str:
        """
        Raw Python script to scale GDS.
        Needs to be written out to a file from par tool, then executed.
        Needs the standard cell base list to exclude from scaling
        and the GDS file to scale.
        Note: Need to escape TCL constructs such as [] and {}!
        """

        return """#!/usr/bin/python3

# Scale the final GDS by a factor of 4
# This is a tech hook that should be inserted post write_design

import sys, glob, os, re

try:
    import gdstk
except ImportError:
    try:
        print('gdstk not found, falling back to gdspy...')
        import gdspy
    except ImportError:
        print('Check your gdspy installation!')
        sys.exit()

print('Scaling down place & routed GDS')

# load the standard cell list
cell_list = \[line.rstrip() for line in open('{cell_list_file}', 'r')\]

if 'gdstk' in sys.modules:
    # load original_gds
    gds_lib = gdstk.read_gds(infile='{gds_file}')
    # Iterate through cells that aren't part of standard cell library and scale
    for cell in list(filter(lambda c: c.name not in cell_list, gds_lib.cells)):
        print('Scaling down ' + cell.name)

        # Need to remove 'blk' layer from any macros, else LVS rule deck interprets it as a polygon
        # This has a layer datatype of 4
        # Then scale down the polygon
        for poly in list(filter(lambda p: p.datatype != 4, cell.polygons)):
            poly.scale(0.25)

        # Scale paths
        for path in cell.paths:
            path.scale(0.25)

        # Scale and move labels
        for label in cell.labels:
            # Bug fix for some EDA tools that didn't set MAG field in gds file
            # Maybe this is expected behavior in ASAP7 PDK
            label.magnification = 0.25
            label.origin = tuple(i * 0.25 for i in label.origin)

        # Move references (which are scaled if needed)
        for ref in cell.references:
            ref.origin = tuple(i * 0.25 for i in ref.origin)

    # Overwrite original GDS file
    gds_lib.write_gds('{gds_file}')

    # We can also write an SVG of the top cell
    gds_lib.top_level()[0].write_svg(os.path.splitext('{gds_file}')\[0\] + '.svg')

elif 'gdspy' in sys.modules:
    # load original_gds
    gds_lib = gdspy.GdsLibrary().read_gds(infile='{gds_file}', units='import')
    # Iterate through cells that aren't part of standard cell library and scale
    for k,v in gds_lib.cell_dict.items():
        if not any(cell in k for cell in cell_list):
            print('Scaling down ' + k)

            # Need to remove 'blk' layer from any macros, else LVS rule deck interprets it as a polygon
            # This has a layer datatype of 4
            # Then scale down the polygon
            v.polygons = \[poly.scale(0.25) for poly in v.polygons if not 4 in poly.datatypes\]

            # Scale paths
            for path in v.paths:
                path.scale(0.25)
                # gdspy v1.4 bug: we also need to scale custom path extensions
                # Fixed by gdspy/pull#101 in next release
                if gdspy.__version__ == '1.4':
                    for i, end in enumerate(path.ends):
                        if isinstance(end, tuple):
                            path.ends\[i\] = tuple(\[e*0.25 for e in end\])

            # Scale and move labels
            for label in v.labels:
                # Bug fix for some EDA tools that didn't set MAG field in gds file
                # Maybe this is expected behavior in ASAP7 PDK
                # In gdspy/__init__.py: `kwargs\['magnification'\] = record\[1\]\[0\]`
                label.magnification = 0.25
                label.translate(-label.position\[0\]*0.75, -label.position\[1\]*0.75)

            # Move references (which are scaled if needed)
            for ref in v.references:
                ref.translate(-ref.origin\[0\]*0.75, -ref.origin\[1\]*0.75)

    # Overwrite original GDS file
    gds_lib.write_gds('{gds_file}')
        """.format(cell_list_file=os.path.join(self.cache_dir, 'stdcells.txt'),
                   stdcell_dir=self.get_setting("technology.asap7.stdcell_install_dir"),
                   gds_file=gds_file)

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {"innovus": [
            HammerTool.make_post_persistent_hook("init_design", asap7_innovus_settings),
            HammerTool.make_post_insertion_hook("floorplan_design", asap7_update_floorplan),
            HammerTool.make_post_insertion_hook("write_design", asap7_scale_final_gds)
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
    ''')
    return True

def asap7_update_floorplan(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "asap7_update_floorplan can only run on par"
    assert isinstance(ht, TCLTool), "asap7_update_floorplan can only run on TCL tools"
    """
    This is needed to move the core up by 1 site and re-do wiring tracks.
    This resolves many DRCs and removes the need for the user to do it in placement constraints.
    """
    ht.append('''
# Need to delete and recreate tracks based on tech LEF
add_tracks -honor_pitch

# Create place blockage on bottom row, fixes wiring issue + power vias for LVS
set core_lly [get_db current_design .core_bbox.ll.y]
set botrow [get_db rows -if {.rect.ll.y == $core_lly}]
create_place_blockage -area [get_db $botrow .rect] -name ROW1_BLOCK

# Prevent extending M1 pins in cells
set_db route_design_with_via_in_pin true
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
# Write script out to a temporary file and execute it
set fp [open "{script_file}" "w"]
puts -nonewline $fp "{script_text}"
close $fp

# Innovus <19.1 appends some bad LD_LIBRARY_PATHS, so remove them before executing python
set env(LD_LIBRARY_PATH) [join [lsearch -not -all -inline [split $env(LD_LIBRARY_PATH) ":"] "*INNOVUS*"] ":"]
python3 {script_file}
'''.format(script_text=ht.technology.scale_gds_script(ht.output_gds_filename), script_file=os.path.join(ht.run_dir, "gds_scale.py")))
    return True

tech = ASAP7Tech()
