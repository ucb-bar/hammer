#!/usr/bin/env python3

import sys
import os
import re

if len(sys.argv) != 3:
    print("Usage: ./sram-cache-gen.py list-of-srams-1-per-line.txt output-file.json")
    exit(1)

list_of_srams = []
with open(sys.argv[1]) as f:
    for line in f:
        list_of_srams.append(line)

json = []

for sram_name in list_of_srams:
    if sram_name.startswith("SRAM2RW"):
        m = re.match("SRAM2RW(\d+)x(\d+)", sram_name)
        if m:
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
}}
  """.format(n=sram_name.strip(), d=m.group(1), w=m.group(2)))
        else:
            print("Unsupported memory: {n}".format(n=sram_name))
    elif sram_name.startswith("SRAM1RW"):
        m = re.match("SRAM1RW(\d+)x(\d+)", sram_name)
        if m:
            json.append("""
{{
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
}}
  """.format(n=sram_name.strip(), d=m.group(1), w=m.group(2)))
        else:
            print("Unsupported memory: {n}".format(n=sram_name))
    else:
        print("Unsupported memory: {n}".format(n=sram_name))

with open(sys.argv[2], "w") as f:
    f.write("[\n")
    for i in range(0, len(json)):
        f.write(json[i])
        if i != (len(json) - 1):
            f.write(",")
    f.write("]\n")

