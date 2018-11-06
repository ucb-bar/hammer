#!/bin/sh
trap "rm -f _tmp_vlsi.txt" EXIT

../hammer-vlsi/generate_properties.py -d -f hammer_vlsi/hammer_vlsi_impl.py > _tmp_vlsi.txt

if cmp --silent "../hammer-vlsi/hammer_vlsi/hammer_vlsi_impl.py" "_tmp_vlsi.txt"; then
    # Files have the same content
    exit 0
else
    echo "generate_properties.py is inconsistent with the generated files"
    diff -u "../hammer-vlsi/hammer_vlsi/hammer_vlsi_impl.py" "_tmp_vlsi.txt"
    exit 1
fi
