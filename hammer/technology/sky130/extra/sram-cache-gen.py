#  Script to generate the ASAP7 dummy SRAM cache.
#
#  See LICENSE for licence details.

import sys
import re

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
    "mask granularity" : {m}
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
