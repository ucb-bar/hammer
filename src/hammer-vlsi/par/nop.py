#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# See LICENSE for license details.
#
#  nop.py
#  No-op place and route tool.
#

from hammer_vlsi import HammerPlaceAndRouteTool, DummyHammerTool


class NopPlaceAndRoute(HammerPlaceAndRouteTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        self.output_ilms = []
        self.output_gds = "/dev/null"
        self.output_netlist = "/dev/null"
        self.power_nets = []
        self.ground_nets = []
        self.hcells_list = []
        return True


tool = NopPlaceAndRoute
