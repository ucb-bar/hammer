.. _par:

Place-and-Route 
===============================

Hammer has an action for placing and routing a synthesized design.
This action requires a tool plugin to implement ``HammerPlaceAndRouteTool``.

P&R Setup Keys
--------------

* Namespace: ``vlsi.core``

    * ``par_tool_path``

        * Set to the directory containing the tool plugin directory for the place-and-route tool, typically ``/path/to/tool_plugin/par``. This will be the parent directory of the directory containing ``__init__.py`` and ``defaults.yml``.

    * ``par_tool``
        
        * Actual name of the P&R tool that is setup in the directory, ``par_tool_path``, e.g. ``innovus``


P&R Input Keys
--------------

* Namespace: ``vlsi`` 
  
    * These are built-in Hammer APIs covered in :ref:`hammer-apis`

* Namespace: ``par``

    * ``inputs.input_files`` ([])
        
        * List of paths to post-synthesis netlists. Auto-populated after syn-to-par.

    * ``inputs.top_module`` (str)

        * Name of top RTL module to P&R. Auto-populated after syn-to-par.

    * ``inputs.post_synth_sdc`` (str)

        * Post-synthesis generated SDC. Auto-populated after syn-to-par.

    * ``inputs.gds_map_mode`` (str)
    
        * Specify which GDS layermap file to use. ``auto`` uses the technology-supplied file, whereas ``manual`` requires a file to specified via ``inputs.gds_map_file``.

    * ``inputs.gds_merge`` (bool)

        * ``True`` tells the P&R tool to merge all library & macro GDS before streamout. Otherwise, only references will exist and merging needs to be done later, by a tool such as ``Calibre``, ``gdstk``, or ``gdspy``.

    * ``inputs.physical_only_cells_mode`` (str)

        * Specifies which set of cells to exclude from SPICE netlist because they have no logical function. ``auto`` uses the technology-supplied list, whereas ``manual`` and ``append`` overrides and appends to the supplied list, respectively.

    * ``submit`` (dict)

        * Can override global settings for submitting jobs to a workload management platform.

    * ``power_straps_mode`` (str)
        
        * Power straps configuration. ``generate`` enables Hammer's power straps API, whereas ``manual`` requires a TCL script in ``power_straps_script_contents``.

    * ``blockage_spacing`` (Decimal)

        * Global obstruction around every hierarchical sub-block and hard macro

    * ``generate_power_straps_options`` (dict)

        * If ``generate_power_straps_method`` is ``by_tracks``, this struct specifies all the options for the power straps API. See :ref:`hammer-apis` for more detail.

P&R Inputs
----------
There are no other prerequisites to running place & route other than setting the keys described above.

P&R Outputs
-----------

* Hierarchical (e.g. Cadence ILMs) and between-step snapshot databases in ``OBJ_DIR/par-rundir``
* GDSII file with final design: ``{OBJ_DIR}/par-rundir/{TOP_MODULE}.gds``
* Verilog gate-level netlist: ``{OBJ_DIR}/par-rundir/{TOP_MODULE}.lvs.v``
* SDF file for post-par simulation: ``{OBJ_DIR}/par-rundir/{TOP_MODULE}.sdf``
* Timing reports: ``{OBJ_DIR}/par-rundir/timingReports``
* A script to open the final chip: ``{OBJ_DIR}/par-rundir/generated_scripts/open_chip``

P&R output Hammer IR ``{OBJ_DIR}/par-rundir/par-output.json`` is converted to inputs for the DRC, LVS, and simulation tools by the ``par-to-drc``, ``par-to-lvs``, and ``par-to-sim`` actions, respectively.

P&R Commands
------------

* P&R Command (after syn-to-par is run)

    * ``hammer-vlsi -e env.yml -p {OBJ_DIR}/par-input.json --obj_dir OBJ_DIR par``

* P&R to DRC

    * ``hammer-vlsi -e env.yml -p config.yml -p {OBJ_DIR}/par-rundir/par-output.json --obj_dir OBJ_DIR par-to-drc``

* P&R to LVS

    * ``hammer-vlsi -e env.yml -p config.yml -p {OBJ_DIR}/par-rundir/par-output.json --obj_dir OBJ_DIR par-to-lvs``

* P&R to Simulation

    * ``hammer-vlsi -e env.yml -p config.yml -p {OBJ_DIR}/par-rundir/par-output.json --obj_dir OBJ_DIR par-to-sim``

