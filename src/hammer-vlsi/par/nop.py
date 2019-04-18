#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op place and route tool.
#
#  See LICENSE for licence details.

from hammer_vlsi import HammerPlaceAndRouteTool, DummyHammerTool


class NopPlaceAndRoute(HammerPlaceAndRouteTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        self.output_ilms = []
        self.output_gds = "/dev/null"
        self.output_netlist = "/dev/null"
        self.hcells_list = []
        return True


tool = NopPlaceAndRoute
