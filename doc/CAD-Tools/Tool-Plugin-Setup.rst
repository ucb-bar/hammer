Setting up a Hammer CAD Tool Plugin
================================================

This guide will discuss what a Hammer user may do if they want to implement their own CAD tool plugin or extend the current CAD tool plugins. There are some basic mock-up examples of how this can be done in the ``par`` and ``synthesis`` directories inside ``hammer/src/hammer-vlsi/``.

Tool Class
------------------------------------------------

Writing a tool plugin starts with writing the tool class. Hammer already provides a set of classes and mixins for a new tool to extend. For example, the Hammer Innovus plugin inherits from ``HammerPlaceAndRouteTool`` and ``CadenceTool``. 

Steps
------------------------------------------------

Each tool implements a steps method. For instance, a portion of the steps method for a place-and-route tool may look like:

.. _steps-example:
.. code-block:: python
    
    @property
    def steps(self) -> List[HammerToolStep]:
        steps = [
            self.init_design,
            self.floorplan_design,
            self.route_design
        ]
        return self.make_steps_from_methods(steps)

Each of the steps are their own methods in the class that will write TCL that will execute with the tool.

Getting Settings
------------------------------------------------

Hammer provides the method ``get_setting("KEY_NAME")`` for the tool to actually grab the settings from the user's input YML or JSON files.  One example would be ``self.get_setting("par.blockage_spacing")`` so that Hammer can specify to the desired P&R tool what spacing to use around place and route blockages.

Writing TCL
------------------------------------------------

Hammer provides two main methods for writing TCL to a file: ``append`` and ``verbose_append``. Both do similar things but ``verbose_append`` will emit additional TCL code to print the command to the terminal upon execution.

Executing the Tool
------------------------------------------------

When all the desired TCL has been written by various step methods, it is time to execute the tool itself. Hammer provides the method ``run_executable(args, cwd=self.run_dir)`` to do so. ``args`` is a Python list of flags to be run with the tool executable. ``cwd=self.run_dir`` sets the "current working directory" and allows the plugin to specify in what directory to execute the command.


Tool Outputs
-----------------------------------------------

After execution, the Hammer driver will emit a copy of the Hammer IR database in JSON format to the run directory as well as specific new fields created by the activity.
The name of the output JSON files will be related to the activity type (e.g. ``par-output.json`` and ``par-output-full.json`` for the ``par`` activity).
The ``-full`` verison contains the entire Hammer IR database, while the other version contains only the output entries created by this activity.
The individual fields are created when the ``export_config_outputs`` method is called.
Each implementation of this tool must override this method with a new one that calls its ``super`` method and appends any additional output fields to the output dictionary, as necessary.
