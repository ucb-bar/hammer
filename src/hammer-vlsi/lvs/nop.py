#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op LVS tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerLVSTool, DummyHammerTool
from typing import List, Dict


class NopLVS(HammerLVSTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        return True

    def globally_waived_erc_rules(self) -> List[str]:
        return []

    def erc_results_pre_waived(self) -> Dict[str, int]:
        return {}

    def lvs_results(self) -> List[str]:
        return []


tool = NopLVS
