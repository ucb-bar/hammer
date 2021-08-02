import json
import os
from pathlib import Path 
data = {}

HAMMER_HOME = os.getenv('HAMMER_HOME')
SKY130A = os.getenv('SKY130A')
JSON_PATH = os.path.join(HAMMER_HOME,'src/hammer-vlsi/technology/sky130/sky130.tech.json')


library='sky130_fd_sc_hd'

with open('beginning.json', 'r') as f:
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
    vdd = vdd.split('v')
    vdd = vdd[0]+'.'+vdd[1]+' V'

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
with open('stackup.json', 'r') as f:
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
with open('sites.json', 'r') as f:
    sites = json.load(f)
data["sites"] = sites["sites"]

with open('sky130.tech.json', 'w') as f:
    json.dump(data, f, indent=2)

with open(os.path.join(JSON_PATH), 'w') as f:
    json.dump(data, f, indent=2)