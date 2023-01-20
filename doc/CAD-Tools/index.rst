Hammer Tool Plugins
========================================

This guide discusses the use and creation of CAD tool plugins in Hammer. A CAD tool plugin provides the actual implementation of Hammer APIs and outputs the TCL necessary to control its corresponding CAD tool.

Tool plugins must be structured as Python packages under the ``hammer.action`` package hierarchy. For example, if ``dc`` is a synthesis tool, it must be contained under ``hammer/synthesis/dc``. 
The package should contain an class object named 'tool' to create an instance of the tool.
``tool`` should be a class object of an appropriate subclass of HammerTool (e.g. ``HammerSynthesisTool``).

.. toctree::
   :maxdepth: 2
   :caption: Hammer CAD Tools:

   Hammer-CAD-Tools
   Tool-Plugin-Setup
   OpenROAD
