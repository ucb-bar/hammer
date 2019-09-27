Setting up a Hammer CAD Tool Plugin
================================================

This guide will discuss what a Hammer user may do if they want to implement their own CAD tool plugin or extend the current CAD tool plugins. There are some basic mockup examples of how this can be done in ``hammer/src/hammer-vlsi/ACTION/``, where ``ACTION`` may be ``par`` for example.

Tool Class
------------------------------------------------

Writing a tool plugin starts with writing the tool class. Hammer already provides a set of classes for a new tool to extend. For instance, the Hammer Innovus plugin inherits from ``HammerPlaceAndRouteTool`` and ``CadenceTool``. 

Steps
------------------------------------------------

Each tool implements a steps method. For instance, a portion of the steps method for a P&R tool may look like:

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

Hammer provides two main methods for writing TCL to a file: ``append`` and ``verbose_append``. Both do similar things but ``verbose_append`` will print the command explicitly upon execution.

Executing the Tool
------------------------------------------------

When all the desired TCL has been written by various step methods, it is time to execute the tool itself. Hammer provides the method ``run_executable(args, cwd=self.run_dir)`` to do so. ``args`` is a Python list of flags to be run with the tool executable. ``cwd=self.run_dir`` sets the "current working directory" and allows the plugin to specify what directory to execute the command in.


Tool Outputs
-----------------------------------------------

TODO
export_output_configs

