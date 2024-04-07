import json
import os
from typing import Dict, Iterator, Any

from pydantic import ConfigDict, BaseModel
import pytest

from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder


class SimToolTestContext(BaseModel):
    driver: hammer_vlsi.HammerDriver
    temp_dir: str
    env: Dict[Any, Any] = {}
    model_config = ConfigDict(arbitrary_types_allowed=True)


@pytest.fixture()
def sim_tool_text_context(tmp_path) -> Iterator[SimToolTestContext]:
    """Initialize context by creating the temp_dir, driver, and loading mocksim."""
    temp_dir = str(tmp_path)
    json_path = os.path.join(temp_dir, "project.json")
    json_content = {
        "vlsi.core.sim_tool": "hammer.sim.mocksim",
        "vlsi.core.technology": "hammer.technology.nop",
        "sim.inputs.top_module": "dummy",
        "sim.inputs.input_files": ("/dev/null",),
        "sim.submit.command": "local",
        "sim.inputs.options": ["-debug"],
        "sim.inputs.level": "rtl",
        "sim.mocksim.temp_folder": temp_dir
    }

    with open(json_path, "w") as f:
        f.write(json.dumps(json_content, cls=HammerJSONEncoder, indent=4))

    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(temp_dir, "log.txt"),
        obj_dir=temp_dir
    )
    driver = hammer_vlsi.HammerDriver(options)
    yield SimToolTestContext(driver=driver, temp_dir=temp_dir)


class TestSimTool:
    def test_deliverables_exist(self, sim_tool_text_context) -> None:
        c = sim_tool_text_context
        assert c.driver.load_sim_tool()
        assert c.driver.run_sim()

        assert isinstance(c.driver.sim_tool, hammer_vlsi.HammerSimTool)
        # Ignore typing here because this is part of the mocksim API
        assert os.path.exists(c.driver.sim_tool.force_regs_file_path)  # type: ignore
