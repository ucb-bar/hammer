#!/bin/sh
# Convenience script for setting variables for in-tree use of hammer.
if [ -z "$HAMMER_HOME" ]; then
    >&2 echo "Must set HAMMER_HOME to root. Try export HAMMER_HOME="\$PWD" for the current dir."
else
export HAMMER_VLSI="$HAMMER_HOME/src/hammer-vlsi"
export PYTHONPATH="$HAMMER_HOME/src:$HAMMER_HOME/src/jsonschema:$HAMMER_HOME/src/python-jsonschema-objects:$HAMMER_HOME/src/hammer-tech:$HAMMER_HOME/src/hammer-vlsi:$HAMMER_HOME/src/tools/pyyaml/lib3:$PYTHONPATH"
export MYPYPATH="$PYTHONPATH"
export PATH="$HAMMER_HOME/src/hammer-shell:$PATH"
fi
