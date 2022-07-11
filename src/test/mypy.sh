#!/bin/bash
# Shell script that calls mypy a number of times and then suppresses the output
# if empty so that mypy_with_exclusions.sh can report success.
# Exclude bits known to be problematic to mypy.

set -e

err=0

call_mypy () {
    >&2 echo "Running mypy $*"
    output=$(mypy --no-error-summary "$@" | grep -v "python-jsonschema-objects" | grep -v TechJSON | grep -v installs | grep -v tarballs | grep -v ccs | grep -v nldm | grep -v supplies | grep -v lef_file | grep -v qrc_techfile | grep -v serialize | grep -v "hammer_tech.Library" | grep -v milkyway_ | grep -v tluplus | grep -v jsonschema | grep -v provides | grep -v \"libraries\" | grep -v "note: See" || true)
    if [[ ! -z "${output}" ]]; then
        echo "${output}"
        err=1
    fi
}

# Core
call_mypy --package hammer_utils
# call_mypy --package hammer_vlsi
call_mypy ../hammer-vlsi/hammer_vlsi/*.py
call_mypy ../hammer-vlsi/hammer_vlsi/vendor/__init__.py
call_mypy ../hammer-vlsi/hammer_vlsi/vendor/openroad.py

# Shell
call_mypy ../hammer-shell/get-config

# Testing code
call_mypy ../hammer-vlsi/*test.py
call_mypy ../hammer_config_test/test.py

# Plugins
call_mypy ../hammer-vlsi/synthesis/mocksynth/__init__.py
call_mypy ../hammer-vlsi/synthesis/vivado/__init__.py
call_mypy ../hammer-vlsi/synthesis/yosys/__init__.py
call_mypy ../hammer-vlsi/synthesis/nop.py
call_mypy ../hammer-vlsi/par/nop.py
call_mypy ../hammer-vlsi/par/vivado/__init__.py
call_mypy ../hammer-vlsi/par/mockpar/__init__.py
call_mypy ../hammer-vlsi/par/openroad/__init__.py
call_mypy ../hammer-vlsi/drc/*.py
call_mypy ../hammer-vlsi/drc/openroad/__init__.py
call_mypy ../hammer-vlsi/drc/magic/__init__.py
call_mypy ../hammer-vlsi/lvs/*.py
call_mypy ../hammer-vlsi/lvs/netgen/__init__.py
call_mypy ../hammer-vlsi/pcb/generic/__init__.py
call_mypy ../hammer-vlsi/technology/asap7/*.py
call_mypy ../hammer-vlsi/technology/asap7/sram_compiler/__init__.py
call_mypy ../hammer-vlsi/technology/sky130/*.py
call_mypy ../hammer-vlsi/technology/sky130/sram_compiler/__init__.py

# Tool plugins which may or may not exist
if [ -f ../../../hammer-synopsys-plugins/sim/vcs/__init__.py ]; then
    call_mypy ../../../hammer-synopsys-plugins/sim/vcs/__init__.py
fi
if [ -f ../../../hammer-synopsys-plugins/synthesis/dc/__init__.py ]; then
    call_mypy ../../../hammer-synopsys-plugins/synthesis/dc/__init__.py
fi
if [ -f ../../../hammer-cadence-plugins/synthesis/genus/__init__.py ]; then
    MYPYPATH=$MYPYPATH:../../../hammer-cadence-plugins/common call_mypy ../../../hammer-cadence-plugins/synthesis/genus/__init__.py
fi
if [ -f ../../../hammer-synopsys-plugins/par/icc/__init__.py ]; then
    call_mypy ../../../hammer-synopsys-plugins/par/icc/__init__.py
fi
if [ -f ../../../hammer-cadence-plugins/par/innovus/__init__.py ]; then
    MYPYPATH=$MYPYPATH:../../../hammer-cadence-plugins/common call_mypy ../../../hammer-cadence-plugins/par/innovus/__init__.py
fi
if [ -f ../../../hammer-cadence-plugins/power/voltus/__init__.py ]; then
    MYPYPATH=$MYPYPATH:../../../hammer-cadence-plugins/common call_mypy ../../../hammer-cadence-plugins/power/voltus/__init__.py
fi
if [ -f ../../../hammer-cadence-plugins/formal/conformal/__init__.py ]; then
    MYPYPATH=$MYPYPATH:../../../hammer-cadence-plugins/common call_mypy ../../../hammer-cadence-plugins/formal/conformal/__init__.py
fi
if [ -f ../../../hammer-cadence-plugins/timing/tempus/__init__.py ]; then
    MYPYPATH=$MYPYPATH:../../../hammer-cadence-plugins/common call_mypy ../../../hammer-cadence-plugins/timing/tempus/__init__.py
fi
if [ -f ../../../hammer-mentor-plugins/drc/calibre/__init__.py ]; then
    call_mypy ../../../hammer-mentor-plugins/drc/calibre/__init__.py
fi
if [ -f ../../../hammer-synopsys-plugins/drc/icv/__init__.py ]; then
    call_mypy ../../../hammer-synopsys-plugins/drc/icv/__init__.py
fi
if [ -f ../../../hammer-mentor-plugins/lvs/calibre/__init__.py ]; then
    call_mypy ../../../hammer-mentor-plugins/lvs/calibre/__init__.py
fi
if [ -f ../../../hammer-synopsys-plugins/lvs/icv/__init__.py ]; then
    call_mypy ../../../hammer-synopsys-plugins/lvs/icv/__init__.py
fi

# Technology plugin (if first argument is specified)
if [ -f ../../../hammer-$1-plugin/$1/__init__.py ]; then
    call_mypy ../../../hammer-$1-plugin/$1/__init__.py
fi

exit $err
