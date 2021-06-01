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
#from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

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
        self.setup_techlef()
        self.setup_layermap()
        print('Loaded Sky130 Tech')

    def setup_techlef(self) -> None:
        """ Copy and hack the tech-lef, adding this very important `licon` section """
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        library_name = 'sky130_fd_sc_hd'
        tlef_old_path = setting_dir / 'libs.ref' / library_name / 'techlef' / f'{library_name}.tlef'
        if not tlef_old_path.exists():
            raise FileNotFoundError(f"Tech-LEF not found: {tlef_old_path}")

        cache_tech_dir_path = Path(self.cache_dir) 
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        tlef_new_path = cache_tech_dir_path / f'{library_name}.tlef' 

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

        

_the_tlef_edit = '''
LAYER licon
  TYPE CUT ;
END licon
'''

tech = SKY130Tech()

