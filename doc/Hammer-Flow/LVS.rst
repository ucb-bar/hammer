LVS
===============================

Hammer has an action for running LVS decks on a post-P&R'd GDS and gate-levl netlist. This action invokes a ``HammerLVSTool`` that must be provided as part of a tool plugin.

LVS Setup Keys
--------------

* Namespace: ``vlsi.core``

    * ``lvs_tool_path``

        * Set to directory with ``__init__.py`` and ``defaults.yml`` for the lvs tool, typically ``/path/to/tool_plugin/lvs``

    * ``lvs_tool``
        
        * Actual name of the lvs tool that is setup in the directory, ``lvs_tool_path``, e.g. ``calibre``

LVS Input Keys
--------------

* Namespace: ``lvs``

    * ``inputs.top_module`` (str)

        * Name of top RTL module to run LVS on. Auto-populated after par-to-lvs.

    * ``inputs.layout_file`` (str)

        * GDSII file from P&R. Auto-populated after par-to-lvs.

    * ``inputs.schematic_files`` ([str])

        * Netlists from P&R'd design and libraries. Auto-populated after par-to-lvs.

    * ``inputs.additional_lvs_text_mode`` (str)

        * Chooses what custom LVS commands to add to the run file. ``auto`` selects the one provided in the :ref:`tech-json`.

    * ``submit`` (dict)

        * Can override global settings for submitting jobs to a workload management platform.

LVS Inputs 
--------------
There are no other prerequisites to running LVS other than setting the keys described above.

LVS Outputs
--------------
* LVS results report and database in ``{OBJ_DIR}/lvs-rundir``
* A run file: ``{OBJ_DIR}/lvs-rundir/lvs_run_file``
* A script to interactively view the LVS results: ``{OBJ_DIR}/lvs-rundir/generated_scripts/view_lvs``

LVS Commands
--------------

* LVS Command (after par-to-lvs is run)

    * ``hammer-vlsi -e env.yml -p {OBJ_DIR}/lvs-input.json --obj_dir build lvs``
