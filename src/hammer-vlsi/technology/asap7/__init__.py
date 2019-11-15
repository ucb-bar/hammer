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
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

from hammer_tech import HammerTechnology
from hammer_vlsi import HammerTool, HammerPlaceAndRouteTool, CadenceTool, HammerToolHookAction

class ASAP7Tech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """
    def post_install_script(self) -> None:
        try:
            import gdspy  # type: ignore
        except ImportError:
            self.logger.error("Check your gdspy installation! Unable to hack ASAP7 PDK.")
            shutil.rmtree(self.cache_dir)
            sys.exit()
        self.remove_duplication_in_drc_lvs()
        self.generate_multi_vt_gds()
        self.fix_sram_cdl_bug()

    def remove_duplication_in_drc_lvs(self) -> None:
        """
        Remove conflicting specification statements found in PDK's DRC & LVS decks.
        """
        self.logger.info("Remove LAYOUT PATH|LAYOUT PRIMARY|LAYOUT SYSTEM|DRC RESULTS DATABASE|DRC SUMMARY REPORT|LVS REPORT|LVS POWER NAME|LVS GROUND NAME in DRC/LVS Decks")
        ruledirs = os.path.join(self.extracted_tarballs_dir, "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7PDK_r1p5.tar.bz2/asap7PDK_r1p5/calibre/ruledirs")
        drc_deck = os.path.join(ruledirs, "drc/drcRules_calibre_asap7_171111a.rul")
        lvs_deck = os.path.join(ruledirs, "lvs/lvsRules_calibre_asap7_160819a.rul")
        pattern = re.compile(".*(LAYOUT\ PATH|LAYOUT\ PRIMARY|LAYOUT\ SYSTEM|DRC\ RESULTS\ DATABASE|DRC\ SUMMARY\ REPORT|LVS\ REPORT|LVS\ POWER NAME|LVS\ GROUND\ NAME).*\n")
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            with open(drc_deck, 'r') as f:
                tf.write(pattern.sub("", f.read()).encode('utf-8'))
            shutil.copystat(drc_deck, tf.name)
            shutil.copy(tf.name, drc_deck)

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            with open(lvs_deck, 'r') as f:
                tf.write(pattern.sub("", f.read()).encode('utf-8'))
            shutil.copystat(lvs_deck, tf.name)
            shutil.copy(tf.name, lvs_deck)

    def generate_multi_vt_gds(self) -> None:
        """
        PDK GDS only contains SLVT cells.
        This patch will generate the other 3(LVT, RVT, SRAM) VT GDS files.
        """
        import gdspy # TODO: why did module import get lost above for some users?

        self.logger.info("Generate GDS for Multi-VT cells")

        orig_gds = os.path.join(self.extracted_tarballs_dir, "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/gds/asap7sc7p5t_24.gds")
        # load original_gds
        asap7_original_gds = gdspy.GdsLibrary().read_gds(infile=orig_gds, units='import')
        original_cells = asap7_original_gds.cell_dict
        # This is an extra cell in the original GDS that has no geometry inside
        del original_cells['m1_template']
        # required libs
        multi_libs = {
            "R": {
                "lib": gdspy.GdsLibrary(),
                "mvt_layer": None,
                },
            "L": {
                "lib": gdspy.GdsLibrary(),
                "mvt_layer": 98
                },
            "SL": {
                "lib": gdspy.GdsLibrary(),
                "mvt_layer": 97
                },
            "SRAM": {
                "lib": gdspy.GdsLibrary(),
                "mvt_layer": 110
                },
        }
        # create new libs
        for vt, multi_lib in multi_libs.items():
            multi_lib['lib'].name = asap7_original_gds.name.replace('SL', vt)

        for cell in original_cells.values():
            poly_dict = cell.get_polygons(by_spec=True)
            # extract polygon from layer 100(the boundary for cell)
            boundary_polygon = poly_dict[(100, 0)]
            for vt, multi_lib in multi_libs.items():
                mvt_layer = multi_lib['mvt_layer']
                if mvt_layer:
                    # copy boundary_polygon to mvt_layer to mark the this cell is a mvt cell.
                    mvt_polygon = gdspy.PolygonSet(boundary_polygon, multi_lib['mvt_layer'], 0)
                    mvt_cell = cell.copy(name=cell.name.replace('SL', vt), exclude_from_current=True, deep_copy=True).add(mvt_polygon)
                else:
                    # RVT, just copy the cell
                    mvt_cell = cell.copy(name=cell.name.replace('SL', vt), exclude_from_current=True, deep_copy=True)
                # add mvt_cell to corresponding multi_lib
                multi_lib['lib'].add(mvt_cell)

        for vt, multi_lib in multi_libs.items():
            # write multi_lib
            multi_lib['lib'].write_gds(os.path.splitext(orig_gds)[0] + '_' + vt + '.gds')

    def fix_sram_cdl_bug(self) -> None:
        """
        vendor's SRAM cdl use slvt cell, this patch will sed cells name in which, fix this bug.
        """
        self.logger.info("sed slvt to sram in asap7_75t_SRAM.cdl")
        pattern0 = re.compile("SL")
        pattern1 = re.compile("slvt")

        with tempfile.NamedTemporaryFile(delete=False) as tf:
            sram_cdl = os.path.join(self.extracted_tarballs_dir, "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/cdl/lvs/asap7_75t_SRAM.cdl")
            with open(sram_cdl, 'r') as f:
                tf.write(pattern1.sub("sram", pattern0.sub("SRAM", f.read())).encode('utf-8'))
            shutil.copystat(sram_cdl, tf.name)
            shutil.copy(tf.name, sram_cdl)

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

import sys

try:
    import gdspy
    print('Scaling down place & routed GDS')
except ImportError:
    print('Check your gdspy installation!')
    sys.exit()

# load the standard cell list from the gds folder and lop off '_SL' from end
cell_list = \[line.strip()\[:-3\] for line in open('{cell_list_file}', 'r')\]

# Need to remove blk layer from any macros, else LVS rule deck interprets it as a polygon
blockage_datatype = 4

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
            # gdspy bug: we also need to scale custom path extensions
            # Will be fixed by gdspy/pull#101 in next release
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

        # Scale and move references
        for ref in v.references:
            ref.magnification = 0.25
            ref.translate(-ref.origin\[0\]*0.75, -ref.origin\[1\]*0.75)
            ref.magnification = 1

# Overwrite original GDS file
gds_lib.write_gds('{gds_file}')
        """.format(cell_list_file=os.path.join(self.extracted_tarballs_dir, 'ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/gds/cell_list.txt'), gds_file=gds_file)

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {"innovus": [
            HammerTool.make_post_persistent_hook("init_design", asap7_innovus_settings),
            HammerTool.make_post_insertion_hook("write_design", scale_final_gds)
            ]}
        return hooks.get(tool_name, [])

def asap7_innovus_settings(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, CadenceTool), "Innovus is Cadence"
    """Settings that may need to be reapplied at every tool invocation
    Note that the particular routing layer settings here will persist in Innovus;
    this hook only serves as an example of what commands may need to persist."""
    ht.append('''
set_db route_design_bottom_routing_layer 2
set_db route_design_top_routing_layer 7
    ''')
    return True

def scale_final_gds(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "scale_final_gds can only run on par"
    assert isinstance(ht, CadenceTool), "scale_final_gds is only for the Cadence Tcl interpreter"
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
