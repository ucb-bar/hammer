#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  asap7 plugin for Hammer.
#
#  See LICENSE for licence details.

import re
import os
import tempfile
import shutil

import gdspy
from hammer_tech import HammerTechnology

class ASAP7Tech(HammerTechnology):
    """
    override the HammerTechnology used in `hammeer_tech.py`
    this class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """
    def post_install_script(self) -> None:
        self.remove_duplication_in_drc_lvs()
        self.generate_multi_vt_gds()
        self.fix_sram_cdl_bug()

    def remove_duplication_in_drc_lvs(self) -> None:
        """
        fix the conflicting in vendor drc/lvs deck between hammer-mentor-plugin.
        """
        self.logger.info("remove LAYOUT PATH|LAYOUT PRIMARY|LAYOUT SYSTEM|DRC RESULTS DATABASE|DRC SUMMARY REPORT|LVS REPORT|LVS POWER NAME|LVS GROUND NAME in DRC/LVS Decks")
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
        vendor only provide SLVT gds, this patch will generate other 3(LVT, RVT, SRAM) VT gds file.
        """
        self.logger.info("generate gds for Multi-VT cells")

        orig_gds = os.path.join(self.extracted_tarballs_dir, "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/gds/asap7sc7p5t_24.gds")
        # load original_gds
        asap7_original_gds = gdspy.GdsLibrary(infile=orig_gds)
        original_cells = asap7_original_gds.cell_dict
        # WTF is this?
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
            multi_lib["lib"].name = asap7_original_gds.name.replace('SL', vt)

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

tech = ASAP7Tech()