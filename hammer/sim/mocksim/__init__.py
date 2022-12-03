#  Mock hammer-vlsi sim plugin to help test Hammer infrastructure
#  without proprietary/NDAed tools.
#  NOT FOR EXTERNAL/PUBLIC USE.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerSimTool, DummyHammerTool, HammerToolStep, deepdict
from hammer.config import HammerJSONEncoder

from typing import Dict, List, Any, Optional
from decimal import Decimal

import os
import json


class MockSim(HammerSimTool, DummyHammerTool):

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        new_dict.update({})  # TODO: stuffs
        return new_dict

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.step1
        ])

    @property
    def force_regs_file_path(self) -> str:
        return os.path.join(self.run_dir, "{module}_regs.txt".format(module=self.top_module))

    def step1(self) -> bool:
        sim_file = os.path.join(self.run_dir, "{module}_regs.txt".format(module=self.top_module))
        with open(sim_file, "w") as f:
            f.write(self.get_setting("sim.inputs.level"))
            f.write("\n")
            for option in self.get_setting("sim.inputs.options"):
                f.write(option)
                f.write("\n")
        return True



tool = MockSim
