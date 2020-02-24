Hammer Actions
===================================

Hammer has a set of actions including synthesis, place-and-route, DRC, LVS, simulation, SRAM generation, and PCB collateral generation.
All of the Hammer actions and their associated key inputs can be found in ``hammer/src/hammer-vlsi/defaults.yml`` and are documented in detail in each action's documentation.

Hammer will automatically pass the output files of one action to subsequent actions if those actions require the files.
Hammer does this with conversion steps (e.g. ``syn-to-par`` for synthesis outputs to place-and-route inputs), which map the outputs from one tool into the inputs of another (e.g. ``synthesis.outputs.output_files`` maps to ``par.outputs.input_files``).
The Hammer make infrastructure builds these conversion rules automatically, so using the make infrastructure is recommended.
See the :ref:`buildfile` section for more details.

Hammer actions are implemented using tools. See the :ref:`cad-tools` section for details about how these tools are set up.
