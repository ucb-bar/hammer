#  mocklvs.py
#  Mock LVS tool for testing.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerLVSTool, DummyHammerTool, HammerToolStep, HierarchicalMode
from typing import List, Dict
import os
import json


class MockLVS(HammerLVSTool, DummyHammerTool):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.get_ilms
        ])

    def fill_outputs(self) -> bool:
        return True

    def globally_waived_erc_rules(self) -> List[str]:
        return ["waived_error"]

    def erc_results_pre_waived(self) -> Dict[str, int]:
        return {"unwaived_error_0": 5, "unwaived_error_1": 10, "waived_error": 9}

    def lvs_results(self) -> List[str]:
        return ["VDD is connected to VSS"]

    def get_ilms(self) -> bool:
        if self.hierarchical_mode in [HierarchicalMode.Hierarchical, HierarchicalMode.Top]:
            with open(os.path.join(self.run_dir, "input_ilms.json"), "w") as f:
                f.write(json.dumps(list(map(lambda s: s.to_setting(), self.get_input_ilms()))))
        return True

tool = MockLVS
