#!/usr/bin/env python3
# type: ignore
#   tell mypy to ignore this file during typechecking
# -*- coding: utf-8 -*-
#
#  Generate Hammer Sky130 tech plugin file: sky130.tech.json
#
#  See LICENSE for licence details.
import sys
import json
import os

use_nda_files=True
library='sky130_fd_sc_hd'

def main(args) -> int:
    if len(args) != 3:
        print("Usage: ./sky130-tech-gen.py /path/to/sky130A sky130.tech.json")
        return 1

    SKY130A = sys.argv[1]

    if use_nda_files:
        with open('sky130-tech-gen-files/beginning_nda.json', 'r') as f: data = json.load(f)
    else:
        with open('sky130-tech-gen-files/beginning.json', 'r') as f: data = json.load(f)

    with open('sky130-tech-gen-files/cells.json', 'r') as f:
        cells = json.load(f)
    data["physical_only_cells_list"] = cells["physical_only_cells_list"]
    data["dont_use_list"] = cells["dont_use_list"]
    data["special_cells"] = cells["special_cells"]

    SKYWATER_LIBS = os.path.join('$SKY130A', 'libs.ref', library)
    LIBRARY_PATH  = os.path.join(  SKY130A,  'libs.ref', library, 'lib')
    lib_corner_files=os.listdir(LIBRARY_PATH)
    for cornerfilename in lib_corner_files:
        if (not (library in cornerfilename) ) : continue
        if ('ccsnoise' in cornerfilename): continue # ignore duplicate corner.lib/corner_ccsnoise.lib files

        tmp = cornerfilename.replace('.lib','')
        if (tmp+'_ccsnoise.lib' in lib_corner_files): 
            cornerfilename=tmp+'_ccsnoise.lib' # use ccsnoise version of lib file

        cornername = tmp.split('__')[1]
        cornerparts = cornername.split('_')

        speed = cornerparts[0]
        if (speed == 'ff'): speed = 'fast'
        if (speed == 'tt'): speed = 'typical'
        if (speed == 'ss'): speed = 'slow'

        temp = cornerparts[1]
        temp = temp.replace('n','-')
        temp = temp.split('C')[0]+' C'

        vdd = cornerparts[2]
        vdd = vdd.split('v')[0]+'.'+vdd.split('v')[1]+' V'

        lib_entry = {
            "nldm_liberty_file":  os.path.join(SKYWATER_LIBS,'lib', cornerfilename),
            "verilog_sim":        os.path.join('cache',             library+'.v'),
            "lef_file":           os.path.join(SKYWATER_LIBS,'lef', library+'.lef'),
            "spice_file":         os.path.join('cache',             library+'.cdl'),
            "gds_file":           os.path.join(SKYWATER_LIBS,'gds', library+'.gds'),
            "corner": {
                "nmos": speed,
                "pmos": speed,
                "temperature": temp
            },
            "supplies": {
                "VDD": vdd,
                "GND": "0 V"
            },
            "provides": [
                {
                "lib_type": "stdcell",
                "vt": "RVT" 
                }
            ]
        }

        data["libraries"].append(lib_entry)

    with open('sky130-tech-gen-files/stackups.json', 'r') as f:
        stackups = json.load(f)
    data["stackups"] = [stackups]

    with open('sky130-tech-gen-files/sites.json', 'r') as f:
        sites = json.load(f)
    data["sites"] = sites["sites"]

    with open(sys.argv[2], 'w') as f:
        json.dump(data, f, indent=2)
    
    return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv))
