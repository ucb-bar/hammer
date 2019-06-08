#!/bin/sh
# Convenience script for setting variables for in-tree use of hammer.
if [ -z "$HAMMER_HOME" ]; then
    >&2 echo "Must set HAMMER_HOME to root. Try export HAMMER_HOME="\$PWD" for the current dir."
else
export HAMMER_VLSI="$HAMMER_HOME/src/hammer-vlsi"
export PYTHONPATH="$HAMMER_HOME/src:$HAMMER_HOME/src/hammer-tech:$HAMMER_HOME/src/hammer-vlsi:$PYTHONPATH"
# if import failed, then use vending version
python3 -c "import jsonschema, python_jsonschema_objects, yaml" > /dev/null 2>&1
if [[ $? == 1 ]]; then
    export PYTHONPATH="$HAMMER_HOME/src/contrib/jsonschema:$HAMMER_HOME/src/contrib/python-jsonschema-objects:$HAMMER_HOME/src/contrib/pyyaml:$PYTHONPATH"
fi
export MYPYPATH="$PYTHONPATH"
export PATH="$HAMMER_HOME/src/hammer-shell:$PATH"
fi
