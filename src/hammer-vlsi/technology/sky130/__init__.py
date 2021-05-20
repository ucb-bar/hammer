#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  SKY130 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os
#import tempfile
#import shutil
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

        # hack tlef
        sky130A = self.get_setting("technology.sky130.sky130A")
        lef_files = self.read_libs([
            hammer_tech.filters.lef_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        tlef_new_path = lef_files[0]
        words = tlef_new_path.split('/')
        tlef_filename = words[-1]
        library_name = tlef_filename.split('.')[0]
        tlef_old_path = os.path.join(sky130A,'libs.ref',library_name,'techlef',tlef_filename)

        f_old = open(tlef_old_path,'r')
        f_new = open(tlef_new_path,'w')
        for line in f_old:
            f_new.write(line)
            if line.strip() == 'END pwell':
                f_new.write('''
LAYER licon
  TYPE CUT ;
END licon
''')
            
        f_old.close()
        f_new.close()
        print('Loaded Sky130 Tech')
        

tech = SKY130Tech()

