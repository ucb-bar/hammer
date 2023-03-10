OpenROAD Place-and-Route Tool Plugin
====================================


Tool Setup
----------

* OpenROAD - install [using conda](https://anaconda.org/litex-hub/openroad) or [from source](https://github.com/The-OpenROAD-Project/OpenROAD#build)
  * we recommend installing from source because the conda package was compiled with the GUI disabled
* KLayout (DEF to GDSII conversion) - install [using conda](https://anaconda.org/litex-hub/klayout) or [from source](https://www.klayout.de/build.html).


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
    global_placement
    io_placement
    resize
    detailed_placement
    
    # CTS
    clock_tree
    clock_tree_resize
    add_fillers
    
    ## ROUTING
    global_route
    global_route_resize
    detailed_route
    
    # FINISHING
    extraction
    write_design


Step Details
------------

A few of the steps are detailed below, mainly to document some details that aren't present in the comments within the plugin.
The plugin (``__init__.py`` and ``defaults.yml``) is still the best reference for what each step does, the explanations below are just more nuanced.


### Macro Placement

At the beginning of the ``floorplan_design`` step, a file called ``macros.txt`` will be generated in ``build/par-rundir`` that lists for each macro: their name/path in the design, master cell name, width/height, and origin (x,y). These may help in setting the ``vlsi.inputs.placement_constraints`` key in your design configuration.

Currently, there are two ways to place macros.

If ``par.openroad.floorplan_mode`` == ``generate`` (default value), use the ``vlsi.inputs.placement_constraints`` key to specify the path and (x,y) coordinate of each macro in the design. The placement constraints for ALL macros must be specified, or OpenROAD will eventually throw an error about an unplaced instance.
Note that the (x,y) position is fixed to the bottom left corner of the macro, then the orientation is applied. This means that for rotations besides ``r0``, the (x,y) position WILL NOT correspond to the bottom left corner of the final placed macro (e.g. the (x,y) position for a macro with orientation ``mx`` will correspond to the top left corner of the final placed macro). To get around this, when ``par.openroad.floorplan_origin_pos`` == ``bottom_left`` (default value), the placement (x,y) coordinates are translated based on the rotation of the macro and the width/height specified in the ``vlsi.inputs.placement_constraints``, so that the (x,y) position specified in ``vlsi.inputs.placement_constraints`` corresponds with the bottom left corner of the final placed macro. If ``par.openroad.floorplan_origin_pos`` == ``rotated``, then the (x,y) position of the macro is not translated.

If ``par.openroad.floorplan_mode`` == ``auto_macro``, you must still use the ``vlsi.inputs.placement_constraints`` key to specify the top-level width/height and margins constraints of the chip, but all macros will be placed automatically using OpenROAD's ``macro_placement`` command, leading to poor-quality but sane results.


### Write Design
OpenROAD uses an external tool called KLayout, which executes a custom Python script ``def2stream.py``
(see ``par.openroad.def2stream_file`` for this file's path)
to write the final design to a GDS file.
This is the same process used in the default VLSI flow from OpenROAD.

Issue Archiving
---------------
This plugin supports generating a ``tar.gz`` archive of the current ``build/par-rundir`` directory with a ``runme.sh`` script to reproduce the results.
This feature is enabled with the ``par.openroad.create_archive_mode`` YAML key, which can take the following values:
* ``none`` - never create an archive (default)
* ``after_error`` - if OpenROAD errors, create an archive of the run
* ``always`` - create an archive after every par run (regardless of whether OpenROAD errors)
* ``latest_run`` - create an archive of latest par run (don't run OpenROAD)
    * useful if OpenROAD gets stuck on endless optimization iterations but never actually "errors"

Creating an archive does the following:
* Generates a issue directory based on the date/time, top module, OS platform
* Dumps the logger output
* Generates a runme.sh script
* Copies .tcl, .sdc, .pdn, and .lef files in par-rundir to the issue dir
* Copies all input Verilog to issue dir
* Copies all input LEFs to issue dir (some may not be used since they are hacked in read_lef())
* Copies all input LIBs to issue dir
* Hacks copied par.tcl script to remove all abspaths
* Hacks copied par.tcl script to comment out write_gds block w/ KLayout
* Tars up issue dir
