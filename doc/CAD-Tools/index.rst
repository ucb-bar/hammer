Hammer CAD Tool Plugins
========================================

This guide discusses the use and creation of CAD tool plugins in Hammer. A CAD tool plugin provides the actual implementation of Hammer APIs and outputs the TCL necessary to control its corresponding CAD tool.

Hammer imports libraries as Python modules. For example, if dc was a tool, it would be either 1) a folder named "dc" with __init__.py which follows the given format; 2) a file named dc.py which follows the given format.

The module should contain an class object named 'tool', since hammer-vlsi will do `import dc.tool`, for example, and use it to create an instance of the tool.
`tool` should be a class object of an appropriate subclass of HammerTool (e.g. `HammerSynthesisTool`).

.. toctree::
   :maxdepth: 2
   :caption: Hammer CAD Tools:

   Hammer-CAD-Tools
   Tool-Plugin-Setup
