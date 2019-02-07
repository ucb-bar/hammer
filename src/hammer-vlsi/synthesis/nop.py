#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op synthesis tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerSynthesisTool, DummyHammerTool
from hammer_utils import deeplist


class NopSynth(HammerSynthesisTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        self.output_files = deeplist(self.input_files)
        return True


tool = NopSynth
