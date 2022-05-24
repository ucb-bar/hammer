#!/bin/bash
# Convenience script for setting variables for in-tree use of hammer.

if [ -z "${HAMMER_HOME}" ]; then
  # Try to find the location of the script even if it's called through a symlink.
  #  https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself
  #  https://stackoverflow.com/questions/35006457/choosing-between-0-and-bash-source
  export HAMMER_HOME="$( dirname "$( readlink -f "${BASH_SOURCE[0]}" )" )"
  >&2 echo "Setting HAMMER_HOME=${HAMMER_HOME}"
fi

export HAMMER_VLSI="${HAMMER_HOME}/src/hammer-vlsi"
export PYTHONPATH="${HAMMER_HOME}/src:${HAMMER_HOME}/src/jsonschema:${HAMMER_HOME}/src/python-jsonschema-objects:${HAMMER_HOME}/src/hammer-tech:${HAMMER_HOME}/src/hammer-vlsi:${PYTHONPATH}"
export MYPYPATH="${PYTHONPATH}"
export PATH="${HAMMER_HOME}/src/hammer-shell:${PATH}"
