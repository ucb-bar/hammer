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
from copy import deepcopy

from gdsii.library import Library
from gdsii.elements import *

from hammer_tech import HammerTechnology

class ASAP7Tech(HammerTechnology):
    def post_install_script(self) -> None:
        self.remove_duplication_in_drc_lvs()
        self.generate_multi_vt_gds()
        self.fix_sram_cdl_bug()

    def remove_duplication_in_drc_lvs(self) -> None:
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
        self.logger.info("generate gds for Multi-VT cells")
        # Read original GDS (argument is filename)
        orig_gds = os.path.join(self.extracted_tarballs_dir, "ASAP7_PDKandLIB.tar/ASAP7_PDKandLIB_v1p5/asap7libs_24.tar.bz2/asap7libs_24/gds/asap7sc7p5t_24.gds")
        with open(orig_gds, 'rb') as stream:
            lib = Library.load(stream)

        # Define threshold to layer mapping
        layermap = {'R': None, 'L': 98, 'SL': 97, 'SRAM': 110}

        for vt,num in layermap.items():
            # Make a new copy of the library
            new_lib = deepcopy(lib)

            # Iterate through all cells, change cell name, copy boundary as new Vt layer, and write the GDS
            for cell in new_lib:
                cell.name = cell.name.decode('utf-8').replace('SL', vt).encode('utf-8')
                if num is not None:
                    for el in cell:
                        if el.layer == 100: #BOUNDARY
                            new_el = deepcopy(el)
                            new_el.layer = num
                            cell.append(new_el)

            # Write to new GDS
            new_gds = os.path.splitext(orig_gds)[0] + '_' + vt + '.gds'
            with open(new_gds, 'wb') as stream:
                new_lib.save(stream)

    def fix_sram_cdl_bug(self) -> None:
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