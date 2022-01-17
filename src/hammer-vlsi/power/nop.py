#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op power tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerPowerTool, DummyHammerTool


class NopPower(HammerPowerTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        return True

tool = NopPower
