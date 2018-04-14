#!/bin/sh
set -x
# Core
mypy ../hammer-vlsi/cli_driver.py

# Shell
mypy ../hammer-shell/get-config

# Testing code
mypy ../hammer-vlsi/test.py
mypy ../hammer_config_test/test.py 

# Plugins
mypy ../hammer-vlsi/synthesis/dc/__init__.py
mypy ../hammer-vlsi/synthesis/genus/__init__.py
mypy ../hammer-vlsi/synthesis/mocksynth/__init__.py
mypy ../hammer-vlsi/par/icc/__init__.py
mypy ../hammer-vlsi/par/innovus/__init__.py
mypy ../hammer-vlsi/par/*.py
