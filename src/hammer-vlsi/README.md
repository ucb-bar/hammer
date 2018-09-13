hammer-vlsi
===========

This is hammer-vlsi, the portion of HAMMER which abstracts synthesis + place-and-route in a tool and technology-agnostic fashion, for modular use in higher level tools.

Setup and environment
=====================

Requirements:
- Python 3.3+
  - For **Python 3.4 and lower**, the `typing` module must be installed. (`python3 -m pip install typing`)
  - For **Python 3.4**, the [enum34](https://pypi.org/project/enum34/) package must be installed. (`python3 -m pip install enum34`)
- python3 in the $PATH
- hammer-shell in the $PATH

- hammer_config, python-jsonschema-objects, hammer-tech, hammer-vlsi in $PYTHONPATH
- HAMMER_PYYAML_PATH set to pyyaml/lib3 or pyyaml in $PYTHONPATH
- HAMMER_HOME set to hammer repo root
- HAMMER_VLSI path set to $HAMMER_HOME/src/hammer-vlsi

Example of in-tree use of hammer/hammer-vlsi:
```shell
export HAMMER_HOME="..." # Replace this with the hammer repo root
export HAMMER_VLSI="$HAMMER_HOME/src/hammer-vlsi"
export PYTHONPATH="$HAMMER_HOME/src:$HAMMER_HOME/src/python-jsonschema-objects:$HAMMER_HOME/src/hammer-tech:$HAMMER_HOME/src/hammer-vlsi:$HAMMER_HOME/src/tools/pyyaml/lib3:$PYTHONPATH"
export PATH="$HAMMER_HOME/src/hammer-shell:$PATH"
```

Tool library system
===================

hammer-vlsi imports libraries as Python modules. For example, if dc was a tool, it would be either 1) a folder named "dc" with __init__.py which follows the given format; 2) a file named dc.py which follows the given format.

The module should contain an class object named 'tool', since hammer-vlsi will do `import dc.tool`, for example, and use it to create an instance of the tool.
`tool` should be a class object of an appropriate subclass of HammerTool (e.g. `HammerSynthesisTool`).

Technology library system
=========================

Currently technologies should have its own folder along with a corresponding .tech.json file. For example, "saed32" would have a "saed32.tech.json" file inside of the "saed32" folder.
