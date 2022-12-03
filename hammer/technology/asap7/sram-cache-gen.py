#!/usr/bin/env python3
#  Script to generate the ASAP7 dummy SRAM cache.
#
#  See LICENSE for licence details.

import sys
import re

from typing import List

def main(args: List[str]) -> int:
    if len(args) != 3:
        print("Usage: ./sram-cache-gen.py list-of-srams-1-per-line.txt output-file.json")
        return 1

    list_of_srams = []  # type: List[str]
    with open(sys.argv[1]) as f:
        for line in f:
            list_of_srams.append(line)

    json = []  # type: List[str]

    for sram_name in list_of_srams:
        if sram_name.startswith("SRAM2RW"):
            match = re.match(r"SRAM2RW(\d+)x(\d+)", sram_name)
            if match:
                json.append("""
{{
  "type" : "sram",
  "name" : "{n}",
  "vt" : "SRAM",
  "depth" : "{d}",
  "width" : {w},
  "mux" : 1,
  "family" : "2RW",
  "mask" : "false",
  "ports": [ {{
    "address port name" : "A1",
    "address port polarity" : "active high",
    "clock port name" : "CE1",
    "clock port polarity" : "positive edge",
    "write enable port name" : "WEB1",
    "write enable port polarity" : "active low",
    "read enable port name" : "OEB1",
    "read enable port polarity" : "active low",
    "output port name" : "O1",
    "output port polarity" : "active high",
    "input port name" : "I1",
    "input port polarity" : "active high",
    "chip enable port name" : "CSB1",
    "chip enable port polarity" : "active low"
  }}, {{
    "address port name" : "A2",
    "address port polarity" : "active high",
    "clock port name" : "CE2",
    "clock port polarity" : "positive edge",
    "write enable port name" : "WEB2",
    "write enable port polarity" : "active low",
    "read enable port name" : "OEB2",
    "read enable port polarity" : "active low",
    "output port name" : "O2",
    "output port polarity" : "active high",
    "input port name" : "I2",
    "input port polarity" : "active high",
    "chip enable port name" : "CSB2",
    "chip enable port polarity" : "active low"
  }} ],
  "extra ports" : []
}}""".format(n=sram_name.strip(), d=match.group(1), w=match.group(2)))
            else:
                print("Unsupported memory: {n}".format(n=sram_name), file=sys.stderr)
                return 1
        elif sram_name.startswith("SRAM1RW"):
            match = re.match(r"SRAM1RW(\d+)x(\d+)", sram_name)
            if match:
                json.append("""{{
  "type" : "sram",
  "name" : "{n}",
  "vt" : "SRAM",
  "depth" : "{d}",
  "width" : {w},
  "mux" : 1,
  "family" : "1RW",
  "mask" : "false",
  "ports" : [ {{
    "address port name" : "A",
    "address port polarity" : "active high",
    "clock port name" : "CE",
    "clock port polarity" : "positive edge",
    "write enable port name" : "WEB",
    "write enable port polarity" : "active low",
    "read enable port name" : "OEB",
    "read enable port polarity" : "active low",
    "output port name" : "O",
    "output port polarity" : "active high",
    "input port name" : "I",
    "input port polarity" : "active high",
    "chip enable port name" : "CSB",
    "chip enable port polarity" : "active low"
  }} ],
  "extra ports" : []
}}""".format(n=sram_name.strip(), d=match.group(1), w=match.group(2)))
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
