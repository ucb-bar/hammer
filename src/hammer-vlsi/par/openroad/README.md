OpenROAD Place-and-Route Tool Plugin
====================================


Tool Setup
----------

TODO: link the tool setup here



Tool Steps
----------

TODO: maybe describe each step here?

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



Macro Placement
---------------

TODO: describe how floorplanning constraints work vs ``maco_placement``


Detailed Route
--------------
By far the most time-consuming step.


Write Design
------------
TODO: describe klayout, limitations there
