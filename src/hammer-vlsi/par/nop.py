#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  nop.py
#  No-op place and route tool.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from typing import List

from hammer_vlsi import HammerPlaceAndRouteTool, HammerToolStep


class Nop(HammerPlaceAndRouteTool):
    def fill_outputs(self) -> bool:
        self.output_ilms = []
        return True

    @property
    def steps(self) -> List[HammerToolStep]:
        return []


tool = Nop
