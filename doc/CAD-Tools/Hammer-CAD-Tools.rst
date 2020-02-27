.. _cad-tools:

Hammer CAD Tools
===============================

Hammer currently has three repos for CAD tools from different vendors: ``hammer-cadence-plugins``, ``hammer-synopsys-plugins``, and ``hammer-mentor-plugins``. These repos are private since they contain commands specific to each tool, but access to them may be granted for Hammer users pending approval from their respective companies.  

The structure of each repository is as follows:

* ACTION

    * TOOL_NAME

        * ``__init__.py`` contains the methods needed to implement the tool
        * ``defaults.yml`` contains the default Hammer IR needed by the tool
        
        
ACTION is the Hammer action name (e.g. ``par``, ``synthesis``, ``drc``, etc.).
TOOL_NAME is the name of the tool, which is referenced in your configuration. For example, having ``vlsi.core.par_tool_path: par_tool_foo`` in your configuration would expect a TOOL_NAME of ``par_tool_foo``.
