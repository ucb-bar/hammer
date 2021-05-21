#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to generate the SRAM cache.
See LICENSE for licence details.

As of publication-time, in Sky130, you should not use this script **at all**. 

The `sram-cache.json` is hand-crafted to work through peculiarites 
that get ChipYard to play nice with one (and only one) OpenRAM-generated Sky130 SRAM. 

This script is here nonetheless for future work, 
to be updated so that it might expand to more SRAMs later. 

Sources of SRAM comprehended by this script include:
* The OpenRAM/ eFabless generated macros available at https://github.com/efabless/sky130_sram_macros
* DFFRAM's flip-flop/latch based macros availabe at https://github.com/Cloud-V/DFFRAM

Note to date *ChipYard*, particularly its macro-compiler/selector, 
does not comprehend the interface to the latter. 

Prior editions of scripts similar to this have read macro-names 
from a text file. Given the near-complete difference between handling 
of the OpenRAM and DFFRAM circuits, this version has to pretend to 
discern which is which from their names in said text file. 
(So, just put these things in edits to the script instead.) 

"""
import sys
import re

from typing import List
srams_dot_txt = """
sky130_sram_1kbyte_1rw1r_32x256_8
sky130_sram_1kbyte_1rw1r_8x1024_8
sky130_sram_2kbyte_1rw1r_32x512_8
sky130_sram_4kbyte_1rw1r_32x1024_8
sky130_sram_8kbyte_1rw1r_32x2048_8
"""

def main(args: List[str]) -> int:
    if len(args) != 3:
        print("Usage: ./sram-cache-gen.py output-file.json")
        print("E.g.: ./sram-cache-gen.py sram-cache.json")
        return 1

    list_of_srams = srams_dot_txt.split("\n")

    print(str(len(list_of_srams)) + " SRAMs to cache")

    json = []  # type: List[str]

    for sram_name in list_of_srams:
        # DFFRAM-generated 1-port rams
        if sram_name.startswith("RAM"):
            match = re.match(r"RAM(\d+)x(\d+)", sram_name)
            if match:
                json.append("""{{
  "type" : "sram",
  "name" : "{n}",
  "depth" : "{d}",
  "width" : {w},
  "family" : "1rw",
  "mask" : "true",
  "ports" : [ {{
    "address port name" : "A",
    "address port polarity" : "active high",
    "clock port name" : "CLK",
    "clock port polarity" : "positive edge",
    "output port name" : "Do",
    "output port polarity" : "active high",
    "input port name" : "Di",
    "input port polarity" : "active high",
    "chip enable port name" : "EN",
    "chip enable port polarity" : "active high",
    "mask port name" : "WE",
    "mask port polarity" : "active high",
    "mask granularity" : 8
  }} ],
  "extra ports" : []
}}""".format(n=sram_name.strip(), d=match.group(1), w=match.group(2)))
            else:
                print("Unsupported memory: {n}".format(n=sram_name), file=sys.stderr)
                return 1
        # OpenRAM-generated 2-port rams
        elif sram_name.startswith("sky130_sram"):
            match = re.match(r"sky130_sram_(\d+)kbyte_1rw1r_(\d+)x(\d+)_(\d+)", sram_name)
            if match:
                json.append("""
{{
  "type" : "sram",
  "name" : "{n}",
  "depth" : "{d}",
  "width" : {w},
  "family" : "1rw1r",
  "mask" : "true",
  "ports": [ {{
    "address port name" : "addr0",
    "address port polarity" : "active high",
    "clock port name" : "clk0",
    "clock port polarity" : "positive edge",
    "write enable port name" : "web0",
    "write enable port polarity" : "active low",
    "output port name" : "dout0",
    "output port polarity" : "active high",
    "input port name" : "din0",
    "input port polarity" : "active high",
    "chip enable port name" : "csb0",
    "chip enable port polarity" : "active low",
    "mask port name" : "wmask0",
    "mask port polarity" : "active high",
    "mask granularity" : 8
  }}, {{
    "address port name" : "addr1",
    "address port polarity" : "active high",
    "clock port name" : "clk1",
    "clock port polarity" : "positive edge",
    "output port name" : "dout1",
    "output port polarity" : "active high",
    "chip enable port name" : "csb1",
    "chip enable port polarity" : "active low"
  }} ],
  "extra ports" : []
}}""".format(n=sram_name.strip(), w=match.group(2), d=match.group(3), m=match.group(4)))
            else:
                print("Unsupported memory: {n}".format(n=sram_name), file=sys.stderr)
                return 1
        else:
            print("Unsupported memory: {n}".format(n=sram_name), file=sys.stderr)
            return 1

    json_str = "[\n" + ",\n".join(json) + "]\n"

    with open(sys.argv[2], "w") as f:
        f.write(json_str)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
