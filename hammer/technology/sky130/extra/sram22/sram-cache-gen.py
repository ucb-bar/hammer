#!/usr/bin/env python3
# type: ignore
#   tell mypy to ignore this file during typechecking
# -*- coding: utf-8 -*-
#
#  Script to generate the SRAM22 sram-cache.json
#
#  See LICENSE for licence details.

import sys
import re
import json

from typing import List

def main(args: List[str]) -> int:
    if len(args) != 3:
        print("Usage: ./sram-cache-gen.py list-of-srams-1-per-line.txt output-file.json")
        print("E.g.: ./sram-cache-gen.py srams.txt sram-cache.json")
        return 1

    list_of_srams = []  # type: List[str]
    with open(sys.argv[1]) as f:
        for line in f:
            list_of_srams.append(line)

    print(str(len(list_of_srams)) + " SRAMs to cache")

    sram_dicts = []

    for sram_name in list_of_srams:
        # SRAM22-generated single-port RAMs
        if sram_name.startswith("sram22_"):
            match = re.match(r"sram22_(\d+)x(\d+)m(\d+)w(\d+)(\D*)", sram_name)
            if match:
                width = int(match.group(2))
                mask_gran = int(match.group(4))
                
                sram_dict = {}
                sram_dict['type'] = 'sram'
                sram_dict['name'] = sram_name.strip()
                sram_dict['source'] = 'sram22'
                sram_dict['depth'] = match.group(1)
                sram_dict['width'] = width
                sram_dict['family'] = '1rw'
                sram_dict['mask'] = "true"
                sram_dict['vt'] = 'svt'
                sram_dict['mux'] = int(match.group(3))
                sram_dict['ports'] = []

                port_dict = {}
                port_dict['address port name'] = "addr"
                port_dict['address port polarity'] = "active high"
                
                port_dict['clock port name'] = "clk"
                port_dict['clock port polarity'] = "active high"

                port_dict['write enable port name'] = "ce"
                port_dict['write enable port polarity'] = "active high" # ???

                port_dict['write enable port name'] = "we"
                port_dict['write enable port polarity'] = "active high" # ???

                port_dict['output port name'] = "dout"
                port_dict['output port polarity'] = "active high"

                port_dict['input port name'] = "din"
                port_dict['input port polarity'] = "active high"
                
                port_dict['mask port name'] = "wmask"
                port_dict['mask granularity'] = mask_gran
                port_dict['mask port polarity'] = "active high"  # ???
                
                sram_dict['ports'].append(port_dict.copy())

                sram_dict['extra_ports'] = [{
                    "name": "rstb",
                    "width": 1,
                    "type": "constant",
                    "value": 1,
                }]

                sram_dicts.append(sram_dict.copy())
            
            else:
                print("Unsupported memory: {n}".format(n=sram_name), file=sys.stderr)
                return 1
        else:
            print("Unsupported memory: {n}".format(n=sram_name), file=sys.stderr)
            return 1

    with open(sys.argv[2], "w") as f:
        json.dump(sram_dicts, f, indent=2)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
