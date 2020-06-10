#!/bin/sh
# Convenience script for setting variables for in-tree use of hammer.

# Try to find the location of the script even if it's called through a symlink.
#  https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself
SOURCE="${BASH_SOURCE[0]}"
while [ -h "${SOURCE}" ]; do
  DIR="$( cd -P "$( dirname "${SOURCE}" )" > /dev/null 2>&1 && pwd )"
  SOURCE="$( readlink "${SOURCE}")"
  [[ ${SOURCE} != /* ]] && SOURCE="${DIR}/${SOURCE}"
done
DIR="$( cd -P "$( dirname "${SOURCE}" )" > /dev/null 2>&1 && pwd )"

if [ -z "${HAMMER_HOME}" ]; then
  export HAMMER_HOME="${DIR}"
  >&2 echo "Using (default) HAMMER_HOME=${HAMMER_HOME}"
else
  >&2 echo "Using HAMMER_HOME=${HAMMER_HOME}"
fi

export HAMMER_VLSI="${HAMMER_HOME}/src/hammer-vlsi"
export PYTHONPATH="${HAMMER_HOME}/src:${HAMMER_HOME}/src/jsonschema:${HAMMER_HOME}/src/python-jsonschema-objects:${HAMMER_HOME}/src/hammer-tech:${HAMMER_HOME}/src/hammer-vlsi:${HAMMER_HOME}/src/tools/pyyaml/lib3:${PYTHONPATH}"
export MYPYPATH="${PYTHONPATH}"
export PATH="${HAMMER_HOME}/src/hammer-shell:${PATH}"
