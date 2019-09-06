#! /usr/bin/python

import os
from sys import argv
from gdsii.library import Library
from gdsii.elements import *
from copy import deepcopy

# Read original GDS (argument is filename)
orig_gds = argv[1]
with open(orig_gds, 'rb') as stream:
    lib = Library.load(stream)

# Define threshold to layer mapping
layermap = {'R': None, 'L': 98, 'SL': 97, 'SRAM': 110}

for vt,num in layermap.items():
    # Make a new copy of the library
    new_lib = deepcopy(lib)

    # Iterate through all cells, change cell name, copy boundary as new Vt layer, and write the GDS
    for cell in new_lib:
        cell.name = cell.name.decode('utf-8').replace('SL', vt).encode('utf-8')
        if num is not None:
            for el in cell:
                if el.layer == 100: #BOUNDARY
                    new_el = deepcopy(el)
                    new_el.layer = num
                    cell.append(new_el)

    # Write to new GDS
    new_gds = os.path.splitext(orig_gds)[0] + '_' + vt + '.gds'
    print("Writing " + new_gds)
    with open(new_gds, 'wb') as stream:
        new_lib.save(stream)
