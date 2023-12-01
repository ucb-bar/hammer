import json
import os
from decimal import Decimal
from typing import Dict, cast, List, Any, Iterator
import sys

from pydantic import BaseModel
import pytest

from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.logging import HammerVLSILogging
from hammer.utils import deepdict, add_dicts
from hammer.tech.specialcells import CellType, SpecialCell
from utils.stackup import StackupTestHelper
from utils.tech import HasGetTech
from utils.tool import HammerToolTestHelpers


class PowerStrapsTestContext(BaseModel):
    #straps_options: Dict[str, Any]
    temp_dir: str
    driver: hammer_vlsi.HammerDriver
    logger = HammerVLSILogging.context("")

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture()
def power_straps_test_context(tmp_path, tech_name: str, straps_options: Dict[str, Any]) -> Iterator[PowerStrapsTestContext]:
    """Initialize context by creating the temp_dir, driver, and loading mockpar."""
    tech_dir_base = str(tmp_path)
    json_path = os.path.join(tech_dir_base, "project.json")
    tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
    sys.path.append(tech_dir_base)
    tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

    def add_stackup_and_site(in_dict: Dict[str, Any]) -> Dict[str, Any]:
        out_dict = deepdict(in_dict)
        out_dict["stackups"] = [StackupTestHelper.create_test_stackup(8, StackupTestHelper.mfr_grid()).dict()]
        out_dict["sites"] = [StackupTestHelper.create_test_site(StackupTestHelper.mfr_grid()).dict()]
        out_dict["grid_unit"] = str(StackupTestHelper.mfr_grid())
        out_dict["special_cells"] = [SpecialCell(cell_type=CellType.TapCell, name=["FakeTapCell"]).dict()]
        return out_dict

    HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_stackup_and_site)

    with open(json_path, "w") as f:
        f.write(json.dumps(add_dicts({
            "vlsi.core.par_tool": "hammer.par.mockpar",
            "vlsi.core.technology": f"{tech_name}",
            "vlsi.core.node": "28",
            "vlsi.core.placement_site": "CoreSite",
            "vlsi.core.technology_path": [os.path.join(tech_dir, '..')],
            "vlsi.core.technology_path_meta": "append",
            "par.inputs.top_module": "dummy",
            "par.inputs.input_files": ("/dev/null",),
            "technology.core.stackup": "StackupWith8Metals",
            "technology.core.std_cell_rail_layer": "M1",
            "par.mockpar.temp_folder": tech_dir_base
        }, straps_options), cls=HammerJSONEncoder, indent=4))

    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(tech_dir_base, "log.txt"),
        obj_dir=tech_dir_base
    )
    driver = hammer_vlsi.HammerDriver(options)
    assert driver.load_par_tool()
    yield PowerStrapsTestContext(temp_dir=tech_dir_base, driver=driver)


def simple_straps_options() -> Dict[str, Any]:
    # TODO clean this up a bit

    strap_layers = ["M4", "M5", "M6", "M7", "M8"]
    pin_layers = ["M7", "M8"]
    track_width = 4
    track_width_M7 = 8
    track_width_M8 = 10
    track_spacing = 0
    track_spacing_M6 = 1
    power_utilization = 0.2
    power_utilization_M8 = 1.0
    track_start_M5 = 1
    track_offset_M5 = 1.2
    bottom_via_layer = "rail"

    # VSS comes before VDD
    nets = ["VSS", "VDD"]

    straps_options = {
        "vlsi.inputs.supplies": {
            "power": [{"name": "VDD", "pins": ["VDD"]}],
            "ground": [{"name": "VSS", "pins": ["VSS"]}],
            "VDD": "1.00 V",
            "GND": "0 V"
        },
        "par.power_straps_mode": "generate",
        "par.generate_power_straps_method": "by_tracks",
        "par.generate_power_straps_options.by_tracks": {
            "strap_layers": strap_layers,
            "pin_layers": pin_layers,
            "track_width": track_width,
            "track_width_M7": track_width_M7,
            "track_width_M8": track_width_M8,
            "track_spacing": track_spacing,
            "track_spacing_M6": track_spacing_M6,
            "power_utilization": power_utilization,
            "power_utilization_M8": power_utilization_M8,
            "track_start_M5": track_start_M5,
            "track_offset_M5": track_offset_M5,
            "bottom_via_layer": bottom_via_layer
        }
    }
    return straps_options


def multiple_domains_straps_options() -> Dict[str, Any]:
    strap_layers = ["M4", "M5", "M8"]
    pin_layers = ["M8"]
    track_width = 8
    track_spacing = 0
    power_utilization = 0.2
    power_utilization_M8 = 1.0
    bottom_via_layer = "rail"

    straps_options = {
        "vlsi.inputs.supplies": {
            "power": [{"name": "VDD", "pins": ["VDD"]}, {"name": "VDD2", "pins": ["VDD2"]}],
            "ground": [{"name": "VSS", "pins": ["VSS"]}],
            "VDD": "1.00 V",
            "GND": "0 V"
        },
        "par.power_straps_mode": "generate",
        "par.generate_power_straps_method": "by_tracks",
        "par.generate_power_straps_options.by_tracks": {
            "strap_layers": strap_layers,
            "pin_layers": pin_layers,
            "track_width": track_width,
            "track_spacing": track_spacing,
            "power_utilization": power_utilization,
            "power_utilization_M8": power_utilization_M8,
            "bottom_via_layer": bottom_via_layer
        }
    }
    return straps_options


class TestPowerStrapsTest(HasGetTech):
    @pytest.mark.parametrize("straps_options, tech_name", [(simple_straps_options(), "simple_by_tracks")])
    def test_simple_by_tracks_power_straps(self, power_straps_test_context) -> None:
        """ Creates simple power straps using the by_tracks method """
        c = power_straps_test_context
        success, par_output = c.driver.run_par()
        assert success

        par_tool = c.driver.par_tool
        # It's surpringly annoying to import mockpar.MockPlaceAndRoute, which is the class
        # that contains the parse_mock_power_straps_file() method, so we're just ignoring
        # that particular part of this
        assert isinstance(par_tool, hammer_vlsi.HammerPlaceAndRouteTool)
        stackup = par_tool.get_stackup()
        parsed_out = par_tool.parse_mock_power_straps_file()  # type: ignore
        entries = cast(List[Dict[str, Any]], parsed_out)

        # TODO: this is copied, avoid that
        strap_layers = ["M4", "M5", "M6", "M7", "M8"]
        pin_layers = ["M7", "M8"]
        track_width = 4
        track_width_M7 = 8
        track_width_M8 = 10
        track_spacing = 0
        track_spacing_M6 = 1
        power_utilization = 0.2
        power_utilization_M8 = 1.0
        track_start_M5 = 1
        track_offset_M5 = 1.2
        nets = ["VSS", "VDD"]

        for entry in entries:
            c.logger.debug("Power strap entry:" + str(entry))
            layer_name = entry["layer_name"]
            if layer_name == "M1":
                # Standard cell rails
                assert entry["tap_cell_name"] == "FakeTapCell"
                assert entry["bbox"] == []
                assert entry["nets"] == nets
                continue

            strap_width = Decimal(entry["width"])
            strap_spacing = Decimal(entry["spacing"])
            strap_pitch = Decimal(entry["pitch"])
            strap_offset = Decimal(entry["offset"])
            metal = stackup.get_metal(layer_name)
            min_width = metal.min_width
            group_track_pitch = strap_pitch / metal.pitch
            track_offset = Decimal(str(track_offset_M5)) if layer_name == "M5" else Decimal(0)
            track_start = Decimal(str(track_start_M5)) if layer_name == "M5" else Decimal(0)
            used_tracks = round(Decimal(strap_offset + strap_width + strap_spacing + strap_width + strap_offset - 2 * (track_offset + track_start * metal.pitch)) / metal.pitch) - 1
            if layer_name == "M4":
                assert entry["bbox"] == []
                assert entry["nets"] == nets
                # TODO more tests in a future PR
            elif layer_name == "M5":
                assert entry["bbox"] == []
                assert entry["nets"] == nets
                # Check that the requested tracks equals the used tracks
                requested_tracks = track_width * 2 + track_spacing
                assert used_tracks == requested_tracks
                # Spacing should be at least the min spacing
                min_spacing = metal.get_spacing_for_width(strap_width)
                assert strap_spacing >= min_spacing
                # TODO more tests in a future PR
            elif layer_name == "M6":
                assert entry["bbox"] == []
                assert entry["nets"] == nets
                # This is a sanity check that we didn't accidentally change something up above
                assert track_spacing_M6 == 1
                # We should be able to fit a track in between the stripes because track_spacing_M6 == 1
                wire_to_strap_spacing = (strap_spacing - min_width) / 2
                min_spacing = metal.get_spacing_for_width(strap_width)
                assert wire_to_strap_spacing >= min_spacing
                # Check that the requested tracks equals the used tracks
                requested_tracks = track_width * 2 + track_spacing_M6
                assert used_tracks == requested_tracks
                # Spacing should be at least the min spacing
                min_spacing = metal.get_spacing_for_width(strap_width)
                assert wire_to_strap_spacing >= min_spacing
                # TODO more tests in a future PR
            elif layer_name == "M7":
                assert entry["bbox"] == []
                assert entry["nets"] == nets
                # TODO more tests in a future PR
            elif layer_name == "M8":
                other_spacing = strap_pitch - (2 * strap_width) - strap_spacing
                # Track spacing should be 0
                assert track_spacing == 0
                # Test that the power straps are symmetric
                assert other_spacing == strap_spacing
                # Spacing should be at least the min spacing
                min_spacing = metal.get_spacing_for_width(strap_width)
                assert other_spacing >= min_spacing
                # Test that a slightly larger strap would be a DRC violation
                new_spacing = metal.get_spacing_for_width(strap_width + metal.grid_unit)
                new_pitch = (strap_width + metal.grid_unit + new_spacing) * 2
                assert strap_pitch < new_pitch
                # Test that the pitch does consume the right number of tracks
                required_pitch = Decimal(track_width_M8 * 2) * metal.pitch
                # 100% power utilzation should produce straps that consume 2*strap_width + strap_spacing tracks
                assert strap_pitch == required_pitch
            else:
                assert False, "Got the wrong layer_name: {}".format(layer_name)

    @pytest.mark.parametrize("straps_options, tech_name", [(multiple_domains_straps_options(), "multiple_domains")])
    def test_multiple_domains(self, power_straps_test_context) -> None:
        """ Tests multiple power domains """
        c = power_straps_test_context
        success, par_output = c.driver.run_par()
        assert success

        par_tool = c.driver.par_tool
        # It's surpringly annoying to import mockpar.MockPlaceAndRoute, which is the class
        # that contains the parse_mock_power_straps_file() method, so we're just ignoring
        # that particular part of this
        assert isinstance(par_tool, hammer_vlsi.HammerPlaceAndRouteTool)
        stackup = par_tool.get_stackup()
        parsed_out = par_tool.parse_mock_power_straps_file()  # type: ignore
        entries = cast(List[Dict[str, Any]], parsed_out)

        # There should be 1 std cell rail definition and 2 straps per layer (total 7)
        assert len(entries) == 7

        strap_layers = ["M4", "M5", "M8"]
        pin_layers = ["M8"]
        track_width = 8
        track_spacing = 0
        power_utilization = 0.2
        power_utilization_M8 = 1.0

        first_M5 = True
        first_M8 = True
        offset_M5 = Decimal(0)
        offset_M8 = Decimal(0)
        for entry in entries:
            c.logger.debug("Power strap entry:" + str(entry))
            layer_name = entry["layer_name"]
            if layer_name == "M1":
                # Standard cell rails
                assert entry["tap_cell_name"] == "FakeTapCell"
                assert entry["bbox"] == []
                assert entry["nets"] == ["VSS", "VDD", "VDD2"]
                continue

            strap_width = Decimal(entry["width"])
            strap_spacing = Decimal(entry["spacing"])
            strap_pitch = Decimal(entry["pitch"])
            strap_offset = Decimal(entry["offset"])
            metal = stackup.get_metal(layer_name)
            min_width = metal.min_width
            group_track_pitch = strap_pitch / metal.pitch
            used_tracks = round(Decimal(strap_offset + strap_width + strap_spacing + strap_width + strap_offset) / metal.pitch) - 1
            if layer_name == "M4":
                # This is just here to keep the straps from asserting due to a direction issue
                pass
            elif layer_name == "M5":
                # Test 2 domains
                assert entry["bbox"] == []
                if first_M5:
                    first_M5 = False
                    assert entry["nets"] == ["VSS", "VDD"]
                    offset_M5 = strap_offset
                else:
                    assert entry["nets"] == ["VSS", "VDD2"]
                    assert strap_offset == (strap_pitch / 2) + offset_M5
                # TODO more tests in a future PR
            elif layer_name == "M8":
                # Test 100% with two domains
                assert entry["bbox"] == []
                # Test that the pitch does consume the right number of tracks
                # This will be twice as large as the single-domain case because we'll offset another set
                required_pitch = Decimal(track_width * 4) * metal.pitch
                assert strap_pitch == required_pitch
                if first_M8:
                    first_M8 = False
                    assert entry["nets"] == ["VSS", "VDD"]
                    offset_M8 = strap_offset
                else:
                    assert entry["nets"] == ["VSS", "VDD2"]
                    assert strap_offset == (strap_pitch / 2) + offset_M8
                # TODO more tests in a future PR
            else:
                assert False, "Got the wrong layer_name: {}".format(layer_name)
