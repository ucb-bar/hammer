#!/bin/sh

set -ex

coverage3 erase

coverage3 run -a ../hammer-vlsi/vlsi_test.py

coverage3 run -a ../hammer_config/config_test.py

coverage3 html
