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
import re
import functools

use_nda_files=True

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

    # Standard cells
    library='sky130_fd_sc_hd'
    SKYWATER_LIBS = os.path.join('$SKY130A', 'libs.ref', library)
    LIBRARY_PATH  = os.path.join(  SKY130A,  'libs.ref', library, 'lib')
    lib_corner_files=os.listdir(LIBRARY_PATH)
    lib_corner_files.sort()
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

    # IO cells
    library='sky130_fd_io'
    SKYWATER_LIBS = os.path.join('$SKY130A', 'libs.ref', library)
    LIBRARY_PATH  = os.path.join(  SKY130A,  'libs.ref', library, 'lib')
    lib_corner_files=os.listdir(LIBRARY_PATH)
    lib_corner_files.sort()
    for cornerfilename in lib_corner_files:
        # Skip versions with no internal power
        if ('nointpwr' in cornerfilename) : continue

        tmp = cornerfilename.replace('.lib','')
        # Split into cell, and corner strings
        # Resulting list if only one ff/ss/tt in name: [<cell_name>, <match 'ff'?>, <match 'ss'?>, <match 'tt'?>, <temp & voltages>]
        # Resulting list if ff_ff/ss_ss/tt_tt in name: [<cell_name>, <match 'ff'?>, <match 'ss'?>, <match 'tt'?>, '', <match 'ff'?>, <match 'ss'?>, <match 'tt'?>, <temp & voltages>]
        split_cell_corner = re.split('_(ff)|_(ss)|_(tt)', tmp)
        cell_name = split_cell_corner[0]
        process = split_cell_corner[1:-1]
        temp_volt = split_cell_corner[-1].split('_')[1:]

        # Filter out cross corners (e.g ff_ss or ss_ff)
        if len(process) > 3:
            if not functools.reduce(lambda x,y: x and y, map(lambda p,q: p==q, process[0:3], process[4:]), True):
                continue
        # Determine actual corner
        speed = next(c for c in process if c is not None).replace('_','')
        if (speed == 'ff'): speed = 'fast'
        if (speed == 'tt'): speed = 'typical'
        if (speed == 'ss'): speed = 'slow'

        temp = temp_volt[0]
        temp = temp.replace('n','-')
        temp = temp.split('C')[0]+' C'

        vdd = ('.').join(temp_volt[1].split('v')) + ' V'
        # Filter out IO/analog voltages that are not high voltage
        if temp_volt[2].startswith('1'): continue
        if len(temp_volt) == 4:
            if temp_volt[3].startswith('1'): continue

        # gpiov2_pad_wrapped has separate GDS
        if cell_name == 'sky130_ef_io__gpiov2_pad_wrapped':
            file_lib = 'sky130_ef_io'
            gds_file = cell_name + '.gds'
            lef_file = 'cache/sky130_ef_io.lef'
        elif 'sky130_ef_io' in cell_name:
            file_lib = 'sky130_ef_io'
            gds_file = file_lib + '.gds'
            lef_file = 'cache/' + file_lib + '.lef'
        else:
            file_lib = library
            gds_file = file_lib + '.gds'
            lef_file = os.path.join(SKYWATER_LIBS,'lef', file_lib + '.lef')

        lib_entry = {
            "nldm_liberty_file":  os.path.join(SKYWATER_LIBS,'lib', cornerfilename),
            "verilog_sim":        os.path.join(SKYWATER_LIBS,'verilog', file_lib + '.v'),
            "lef_file":           lef_file,
            "spice_file":         os.path.join(SKYWATER_LIBS,'spice', file_lib + '.spice'),
            "gds_file":           os.path.join(SKYWATER_LIBS,'gds', gds_file),
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
                "lib_type": cell_name,
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
