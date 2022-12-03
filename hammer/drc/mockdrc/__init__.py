#  mockdrc.py
#  Mock DRC tool for testing.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerDRCTool, DummyHammerTool
from typing import List, Dict


class MockDRC(HammerDRCTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        return True

    def globally_waived_drc_rules(self) -> List[str]:
        return ["waived_error"]

    def drc_results_pre_waived(self) -> Dict[str, int]:
        return {"unwaived_error_0": 5, "unwaived_error_1": 10, "waived_error": 9}


tool = MockDRC
