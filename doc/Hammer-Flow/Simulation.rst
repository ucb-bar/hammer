Simulation
===============================

Hammer supports RTL, post-synthesis, and post-P&R simulation. It provides a simple API to add flags to the simulator call and automatically passes in collateral to the simulation tool from the synthesis and place-and-route outputs.
This action requires a tool plugin to implement ``HammerSimTool``.

Simulation Setup Keys
-------------------------------

* Namespace: ``vlsi.core``
  
    * ``sim_tool_path``
        * Set to the directory containing the tool plugin directory for the DRC tool, typically ``/path/to/tool_plugin/sim``. This will be the parent directory of the directory containing ``__init__.py`` and ``defaults.yml``.
    * ``sim_tool``
        * Actual name of the simulation tool that is setup in the directory ``synthesis_tool_path``, e.g. ``vcs``

Simulation Input Keys
-------------------------------

* Namespace: ``sim.inputs``

    * ``input_files`` ([])

        * A list of file paths to source files (verilog sources, testharness/testbench, etc.) to be passed to the synthesis tool (both verilog and any other source files needed). The paths may be relative to the directory in which ``hammer-vlsi`` is called.

    * ``top_module`` (str)

        * Name of the top level module of the design.

    * ``options`` ([str])

        *  Any options that are passed into this key will appear as plain text flags in the simulator call.

    * ``defines`` ([str])

        * Specifies define options that are passed to the simulator. e.g. when using VCS, this will be added as ``+define+{DEFINE}``.

    *  ``compiler_opts`` ([str])

        * Specifies C compier options when generating the simulation executable. e.g. when using VCS, each compiler_opt will be added as ``-CC {compiler_opt}``.

    * ``timescale`` (str)

        * Plain string that specifies the simulation timescale. e.g. when using VCS, ``sim.inputs.timescale: '1ns/10ps'`` would be passed as ``-timescale=1ns/10ps``

    * ``tb_dut`` (str)
        
        * Hierarchical path to the to top level instance of the "dut" from the testbench.

    * ``level`` (``"rtl"`` or ``"gl"``)

        * This defines whether the simulation being run is at the RTL level or at the gate level.

    * ``all_regs`` ([str])

        * List of all registers in the design, typically generated from the synthesis or P&R tool. This is used in gate level simulation to initialize register values.

    * ``seq_cells`` ([str])

        * List of all sequential standard cells in the design, typically generated from the synthesis or P&R tool. This is used in gate level simulation.

    * ``sdf_file`` (str)

        * Path to Standard Delay Format file used in timing annotated simulations.

    * ``gl_register_force_value`` (0 or 1)

        * Defines what value all registers will be initialized to for gate level simulations.

    * ``timing_annotated`` (false or true)

        * Setting to false means that the simulation will be entirely functional. Setting to true means that the simulation will be time annotated based on synthesis or P&R results.

    * ``execution_flags`` ([str])

        *  Each string in this list will be passed as an option when actually executing the simulation executable generated from the previous arguments.

    * ``execute_sim`` (true or false)

        * Determines whether or not the simulation executable that is generated with the above inputs with the given flags or if the executable will just be generated.
        

Simulation Inputs
-------------------------------

There are no prerequisites to running an RTL simulation other than setting the keys that are described above. Running the ``syn-to-sim`` step after running synthesis will automatically generate the Hammer IR required to pipe the synthesis outputs to the Hammer simulation tool, and should be included in the Hammer call, as demonstrated in the "Post-Synthesis Gate Level Sim" command below.  The same goes for post-place-and-route simulations. The required files for these simulations
(SDF, SPEF, etc.) are generated and piped to the simulation tool in the corresponding step's outputs. 

The Hammer simulation tool will initialize register values in the simulation, as that is of particular need when simulating Chisel-based designs, to deal with issues around x-pessimism.

Simulation Outputs
-------------------------------

The simulation tool is able to output VCD/VPD files for the simulation. All of the relevant outputs of the simulation can be found in ``OBJ_DIR/sim-rundir/``.

Simulation Commands
-------------------------------

* RTL Simulation Command

    * ``hammer-vlsi -e env.yml -p config.yml --obj_dir build sim``

* Synthesis to Sim

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-rundir/syn-output.json --obj_dir build syn-to-sim``

* Post-Synthesis Gate Level Sim

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/syn-to-sim_input.json --obj_dir build sim``

* P&R to Simulation

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/par-rundir/par-output.json --obj_dir build par-to-sim``

* Post-P&R Gate Level Sim

    * ``hammer-vlsi -e env.yml -p config.yml -p OBJ_DIR/par-to-sim_input.json --obj_dir build sim``
