#!/bin/sh
# Run mypy.sh but exclude bits known to be problematic to mypy.
# Also, sort and remove duplicates from multiple calls to mypy.

./mypy.sh | grep -v "python-jsonschema-objects" | grep -v installs | grep -v tarballs | grep -v ccs | grep -v nldm | grep -v supplies | grep -v lef_file | grep -v qrc_techfile | grep -v serialize | grep -v "hammer_tech.Library" | grep -v milkyway_ | grep -v tluplus | grep -v jsonschema | grep -v "pyyaml/" | grep -v provides | grep -v \"libraries\" | sort -u
