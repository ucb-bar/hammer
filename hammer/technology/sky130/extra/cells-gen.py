'''
    Purpose: generate list of standard cells in skywater library
    Usage: 
        export PDK_ROOT=<path-to-dir-containing-sky130-setup>
        python cells-gen.py
    Output:
        cells.txt: list of all cell names, one per line.
'''
import os
PDK_ROOT = os.getenv('PDK_ROOT')
if PDK_ROOT is None:
    print("Error: Must set $PDK_ROOT to the directory that contains skywater-pdk and the root of the sky130A install.")
    exit()

SKYWATER_PDK = os.path.join(PDK_ROOT, 'skywater-pdk/libraries/sky130_fd_sc_hd/latest/cells')
cells = os.listdir(SKYWATER_PDK)
cell_names = []
for cell in cells:
    files = os.listdir(os.path.join(SKYWATER_PDK,cell))
    for f in files:
        if '.gds' in f:
            cell_name = f.split('.')[0]
            cell_names.append(cell_name)

with open('cells.txt', 'w') as cells_file:
    for cell_name in cell_names:
        cells_file.write(cell_name+'\n')