OpenROAD Place-and-Route Tool Plugin
====================================


Tool Setup
----------

First, follow [these directions](https://github.com/The-OpenROAD-Project/OpenROAD#build) to build and install OpenROAD.



Tool Steps
----------

See ``__init__.py`` for the implementation of these steps.

    # INITIALIZE
    init_design
    
    # FLOORPLAN
    floorplan_design
    place_bumps
    macro_placement
    place_tapcells 
    power_straps 
   
    # PLACE
    initial_global_placement
    io_placement
    global_placement
    resize
    detailed_placement
    
    # CTS
    clock_tree
    add_fillers 
    ## ROUTING
    global_route
    detailed_route
    
    # FINISHING
    extraction
    write_design


Step Details
------------

A few of the steps are detailed below, mainly to document some details that aren't present in the comments within the plugin.
The plugin is still the best reference for what each step does, the explanations below are just more nuanced.


### Macro Placement

Currently, there are two ways to place macros.

If ``par.openroad.floorplan_mode`` == ``generate``, use the ``vlsi.inputs.placement_constraints`` key to specify the path and (x,y) coordinate of each macro in the design. The placement constraints for ALL macros must be specified, or OpenROAD will eventually throw an error about an unplaced instance.
Note that the (x,y) position is fixed to the bottom left corner of the macro, then the orientation is applied. This means that for rotations besides ``r0``, the (x,y) position WILL NOT correspond to the bottom left corner of the final placed macro (e.g. the (x,y) position for a macro with orientation ``mx`` will correspond to the top left corner of the final placed macro).

If ``par.openroad.floorplan_mode`` == ``auto``, the macros will be placed automatically using OpenROAD's ``macro_placement`` command, leading to poor-quality but sane results.


### Detailed Route

This is by far the most time-consuming step.
For context, on a 16-core machine running one thread per core, 
a small RISC-V CPU with caches and a few digital peripherals, from
[this tutorial in Chipyard](https://chipyard.readthedocs.io/en/stable/VLSI/Sky130-OpenROAD-Tutorial.html),
takes several hours.

### Write Design
OpenROAD uses an external tool called KLayout, which executes a custom Python script (``def2stream.py``)
to write the final design to a GDS file.
This is the same process used in the default VLSI flow from OpenROAD.

