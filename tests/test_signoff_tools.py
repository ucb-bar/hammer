import json
import os
from typing import Dict, Any, Iterator

from pydantic import field_validator, ConfigDict, BaseModel
import pytest

from hammer import vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.logging import HammerVLSILogging


class SignoffToolTestContext(BaseModel):
    env: Dict[Any, Any] = {}
    driver: hammer_vlsi.HammerDriver
    tool_type: str
    temp_dir: str
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_validator("tool_type")
    @classmethod
    def check_tool_type(cls, tool_type):
        if tool_type not in ["drc", "lvs"]:
            raise NotImplementedError("Have not created a test for %s yet" % tool_type)


@pytest.fixture()
def signoff_test_context(tmp_path, tool_type: str) -> Iterator[SignoffToolTestContext]:
    """Initialize context by creating the temp_dir, driver, and loading the signoff tool."""
    HammerVLSILogging.clear_callbacks()
    temp_dir = str(tmp_path)
    json_path = os.path.join(temp_dir, "project.json")
    json_content = {
        "vlsi.core.technology": "hammer.technology.nop",
        "vlsi.core.%s_tool" % tool_type: "hammer.%s.mock%s" % (tool_type, tool_type),
        "%s.inputs.top_module" % tool_type: "dummy",
        "%s.inputs.layout_file" % tool_type: "/dev/null",
        "%s.temp_folder" % tool_type: temp_dir,
        "%s.submit.command" % tool_type: "local"
    }  # type: Dict[str, Any]
    if tool_type == "lvs":
        json_content.update({
            "lvs.inputs.schematic_files": ["/dev/null"],
            "lvs.inputs.hcells_list": []
        })

    with open(json_path, "w") as f:
        f.write(json.dumps(json_content, cls=HammerJSONEncoder, indent=4))

    options = hammer_vlsi.HammerDriverOptions(
        environment_configs=[],
        project_configs=[json_path],
        log_file=os.path.join(temp_dir, "log.txt"),
        obj_dir=temp_dir
    )
    driver = hammer_vlsi.HammerDriver(options)
    yield SignoffToolTestContext(driver=driver, tool_type=tool_type, temp_dir=temp_dir)


class TestHammerDRCTool:
    @pytest.mark.parametrize("tool_type", ["drc"])
    def test_get_results(self, signoff_test_context) -> None:
        """ Test that a local submission produces the desired output."""
        c = signoff_test_context
        assert c.driver.load_drc_tool()
        assert c.driver.run_drc()
        assert isinstance(c.driver.drc_tool, hammer_vlsi.HammerDRCTool)
        # This magic 15 should be the sum of the two unwaived DRC violation
        # counts hardcoded in drc/mockdrc.py.
        assert c.driver.drc_tool.signoff_results() == 15


class TestHammerLVSTool:
    @pytest.mark.parametrize("tool_type", ["lvs"])
    def test_get_results(self, signoff_test_context) -> None:
        """ Test that a local submission produces the desired output."""
        c = signoff_test_context
        assert c.driver.load_lvs_tool()
        assert c.driver.run_lvs()
        assert isinstance(c.driver.lvs_tool, hammer_vlsi.HammerLVSTool)
        # This magic 16 should be the sum of the two unwaived ERC violation
        # counts and the LVS violation hardcoded in lvs/mocklvs.py.
        assert c.driver.lvs_tool.signoff_results() == 16
