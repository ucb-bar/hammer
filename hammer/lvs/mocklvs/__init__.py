#  mocklvs.py
#  Mock LVS tool for testing.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerLVSTool, DummyHammerTool
from typing import List, Dict


class MockLVS(HammerLVSTool, DummyHammerTool):
    def fill_outputs(self) -> bool:
        return True

    def globally_waived_erc_rules(self) -> List[str]:
        return ["waived_error"]

    def erc_results_pre_waived(self) -> Dict[str, int]:
        return {"unwaived_error_0": 5, "unwaived_error_1": 10, "waived_error": 9}

    def lvs_results(self) -> List[str]:
        return ["VDD is connected to VSS"]


tool = MockLVS
