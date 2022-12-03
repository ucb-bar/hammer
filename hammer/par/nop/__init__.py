#  nop.py
#  No-op place and route tool.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerPlaceAndRouteTool, DummyHammerTool
from typing import List, Optional
from decimal import Decimal


class NopPlaceAndRoute(HammerPlaceAndRouteTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        self.output_ilms = []
        self.output_gds = "/dev/null"
        self.output_netlist = "/dev/null"
        self.output_sim_netlist = "/dev/null"
        self.hcells_list = []
        return True

    def specify_power_straps(self, layer_name: str, bottom_via_layer_name: str, blockage_spacing: Decimal, pitch: Decimal, width: Decimal, spacing: Decimal, offset: Decimal, bbox: Optional[List[Decimal]], nets: List[str], add_pins: bool) -> List[str]:
        return []

    def specify_std_cell_power_straps(self, blockage_spacing: Decimal, bbox: Optional[List[Decimal]], nets: List[str]) -> List[str]:
        return []


tool = NopPlaceAndRoute
