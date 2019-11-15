#!/bin/bash
# Test preparation script.
# Ensures that ammonite and the Hammer IR JAR are built.

set -e
set -euo pipefail

script_dir=$(dirname $0)
cd $script_dir

# Build Hammer IR
pushd ..
./build.sh

# Ensure ammonite exists
if [ ! -f "amm" ]; then
  ./get_ammonite.sh
fi

popd

# Create ammonite wrapper to import hammer_ir JAR.
echo "../amm --predef-code 'import ammonite.ops._; interp.load.cp(pwd/os.up/\"hammer_ir.jar\")' \$1" > amm
chmod +x amm
