#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op place and route tool.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from hammer_vlsi import HammerPlaceAndRouteTool, DummyHammerTool


class Nop(HammerPlaceAndRouteTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        self.output_ilms = []
        self.output_gds = "/dev/null"
        self.output_netlist = "/dev/null"
        self.power_nets = []
        self.ground_nets = []
        self.hcells_list = []
        return True


tool = Nop
