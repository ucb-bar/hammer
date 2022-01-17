#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op sim tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerSimTool, DummyHammerTool


class NopSim(HammerSimTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        return True

tool = NopSim
