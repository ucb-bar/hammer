#!/usr/bin/python3

# Scale the final GDS by a factor of 4
# This is called by a tech hook that should be inserted post write_design

import sys, glob, os, re

assert len(sys.argv) == 3, 'Must have 2 arguments: 1) Path to list of standard cells, 2) Path to GDS file'
stdcells = sys.argv[1]
gds_file = sys.argv[2]

try:
    import gdstk
except ImportError:
    try:
        print('gdstk not found, falling back to gdspy...')
        import gdspy
    except ImportError:
        print('Check your gdspy installation!')
        sys.exit()

print('Scaling down place & routed GDS')

# load the standard cell list
cell_list = [line.rstrip() for line in open(stdcells, 'r')]

if 'gdstk' in sys.modules:
    # load original_gds
    gds_lib = gdstk.read_gds(infile=gds_file)
    # Iterate through cells that aren't part of standard cell library and scale
    for cell in list(filter(lambda c: c.name not in cell_list, gds_lib.cells)):
        print('Scaling down ' + cell.name)

        # Need to remove 'blk' layer from any macros, else LVS rule deck interprets it as a polygon
        # This has a layer datatype of 4
        # Then scale down the polygon
        for poly in list(filter(lambda p: p.datatype != 4, cell.polygons)):
            poly.scale(0.25)

        # Scale paths
        for path in cell.paths:
            path.scale(0.25)

        # Scale and move labels
        for label in cell.labels:
            # Bug fix for some EDA tools that didn't set MAG field in gds file
            # Maybe this is expected behavior in ASAP7 PDK
            label.magnification = 0.25
            label.origin = tuple(i * 0.25 for i in label.origin)

        # Move references (which are scaled if needed)
        for ref in cell.references:
            ref.origin = tuple(i * 0.25 for i in ref.origin)

    # Overwrite original GDS file
    gds_lib.write_gds(gds_file)

    # We can also write an SVG of the top cell
    gds_lib.top_level()[0].write_svg(os.path.splitext(gds_file)[0] + '.svg')

    # For Calibre DRC, we need to rename the top cell to 'TOPCELL'
    gds_lib.top_level()[0].name = 'TOPCELL'
    gds_lib.write_gds(os.path.splitext(gds_file)[0] + '_drc.gds')

elif 'gdspy' in sys.modules:
    # load original_gds
    gds_lib = gdspy.GdsLibrary().read_gds(infile=gds_file, units='import')
    # Iterate through cells that aren't part of standard cell library and scale
    for k,v in gds_lib.cell_dict.items():
        if not any(cell in k for cell in cell_list):
            print('Scaling down ' + k)

            # Need to remove 'blk' layer from any macros, else LVS rule deck interprets it as a polygon
            # This has a layer datatype of 4
            # Then scale down the polygon
            v.polygons = [poly.scale(0.25) for poly in v.polygons if not 4 in poly.datatypes]

            # Scale paths
            for path in v.paths:
                path.scale(0.25)
                # gdspy v1.4 bug: we also need to scale custom path extensions
                # Fixed by gdspy/pull#101 in next release
                if gdspy.__version__ == '1.4':
                    for i, end in enumerate(path.ends):
                        if isinstance(end, tuple):
                            path.ends[i] = tuple([e*0.25 for e in end])

            # Scale and move labels
            for label in v.labels:
                # Bug fix for some EDA tools that didn't set MAG field in gds file
                # Maybe this is expected behavior in ASAP7 PDK
                # In gdspy/__init__.py: `kwargs['magnification'] = record[1][0]`
                label.magnification = 0.25
                label.translate(-label.position[0]*0.75, -label.position[1]*0.75)

            # Move references (which are scaled if needed)
            for ref in v.references:
                ref.translate(-ref.origin[0]*0.75, -ref.origin[1]*0.75)

    # Overwrite original GDS file
    gds_lib.write_gds(gds_file)

    # For Calibre DRC, we need to rename the top cell to 'TOPCELL'
    gds_lib.top_level()[0].name = 'TOPCELL'
    gds_lib.write_gds(os.path.splitext(gds_file)[0] + '_drc.gds')
