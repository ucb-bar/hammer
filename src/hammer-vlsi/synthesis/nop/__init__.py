#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Mock hammer-vlsi synthesis plugin to help test Hammer infrastructure without
#  proprietary/NDAed tools.
#  NOT FOR EXTERNAL/PUBLIC USE.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from hammer_vlsi import HammerSynthesisTool, HammerToolStep

from typing import List

class NopSynth(HammerSynthesisTool):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([])

    def fill_outputs(self) -> bool:
        # This tool doesn't really have outputs
        self.output_files = []
        return True

tool = NopSynth
