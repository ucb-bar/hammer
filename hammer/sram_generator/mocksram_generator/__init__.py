#  mocksram_generator.py
#  Mock SRAM Generator tool for testing.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerSRAMGeneratorTool, DummyHammerTool, \
        SRAMParameters, MMMCCorner
from hammer.tech import ExtraLibrary, Library
from typing import List, Dict

class MockSRAMGenerator(HammerSRAMGeneratorTool, DummyHammerTool):
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        return ExtraLibrary(prefix=None,
               library=Library(gds_file="sram{d}x{w}_{v}V_{c}C.gds".format(
                   d=params.depth, w=params.width,
                   v=corner.voltage.value, c=corner.temp.value)))

tool = MockSRAMGenerator
