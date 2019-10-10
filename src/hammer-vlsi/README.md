hammer-vlsi
===========

This is hammer-vlsi, the portion of HAMMER which abstracts synthesis + place-and-route in a tool and technology-agnostic fashion, for modular use in higher level tools.

Setup and Environment
=====================

System requirements:
- Python 3.6+ recommended (minimum Python 3.3+)
  - For **Python 3.4 and lower**, the `typing` module must be installed. (`python3 -m pip install typing`)
  - For **Python 3.4**, the [enum34](https://pypi.org/project/enum34/) package must be installed. (`python3 -m pip install enum34`)
- python3 in the $PATH
- hammer-shell in the $PATH

- hammer_config, python-jsonschema-objects, hammer-tech, hammer-vlsi in $PYTHONPATH
- HAMMER_PYYAML_PATH set to pyyaml/lib3 or pyyaml in $PYTHONPATH
- HAMMER_HOME set to hammer repo root
- HAMMER_VLSI path set to $HAMMER_HOME/src/hammer-vlsi

See [sourceme.sh](sourceme.sh) for an example of in-tree use of hammer/hammer-vlsi.

The default technology, ASAP7, has some extra requirements. See its [README](technology/asap7/README.md) for instructions.

Environment Check
=================

To quickly test that our environment is set up for Hammer, we can try running the unit tests. Run the following using bash after cloning the Hammer repo:

```bash
git submodule update --init --recursive
export HAMMER_HOME=$PWD
source sourceme.sh
cd src/test
./unittests.sh
echo $?
```

If the last line above returns 0, then the environment is set up and ready to go.


Tool Library
============

hammer-vlsi imports libraries as Python modules. For example, if dc was a tool, it would be either 1) a folder named "dc" with __init__.py which follows the given format; 2) a file named dc.py which follows the given format.

The module should contain an class object named 'tool', since hammer-vlsi will do `import dc.tool`, for example, and use it to create an instance of the tool.
`tool` should be a class object of an appropriate subclass of HammerTool (e.g. `HammerSynthesisTool`).

Technology Library
==================

Currently technologies should have its own folder along with a corresponding .tech.json file. For example, "asap7" would have a "asap7.tech.json" file inside of the "asap7" folder.
