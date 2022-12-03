'''
    Purpose: generate the json file required by the Hammer Sky130 tech plugin
    Usage:
        export PDK_ROOT=<path-to-dir-containing-sky130-setup>
        python sky130-tech-gen.py
    Output:
        sky130.tech.json: specifies Sky130 PDK file locations and various details
'''

import json
import os
from pathlib import Path 

use_nda_files=True
library='sky130_fd_sc_hd'

PDK_ROOT = os.getenv('PDK_ROOT')
if PDK_ROOT is None:
    print("Error: Must set $PDK_ROOT to the directory that contains skywater-pdk and the root of the sky130A install.")
    exit()
SKY130A = os.path.join(PDK_ROOT, 'share/pdk/sky130A')

if use_nda_files:
    with open('sky130-tech-gen-files/beginning_nda.json', 'r') as f: data = json.load(f)
else:
    with open('sky130-tech-gen-files/beginning.json', 'r') as f: data = json.load(f)

with open('sky130-tech-gen-files/cells.json', 'r') as f:
    cells = json.load(f)
data["physical only cells list"] = cells["physical only cells list"]
data["dont use list"] = cells["dont use list"]
data["special cells"] = cells["special cells"]

SKYWATER_LIBS = os.path.join('$SKY130A','libs.ref',library)
LIBRARY_PATH  = os.path.join(SKY130A,'libs.ref',library,'lib')
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
      "nldm liberty file":  os.path.join(SKYWATER_LIBS,'lib',       cornerfilename),
      "verilog sim":        os.path.join('tech-sky130-cache',       library+'.v'),
      "lef file":           os.path.join(SKYWATER_LIBS,'lef',       library+'.lef'),
      "spice file":         os.path.join('tech-sky130-cache',       library+'.cdl'),
      "gds file":           os.path.join(SKYWATER_LIBS,'gds',       library+'.gds'),
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

with open('../sky130.tech.json', 'w') as f:
    json.dump(data, f, indent=2)