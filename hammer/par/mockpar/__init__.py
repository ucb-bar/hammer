#  Mock hammer-vlsi place-and-route plugin to help test Hammer infrastructure
#  without proprietary/NDAed tools.
#  NOT FOR EXTERNAL/PUBLIC USE.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerPlaceAndRouteTool, DummyHammerTool, HammerToolStep, deepdict
from hammer.config import HammerJSONEncoder

from typing import Dict, List, Any, Optional
from decimal import Decimal

import os
import json


class MockPlaceAndRoute(HammerPlaceAndRouteTool, DummyHammerTool):

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        new_dict.update({})  # TODO: stuffs
        return new_dict

    def temp_file(self, filename: str) -> str:
        """Helper function to get the full path to a filename under temp_folder."""
        if self.get_setting("par.mockpar.temp_folder", nullvalue="") == "":
            raise ValueError("par.mockpar.temp_folder is not set correctly")
        return os.path.join(self.get_setting("par.mockpar.temp_folder"), filename)

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.power_straps
        ])

    def power_straps(self) -> bool:
        power_straps_tcl = os.path.join(self.run_dir, "power_straps.tcl")
        with open(power_straps_tcl, "w") as f:
            f.write("\n".join(self.create_power_straps_tcl()))
        return True

    def parse_mock_power_straps_file(self) -> List[Dict[str, Any]]:
        power_straps_tcl = os.path.join(self.run_dir, "power_straps.tcl")
        output = []  # type: List[Dict[str, Any]]
        with open(power_straps_tcl, "r") as f:
            for line in f.readlines():
                output.append(json.loads(line))
        return output

    def specify_power_straps(self, layer_name: str, bottom_via_layer_name: str, blockage_spacing: Decimal, pitch: Decimal, width: Decimal, spacing: Decimal, offset: Decimal, bbox: Optional[List[Decimal]], nets: List[str], add_pins: bool) -> List[str]:
        self._power_straps_check_index(layer_name)
        output_dict = {
            "layer_name": layer_name,
            "bottom_via_layer_name": bottom_via_layer_name,
            "blockage_spacing": str(blockage_spacing),
            "pitch": str(pitch),
            "width": str(width),
            "spacing": str(spacing),
            "offset": str(offset),
            "bbox": [] if bbox is None else list(map(str, bbox)),
            "nets": list(map(str, nets)),
            "add_pins": add_pins
        }
        return [json.dumps(output_dict, cls=HammerJSONEncoder)]

    def specify_std_cell_power_straps(self, blockage_spacing: Decimal, bbox: Optional[List[Decimal]], nets: List[str]) -> List[str]:
        layer_name = self.get_setting("technology.core.std_cell_rail_layer")
        self._power_straps_check_index(layer_name)
        output_dict = {
            "layer_name": layer_name,
            "tap_cell_name": self.get_setting("technology.core.tap_cell_rail_reference"),
            "bbox": [] if bbox is None else list(map(str, bbox)),
            "nets": list(map(str, nets))
        }
        return [json.dumps(output_dict, cls=HammerJSONEncoder)]

    def fill_outputs(self) -> bool:
        self.output_gds = "/dev/null"
        self.output_ilms = []
        self.output_netlist = "/dev/null"
        self.output_sim_netlist = "/dev/null"
        self.hcells_list = []
        return True


tool = MockPlaceAndRoute
