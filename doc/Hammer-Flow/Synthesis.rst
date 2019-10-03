Synthesis 
===============================

Synthesis Setup Keys
-------------------------------

* Namespace: ``vlsi.core``
  
    * ``synthesis_tool_path``

        * Set to directory with ``__init__.py`` and ``defaults.yml`` for the synthesis tool, typically ``/path/to/tool_directory/synthesis/``

    * ``synthesis_tool``

        * Actual name of the synthesis tool that is setup in the directory ``synthesis_tool_path``, e.g. ``genus``

Synthesis Input Keys
-------------------------------

* Namespace: ``synthesis``

    * ``inputs.input_files`` ([])

        * A list of file paths to source files to be passed to the synthesis tool. The paths may be relative to the directory in which ``hammer-vlsi`` is called.

    * ``inputs.top_module`` (str)

        * Name of the top level verilog module of the design. 

    * ``clock_gating_mode`` (str)

        * ``auto``: turn on automatic clock gating inference in CAD tools

        * ``empty``: do not do any clock gating

Synthesis Inputs
-------------------------------

There are no prerequisites to running synthesis other than setting the keys that are described above.


Synthesis Outputs
------------------------------

* Mapped verilog file: ``obj_dir/syn-rundir/{TOP_MODULE}.mapped.v``
* Mapped design SDF: ``obj_dir/syn-rundir/{TOP_MODULE}.mapped.sdf``
* Synthesis output Hammer IR is contained in ``obj_dir/syn-rundir/syn-output.json``
* Synthesis reports for gates, area, and timing are output in ``obj_dir/syn-rundir/reports``. The mapped

The synthesis output Hammer IR is converted to inputs for the P&R tool and the simulation tool by the Hammer ``syn-to-par`` and ``syn-to-sim`` commands, respectively.
    

Synthesis Commands
-----------------------------

* Synthesis Command

    * ``hammer-vlsi -e env.yml -p config.yml --obj_dir build syn``

* Synthesis to P&R

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-rundir/syn-output.json --obj_dir build syn-to-par``

* Synthesis to Simulation

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-rundir/syn-output.json --obj_dir build syn-to-sim`` 
