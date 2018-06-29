#!/bin/sh
set -x
# Core
mypy --package hammer_vlsi

# Shell
mypy ../hammer-shell/get-config

# Testing code
mypy ../hammer-vlsi/*test.py
mypy ../hammer_config_test/test.py 

# Plugins
mypy ../hammer-vlsi/synthesis/mocksynth/__init__.py
mypy ../hammer-vlsi/par/nop.py

# Plugins which may or may not exist
if [ -f ../hammer-vlsi/synthesis/dc/__init__.py ]; then
	mypy ../hammer-vlsi/synthesis/dc/__init__.py
fi
if [ -f ../hammer-vlsi/synthesis/genus/__init__.py ]; then
	mypy ../hammer-vlsi/synthesis/genus/__init__.py
fi
if [ -f ../hammer-vlsi/par/icc/__init__.py ]; then
	mypy ../hammer-vlsi/par/icc/__init__.py
fi
if [ -f ../hammer-vlsi/par/innovus/__init__.py ]; then
	mypy ../hammer-vlsi/par/innovus/__init__.py
fi
