hammer-vlsi
===========

This is hammer-vlsi, the portion of HAMMER which abstracts synthesis + place-and-route in a tool and technology-agnostic fashion, for modular use in higher level tools.

Tool library system
===================

hammer-vlsi imports libraries as python modules. For example, if dc was a tool, it would be either 1) a folder named "dc" with __init__.py which follows the given format; 2) a file named dc.py which follows the given format.

The module should contain an object named 'tool', since hammer-vlsi will do "import dc.tool", for example. `tool` should be an instance of an appropriate subclass of HammerTool (e.g. HammerSynthesisTool).

Technology library system
=========================

Currently technologies should have its own folder along with a corresponding .tech.json file. For example, "saed32" would have a "saed32.tech.json" file inside of the "saed32" folder.
