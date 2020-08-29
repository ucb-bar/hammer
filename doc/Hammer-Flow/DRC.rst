DRC
===============================

Hammer has an action for running design rules check (DRC) on a post-place-and-route GDS.
This action requires a tool plugin to implement ``HammerDRCTool``.

DRC Setup Keys
--------------

* Namespace: ``vlsi.core``

    * ``drc_tool_path``

        * Set to the directory containing the tool plugin directory for the DRC tool, typically ``/path/to/tool_plugin/drc``. This will be the parent directory of the directory containing ``__init__.py`` and ``defaults.yml``.

    * ``drc_tool``
        
        * Actual name of the DRC tool that is setup in the directory, ``drc_tool_path``, e.g. ``calibre``

DRC Input Keys
--------------

* Namespace: ``drc``

    * ``inputs.top_module`` (str)

        * Name of top RTL module to run DRC on. Auto-populated after par-to-drc.

    * ``inputs.layout_file`` (str)

        * GDSII file from place-and-route. Auto-populated after par-to-drc.

    * ``inputs.additional_drc_text_mode`` (str)

        * Chooses what custom DRC commands to add to the run file. ``auto`` selects the one provided in the :ref:`tech-json`.

    * ``inputs.drc_rules_to_run`` ([str])

        * This selects a subset of the rules given in the technology's Design Rule Manual (DRM). The format of these rules will be technology- and tool-specific.

    * ``submit`` (dict)

        * Can override global settings for submitting jobs to a workload management platform.

DRC Inputs 
--------------
There are no other prerequisites to running DRC other than setting the keys described above.

DRC Outputs
--------------

* DRC results report and database in ``{OBJ_DIR}/drc-rundir``
* A run file: ``{OBJ_DIR}/drc-rundir/drc_run_file``
* A script to interactively view the DRC results: ``{OBJ_DIR}/drc-rundir/generated_scripts/view_drc``

DRC Commands
--------------

* DRC Command (after par-to-drc is run)

    * ``hammer-vlsi -e env.yml -p {OBJ_DIR}/drc-input.json --obj_dir OBJ_DIR drc``
