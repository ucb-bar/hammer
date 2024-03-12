from typing import Optional

from hammer import vlsi as hammer_vlsi, config as hammer_config
import hammer.technology.nop
from tests.utils.tool import DummyTool


class SDCDummyTool(hammer_vlsi.HasSDCSupport, DummyTool):
    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None


class TestSDC:
    def test_custom_sdc_constraints(self):
        """
        Test that custom raw SDC constraints work.
        """
        str1 = "create_clock foo -name myclock -period 10.0"
        str2 = "set_clock_uncertainty 0.123 [get_clocks myclock]"
        inputs = {
            "vlsi.inputs.custom_sdc_constraints": [
                str1,
                str2
            ]
        }

        tool = SDCDummyTool()
        tool.technology = hammer.technology.nop.NopTechnology()
        database = hammer_config.HammerDatabase()
        hammer_vlsi.HammerVLSISettings.load_builtins_and_core(database)
        database.update_project([inputs])
        tool.set_database(database)

        constraints = tool.sdc_pin_constraints.split("\n")
        assert str1 in constraints
        assert str2 in constraints
