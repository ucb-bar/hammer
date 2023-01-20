.. _cad-tools:

Hammer CAD Tools
===============================

Hammer currently has open-source CAD tool plugins in the ``hammer/<action>`` folders and three repos for CAD tools from commercial vendors: ``hammer-cadence-plugins``, ``hammer-synopsys-plugins``, and ``hammer-mentor-plugins``. ``hammer-mentor-plugins`` is a private repo since it contains tool-specific commands not yet cleared for public release. Access to them may be granted for Hammer users who already have licenses for those tools. See the note about :ref:`plugins access <plugins-access>` for instructions for how to request access.

The structure of each repository is as follows:

* hammer

    * ACTION

        * TOOL_NAME

            * ``__init__.py`` contains the methods needed to implement the tool
            * ``defaults.yml`` contains the default :ref:`config` needed by the tool
        
        
ACTION is the Hammer action name (e.g. ``par``, ``synthesis``, ``drc``, etc.).
TOOL_NAME is the name of the tool, which is referenced in your configuration.
For example, if ACTION is ``par`` and TOOL_NAME is ``par_tool_foo``, the configuration would reference it as ``hammer.par.par_tool_foo``.
