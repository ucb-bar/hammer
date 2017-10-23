Shell tools for hammer/hammer-vlsi.

Requirements:
- python3 in the $PATH
- hammer-shell in the $PATH

- hammer_config, python-jsonschema-objects, hammer-tech, hammer-vlsi in $PYTHONPATH
- HAMMER_PYYAML_PATH set to pyyaml/lib3 or pyyaml in $PYTHONPATH
- HAMMER_HOME set to hammer repo root
- HAMMER_VLSI path set to $HAMMER_HOME/src/hammer-vlsi

Example PYTHONPATH for in-tree use:
```shell
export PYTHONPATH="$HAMMER_HOME/src:$HAMMER_HOME/src/python-jsonschema-objects:$HAMMER_HOME/src/hammer-tech:$HAMMER_HOME/src/hammer-vlsi:$HAMMER_HOME/src/tools/pyyaml/lib3:$PYTHONPATH"
```
