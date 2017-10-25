#!/bin/sh

set -ex

coverage3 run ../hammer-vlsi/test.py

coverage3 run ../hammer_config_test/test.py

coverage3 html
