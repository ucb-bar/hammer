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

library='sky130_fd_sc_hd'

def main(args) -> int:
    if len(args) != 3:
        print("Usage: ./stackups-gen.py /path/to/sky130A stackups.json")
        return 1

    SKY130A = sys.argv[1]

    stackup = {}
    stackup["name"] = library
    stackup["grid_unit"] = 0.001
    stackup["metals"] = []

    def is_float(string):
        try:
            float(string)
            return True
        except ValueError:
            return False

    def get_min_from_line(line):
        words = line.split()
        nums = [float(w) for w in words if is_float(w)]
        return min(nums)
    

    tlef_path = os.path.join(SKY130A, 'libs.ref', library, 'techlef', f"{library}__min.tlef")
    with open(tlef_path, 'r') as f:
        metal_name = None
        metal_index = 0
        lines = f.readlines()
        idx = -1
        while idx < len(lines):
            idx += 1
            if idx == len(lines) - 1: break
            line = lines[idx]
            if '#' in line: line = line[:line.index('#')]
            words = line.split()
            if line.startswith('LAYER') and len(words) > 1:
                if words[1].startswith('li') or words[1].startswith('met'):
                    metal_name = words[1]
                    metal_index += 1
                    metal = {}
                    metal["name"] = metal_name
                    metal["index"] = metal_index
                    
            if metal_name is not None:
                line = line.strip()
                if line.startswith("DIRECTION"):
                    metal["direction"] = words[1].lower()
                if line.startswith("PITCH"):
                    metal["pitch"] = get_min_from_line(line)
                if line.startswith("OFFSET"):
                    metal["offset"] = get_min_from_line(line)
                if line.startswith("WIDTH"):
                    metal["min_width"] = get_min_from_line(line)
                if line.startswith("SPACINGTABLE"):
                    metal["power_strap_widths_and_spacings"] = []
                    while ';' not in line:
                        idx += 1
                        if idx == len(lines) - 1: break
                        line = lines[idx].strip()
                        if '#' in line: line = line[:line.index('#')]
                        words = line.split()
                        d = {}
                        if line.startswith("WIDTH"):
                            d["width_at_least"] = float(words[1])
                            d["min_spacing"] = float(words[2])
                            metal["power_strap_widths_and_spacings"].append(d.copy())
                if line.startswith("END"):
                    metal["grid_unit"] = 0.001
                    stackup["metals"].append(metal.copy())
                    metal_name = None
            

    with open(sys.argv[2], 'w') as f:
        json.dump(stackup, f, indent=2)
    
    return 0

if __name__ == '__main__':
  sys.exit(main(sys.argv))
