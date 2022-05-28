Static Timing Analysis
===============================

Hammer supports post-synthesis and post-P&R static timing analysis. It provides a simple API to provide a set of design inputs (e.g. Verilog netlists, delay files, parasitics files) to perform static timing analysis (STA) for design signoff.
This action requires a tool plugin to implement ``HammerTimingTool``.

STA Setup Keys
-------------------------------

* Namespace: ``vlsi.core``

    * ``timing_tool_path``
        * Set to the directory containing the tool plugin directory for the STA tool, typically ``/path/to/tool_plugin/timing``. This will be the parent directory of the directory containing ``__init__.py`` and ``defaults.yml``.
    * ``timing_tool``
        * Actual name of the STA tool that is setup in the directory ``timing_tool_path``, e.g. ``tempus``

STA Input Keys
-------------------------------

* Namespace: ``timing.inputs``

    * ``input_files`` ([])

        * A list of file paths to the Verilog gate-level netlist to be passed to the STA tool. The paths may be relative to the directory in which ``hammer-vlsi`` is called.

    * ``top_module`` (str)

        * Name of the top level module of the design to be timed.

    * ``post_synth_sdc`` (str)

        * Post-synthesis generated SDC. Auto-populated after syn-to-timing.

    * ``spefs`` ([str])

        * List of paths to all spef (parasitic extraction) files for the design. This list may include a spef file per MMMC corner. Paths may be relative to the directory in which hammer-vlsi is called.

    * ``sdf_file`` (str)

        * Path to Standard Delay Format file. Auto-populated after syn-to-timing and par-to-timing.

    * ``max_paths`` (int)

        * Maximum number of timing paths to report from the STA tool. Large limits may hurt tool runtime.

STA Inputs
-------------------------------

Running the ``syn-to-timing`` action after running synthesis will automatically generate the Hammer IR required to pipe the synthesis outputs to the Hammer STA tool, and should be included in the Hammer call, as demonstrated in the "Post-Synthesis STA" command below.  The same goes for post-place-and-route STA.

STA Outputs
-------------------------------

The STA tool produces reports in ``OBJ_DIR/timing-rundir/``. Outputs from advanced STA flows such as engineering change order (ECO) patches are not yet supported.

STA Commands
-------------------------------

* Synthesis to STA 

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-rundir/syn-output.json -o OBJ_DIR/syn-to-timing_input.json --obj_dir OBJ_DIR syn-to-timing``

* Post-Synthesis STA 

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-to-timing_input.json --obj_dir OBJ_DIR timing``

* P&R to STA 

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/par-rundir/par-output.json -o OBJ_DIR/par-to-timing_input.json --obj_dir OBJ_DIR par-to-timing``

* Post-P&R STA 

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/par-to-timing_input.json --obj_dir OBJ_DIR timing``
