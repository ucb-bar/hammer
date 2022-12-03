#  nop.py
#  No-op SRAM Generator tool.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerSRAMGeneratorTool, DummyHammerTool, \
        SRAMParameters, MMMCCorner
from hammer.tech import ExtraLibrary, Library


class NopSRAMGenerator(HammerSRAMGeneratorTool, DummyHammerTool):
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        return ExtraLibrary(prefix=None, library=Library())

tool = NopSRAMGenerator
