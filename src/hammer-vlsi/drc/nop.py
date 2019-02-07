#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op DRC tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerDRCTool, DummyHammerTool
from typing import List, Dict


class NopDRC(HammerDRCTool, DummyHammerTool):
    def globally_waived_drc_rules(self) -> List[str]:
        return []

    def drc_results_pre_waived(self) -> Dict[str, int]:
        return {}

    def fill_outputs(self) -> bool:
        return True


tool = NopDRC
