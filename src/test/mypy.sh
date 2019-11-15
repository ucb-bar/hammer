#!/bin/bash
# Shell script that calls mypy a number of times and then suppresses the output
# if empty so that mypy_with_exclusions.sh can report success.
# Exclude bits known to be problematic to mypy.

set -e

err=0

call_mypy () {
    >&2 echo "Running mypy $*"
    output=$(mypy "$@" | grep -v "python-jsonschema-objects" | grep -v TechJSON | grep -v installs | grep -v tarballs | grep -v ccs | grep -v nldm | grep -v supplies | grep -v lef_file | grep -v qrc_techfile | grep -v serialize | grep -v "hammer_tech.Library" | grep -v milkyway_ | grep -v tluplus | grep -v jsonschema | grep -v "pyyaml/" | grep -v provides | grep -v \"libraries\" || true)
    if [[ ! -z "${output}" ]]; then
        echo "${output}"
        err=1
    fi
}

# Core
call_mypy --package hammer_vlsi
call_mypy --package hammer_utils

# Shell
call_mypy ../hammer-shell/get-config

# Testing code
call_mypy ../hammer-vlsi/*test.py
call_mypy ../hammer_config_test/test.py

# Plugins
call_mypy ../hammer-vlsi/synthesis/mocksynth/__init__.py
call_mypy ../hammer-vlsi/synthesis/vivado/__init__.py
call_mypy ../hammer-vlsi/synthesis/nop.py
call_mypy ../hammer-vlsi/par/nop.py
call_mypy ../hammer-vlsi/par/vivado/__init__.py
call_mypy ../hammer-vlsi/par/mockpar/__init__.py
call_mypy ../hammer-vlsi/drc/*.py
call_mypy ../hammer-vlsi/lvs/*.py
call_mypy ../hammer-vlsi/pcb/generic/__init__.py
call_mypy ../hammer-vlsi/technology/asap7/*.py
call_mypy ../hammer-vlsi/technology/asap7/sram_compiler/__init__.py

# Plugins which may or may not exist
if [ -f ../hammer-vlsi/synthesis/dc/__init__.py ]; then
    call_mypy ../hammer-vlsi/synthesis/dc/__init__.py
fi
if [ -f ../hammer-vlsi/synthesis/genus/__init__.py ]; then
    call_mypy ../hammer-vlsi/synthesis/genus/__init__.py
fi
if [ -f ../hammer-vlsi/par/icc/__init__.py ]; then
    call_mypy ../hammer-vlsi/par/icc/__init__.py
fi
if [ -f ../hammer-vlsi/par/innovus/__init__.py ]; then
    call_mypy ../hammer-vlsi/par/innovus/__init__.py
fi
if [ -f ../hammer-vlsi/drc/calibre/__init__.py ]; then
    call_mypy ../hammer-vlsi/drc/calibre/__init__.py
fi
if [ -f ../hammer-vlsi/lvs/calibre/__init__.py ]; then
    call_mypy ../hammer-vlsi/lvs/calibre/__init__.py
fi

exit $err
