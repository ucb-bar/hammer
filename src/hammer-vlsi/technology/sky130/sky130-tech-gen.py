# usage:
#   >> export PDK_ROOT=<path-to-dir-containing-sky130A-dir>
#   >> python sky130-tech-gen.py

import json
import os
from pathlib import Path 

library='sky130_fd_sc_hd'

PDK_ROOT = os.getenv('PDK_ROOT')
if PDK_ROOT is None:
  print("Error: Must set $PDK_ROOT to the directory that contains the sky130A directory.")
  exit()
SKY130A   = os.path.join(PDK_ROOT, 'sky130A')

data = {}
with open('sky130-tech-gen-files/beginning.json', 'r') as f:
    data = json.load(f)

SKYWATER_LIBS = os.path.join('$SKY130A','libs.ref',library)
LIBRARY_PATH  = os.path.join(SKY130A,'libs.ref',library,'lib')
lib_corners=os.listdir(LIBRARY_PATH)
for cornerfilename in lib_corners:
    if (not (library in cornerfilename) ) : continue
    if ('ccsnoise' in cornerfilename): continue 

    tmp = cornerfilename.replace('.lib','__')
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
      "verilog sim":        os.path.join(SKYWATER_LIBS,'verilog',   library+'.v'),
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

stackups = {}
with open('sky130-tech-gen-files/stackup.json', 'r') as f:
    stackups = json.load(f)
stackups["name"] = library
data["stackups"] = [stackups]

# library='sky130_fd_pr'
# SKYWATER_LIBS=os.path.join('$SKY130A',"libs.ref",library)
# lib_entry = {
#   "lef file":           os.path.join(SKYWATER_LIBS,'lef',       library+'.lef'),
#   "spice file":         os.path.join(SKYWATER_LIBS,'cdl',       library+'.cdl'),
#   "gds file":           os.path.join(SKYWATER_LIBS,'gds',       library+'.gds'),
#   "provides": [
#     {
#       "lib_type": "primitives",
#       "vt": "RVT" 
#     }
#   ]
# }
# data["libraries"].append(lib_entry)

sites = {}
with open('sky130-tech-gen-files/sites.json', 'r') as f:
    sites = json.load(f)
data["sites"] = sites["sites"]

with open('sky130.tech.json', 'w') as f:
    json.dump(data, f, indent=2)