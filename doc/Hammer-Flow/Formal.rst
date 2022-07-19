Formal Verification
===============================

Hammer supports post-synthesis and post-P&R formal verification. It provides a simple API to provide a set of reference and implementation inputs (e.g. Verilog netlists) to perform formal verification checks such as logical equivalence checking (LEC).
This action requires a tool plugin to implement ``HammerFormalTool``.

Formal Verification Setup Keys
-------------------------------

* Namespace: ``vlsi.core``

    * ``formal_tool_path``
        * Set to the directory containing the tool plugin directory for the formal tool, typically ``/path/to/tool_plugin/formal``. This will be the parent directory of the directory containing ``__init__.py`` and ``defaults.yml``.
    * ``formal_tool``
        * Actual name of the formal verification tool that is setup in the directory ``formal_tool_path``, e.g. ``conformal``

Formal Verification Input Keys
-------------------------------

* Namespace: ``formal.inputs``

    * ``check`` (str)

        * Name of the formal verification check that is to be performed. Support varies based on the specific tool plugin. Potential check types/algorithms could be "lec", "power", "constraint", "cdc", "property", "eco", and more. At the moment, only "lec" is supported.

    * ``input_files`` ([])

        * A list of file paths to implementation source files (verilog, vhdl, spice, liberty, etc.) to be passed to the formal verification tool. For a LEC tool, this would be the sources for the "revised" design. The paths may be relative to the directory in which ``hammer-vlsi`` is called.

    * ``reference_files`` ([])

        * A list of file paths to reference source files (verilog, vhdl, spice, liberty, etc.) to be passed to the formal verification tool. For a LEC tool, this would be the sources for the "golden" design. The paths may be relative to the directory in which ``hammer-vlsi`` is called.

    * ``top_module`` (str)

        * Name of the top level module of the design to be verified.

Formal Verification Inputs
-------------------------------

Running the ``syn-to-formal`` action after running synthesis will automatically generate the Hammer IR required to pipe the synthesis outputs to the Hammer formal verification tool, and should be included in the Hammer call, as demonstrated in the "Post-Synthesis Formal Verification" command below.  The same goes for post-place-and-route formal verification.

At this time, only netlists are passed to the formal verification tool. Additional files (SDCs, CPFs, etc.) are needed for more advanced formal verification checks but are not yet currently supported. Similarly, formal verification on the behavioral RTL is also not yet supported.

Formal Verification Outputs
-------------------------------

The formal verification tool produces reports in ``OBJ_DIR/formal-rundir/``. Outputs from formal verification flows such as engineering change order (ECO) patches are not yet supported.

Formal Verification Commands
-------------------------------

* Synthesis to Formal Verification

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-rundir/syn-output.json -o OBJ_DIR/syn-to-formal_input.json --obj_dir OBJ_DIR syn-to-formal``

* Post-Synthesis Formal Verification

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-to-formal_input.json --obj_dir OBJ_DIR formal``

* P&R to Formal Verification 

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/par-rundir/par-output.json -o OBJ_DIR/par-to-formal_input.json --obj_dir OBJ_DIR par-to-formal``

* Post-P&R Formal Verification

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/par-to-formal_input.json --obj_dir OBJ_DIR formal``
