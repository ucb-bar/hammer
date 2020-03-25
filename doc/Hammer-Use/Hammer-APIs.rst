.. _hammer-apis:

Hammer APIs
===========

Hammer has a growing collection of APIs that use objects defined by the technology plugin, such as stackups and special cells. They expose useful extracted information from Hammer IR to other methods, such as in tool plugins that will implement this information in a tool-compatible manner.

For syntax details about the Hammer IR needed to use these APIs, refer to the `defaults.yml <https://github.com/ucb-bar/hammer/blob/master/src/hammer-vlsi/defaults.yml>`__.

Power Specification
-------------------
Simple power specs are specified using the Hammer IR key ``vlsi.inputs.supplies``, which is then translated into a a Supply object. ``hammer_vlsi_impl`` exposes the Supply objects to other APIs (e.g. power straps) and can generate the CPF/UPF files depending on which specification the tools support. Multi-mode multi-corner (MMMC) setups are also available by setting ``vlsi.inputs.mmmc_corners`` and manual power spec definitions are supported by setting the relevant ``vlsi.inputs.power_spec...`` keys.

Timing Constraints
------------------
Clock and pin timing constraints are specified using the Hammer IR keys ``vlsi.inputs.clocks/output_loads/delays``. These objects can be turned into SDC-style constraints by ``hammer_vlsi_impl`` for consumption by supported tools.

Floorplan & Placement
---------------------
Placement constraints are specified using the Hammer IR key ``vlsi.inputs.placement_constraints``. These constraints are very flexible and have varying inputs based on the type of object the constraint applies to, such as hierarchical modules, hard macros, or obstructions. At minimum, an ``(x, y)`` coordinate corresponding to the lower left corner must be given, and additional parameters such as width/height, margins, layers, or orientation are needed depending on the type of constraint. Place-and-route tool plugins will take this information and emit the appropriate commands during floorplanning. Additional work is planned to ensure that floorplans are always legal (i.e. on grid, non-overlapping, etc.).

All Hammer tool instances have access to a method that can produce graphical visualization of the floorplan as an SVG file, viewable in a web browser. To use it, call the ``generate_visualization()`` method from any custom hook (see :ref:`hooks`). The options for the visualization tool are in the Hammer IR key ``vlsi.inputs.visualization``.

Bumps
-----
Bump constraints are specified using the Hammer IR key ``vlsi.inputs.bumps``. Rectangular-gridded bumps are supported, although bumps at fractional coordinates in the grid and deleted bumps are allowed. The place-and-route tool plugin translates the list of bump assignments into the appropriate commands to place them in the floorplan and enable flip-chip routing. The bumps API is also used by the PCB plugin to emit the collateral needed by PCB layout tools such as Altium Designer. This API ensures that the bumps are always in correspondence between the chip and PCB.

The visualization tool mentioned above can also display bump placement and assignments. There are options to view the bumps from the perspective of the ASIC designer or the PCB designer. The views are distinguishable by a reference dot displayed in the left and right corners for the ASIC and PCB perspectives, respectively.

Pins
----
Pin constraints are specified using the Hammer IR key ``vlsi.inputs.pin``. PinAssignments objects are generated and passed to the place-and-route tool to place pins along specified block edges on specified metal layers. Preplaced (e.g. hard macros in hierarchical blocks) pins are also supported so that they are not routed. Additional work is planned to use this API in conjunction with the placement constraints API to allow for abutment of hierarchical blocks, which requires pins to be aligned on abutting edges.

Power Straps
------------
Power strap constraints are specified using multiple Hammer IR keys in the ``par`` namespace. The currently supported API supports power strap generation by tracks, which auto-calculates power strap width, spacing, set-to-set distance, and offsets based on basic DRC rules specified in the technology Stackup object. The basic pieces of information needed are the desired track utilization per strap and overall power strap density. Different values can be specified on a layer-by-layer basis by appending ``_<layer name>`` to the end of the desired option.

Special Cells
-------------
Special cells are specified in the technology's JSON, but are exposed to provide lists of cells needed for certain steps, such as for fill, well taps, and more. Synthesis and place-and-route tool plugins can grab the appropriate type of special cell for the relevant steps.

Submission
----------
Each tool has run submission options given by the Hammer IR key ``<tool type>.submit``. Using the ``command`` and ``settings`` keys, a setup for LSF or similar workload management platforms can be standardized.
