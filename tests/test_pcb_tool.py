import json
import os
from typing import Dict, Any, Iterator

from pydantic import ConfigDict, BaseModel
import pytest

import hammer.pcb.generic
from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.logging import HammerVLSILogging


class PCBToolTextContext(BaseModel):
    driver: hammer_vlsi.HammerDriver
    temp_dir: str
    env: Dict[Any, Any] = {}
    model_config = ConfigDict(arbitrary_types_allowed=True)


@pytest.fixture()
def pcb_tool_test_context(tmp_path) -> Iterator[PCBToolTextContext]:
    """Initialize context by creating the temp_dir, driver, and loading the sram_generator tool."""
    HammerVLSILogging.clear_callbacks()
    temp_dir = str(tmp_path)
    json_path = os.path.join(temp_dir, "project.json")
    json_content: Dict[str, Any] = {
        "vlsi.core.technology": "hammer.technology.nop",
        "vlsi.core.pcb_tool": "hammer.pcb.generic",
        "pcb.inputs.top_module": "dummy",
        "pcb.submit.command": "local",
        "vlsi.inputs.bumps_mode": "manual",
        "vlsi.inputs.bumps": {
            "x": 5,
            "y": 4,
            "pitch": 123.4,
            "cell": "dummybump",
            "assignments": [
                {"name": "reset", "x": 1, "y": 1},
                {"name": "clock", "x": 2, "y": 1},
                {"name": "VDD", "x": 3, "y": 1},
                {"name": "VDD", "x": 4, "y": 1},
                {"name": "VSS", "x": 5, "y": 1},
                {"name": "data[0]", "x": 1, "y": 2},
                {"name": "data[1]", "x": 2, "y": 2},
                {"name": "data[2]", "x": 3, "y": 2},
                {"name": "VSS", "x": 4, "y": 2},
                {"name": "VDD", "x": 5, "y": 2},
                {"name": "data[3]", "x": 1, "y": 3},
                {"name": "valid", "x": 2, "y": 3},
                {"name": "ready", "x": 3, "y": 3},
                {"name": "NC", "x": 4, "y": 3, "no_connect": True},
                {"name": "VSS", "x": 5, "y": 3},
                {"name": "VDD", "x": 1, "y": 4},
                {"name": "VSS", "x": 2, "y": 4},
                {"name": "VDD", "x": 3, "y": 4},
                {"name": "VSS", "x": 4, "y": 4}
                # Note 5,4 is left out intentionally
            ]
        },
        "pcb.generic.footprint_type": "PADS-V9",
        "pcb.generic.schematic_symbol_type": "AltiumCSV",
        "technology.pcb.bump_pad_opening_diameter": 60,
        "technology.pcb.bump_pad_metal_diameter": 75
    }

    with open(json_path, "w") as f:
        f.write(json.dumps(json_content, cls=HammerJSONEncoder, indent=4))

    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(temp_dir, "log.txt"),
        obj_dir=temp_dir
    )
    yield PCBToolTextContext(driver=hammer_vlsi.HammerDriver(options), temp_dir=temp_dir)


class TestGenericPCBTool:
    def test_deliverables_exist(self, pcb_tool_test_context) -> None:
        """
        Test that a PADS-V9 footprint, Altium CSV, and pads CSV are created.
        This doesn't check the correctness of the deliverables.
        """
        c: PCBToolTextContext = pcb_tool_test_context
        assert c.driver.load_pcb_tool()
        assert c.driver.run_pcb()
        # Ignoring the type of this for the same reason as the power straps stuff below.
        # It's hard to get the concrete type of this tool that contains the methods used below.
        assert isinstance(c.driver.pcb_tool, hammer.pcb.generic.GenericPCBDeliverableTool)
        assert os.path.exists(c.driver.pcb_tool.output_footprint_filename)
        assert os.path.exists(c.driver.pcb_tool.output_footprint_csv_filename)
        assert os.path.exists(c.driver.pcb_tool.output_schematic_symbol_filename)
        assert os.path.exists(c.driver.pcb_tool.output_bom_builder_pindata_filename)

    # TODO add more checks:
    # - footprint pads should be mirrored relative to GDS
    # - Blank bumps should not show up
    # - test grouping
