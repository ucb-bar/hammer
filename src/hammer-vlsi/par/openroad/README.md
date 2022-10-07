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
The first is to use the ``vlsi.inputs.placement_constraints`` key to specify the path and (x,y) coordinate of each macro in the design.
The alternative method is to not specify any macro placement, which will cause them to be placed automatically, leading to poor-quality but sane results.

The plugin will first honor all macro placements specified in ``vlsi.inputs.placement_constraints``,
then will run the ``macro_placement`` command anyways to place any remaining macros in the design.
Thus OpenROAD should never throw an error for having unplaced macros, as they all get placed eventually.
The reasoning here is that with frequent alterations to the RTL, manually specifying the new macro
paths and locations becomes tedious.

In the future, the ``par.openroad.floorplan_mode`` should be used to set whether to do floorplanning this way,
or throw an error for unplaced macros.

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

