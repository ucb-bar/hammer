#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  SKY130 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os
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

        # hack tlef, adding this very important `licon` section 
        setting_dir = self.get_setting("technology.sky130.open_pdks")
        setting_dir = Path(setting_dir)
        library_name = 'sky130_fd_sc_hd'
        tlef_old_path = setting_dir / 'sky130'/ 'sky130A' / 'libs.ref' / library_name / 'techlef' / f'{library_name}.tlef'
        if not tlef_old_path.exists():
            raise FileNotFoundError(f"Tech-LEF not found: {tlef_old_path}")

        cache_tech_dir_path = Path(self.cache_dir) / 'techlef'
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
        print('Loaded Sky130 Tech')
        

_the_tlef_edit = '''
LAYER licon
  TYPE CUT ;
END licon
'''

tech = SKY130Tech()

