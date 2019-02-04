#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# See LICENSE for license details.
#
#  nop.py
#  No-op synthesis tool.
#

from hammer_vlsi import HammerSynthesisTool, DummyHammerTool
from hammer_utils import deeplist


class NopSynth(HammerSynthesisTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        self.output_files = deeplist(self.input_files)
        return True


tool = NopSynth
