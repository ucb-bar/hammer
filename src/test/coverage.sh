#!/bin/sh

set -ex

coverage3 erase

coverage3 run -a ../hammer-vlsi/test.py

coverage3 run -a ../hammer_config_test/test.py

coverage3 html
