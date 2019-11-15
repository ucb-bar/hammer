#!/bin/sh
if [ ! -f "./mill" ]; then
  ./get_mill.sh
fi
./mill hammer_ir.assembly
cp out/hammer_ir/assembly/dest/out.jar hammer_ir.jar
