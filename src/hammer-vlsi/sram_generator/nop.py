#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op SRAM Generator tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerSRAMGeneratorTool, DummyHammerTool, \
        SRAMParameters, MMMCCorner
from hammer_tech import ExtraLibrary, Library
from typing import List, Dict


class NopSRAMGenerator(HammerSRAMGeneratorTool, DummyHammerTool):
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        return ExtraLibrary(prefix=None, library=Library())

tool = NopSRAMGenerator
