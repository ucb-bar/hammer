#  Mock hammer-vlsi synthesis plugin to help test Hammer infrastructure
#  without proprietary/NDAed tools.
#  NOT FOR EXTERNAL/PUBLIC USE.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerSynthesisTool, DummyHammerTool, HammerToolStep
from hammer.utils import deepdict

from typing import Dict, List

import os


class MockSynth(HammerSynthesisTool, DummyHammerTool):
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        new_dict.update({})  # TODO: stuffs
        return new_dict

    def temp_file(self, filename: str) -> str:
        """Helper function to get the full path to a filename under temp_folder."""
        if self.get_setting("synthesis.mocksynth.temp_folder", nullvalue="") == "":
            raise ValueError("synthesis.mocksynth.temp_folder is not set correctly")
        return os.path.join(self.get_setting("synthesis.mocksynth.temp_folder"), filename)

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.step1,
            self.step2,
            self.step3,
            self.step4
        ])

    def fill_outputs(self) -> bool:
        self.output_files = list(self.input_files)
        return True

    def step1(self) -> bool:
        try:
            with open(self.temp_file("step1.txt"), "w") as f:
                f.write(self.get_setting("synthesis.mocksynth.step1"))
        except PermissionError:
            return False
        return True

    def step2(self) -> bool:
        try:
            with open(self.temp_file("step2.txt"), "w") as f:
                f.write(self.get_setting("synthesis.mocksynth.step2"))
        except PermissionError:
            return False
        return self.get_setting("synthesis.mocksynth.step2_succeeds")

    def step3(self) -> bool:
        try:
            with open(self.temp_file("step3.txt"), "w") as f:
                f.write(self.get_setting("synthesis.mocksynth.step3"))
        except PermissionError:
            return False
        return True

    def step4(self) -> bool:
        try:
            with open(self.temp_file("step4.txt"), "w") as f:
                f.write(self.get_setting("synthesis.mocksynth.step4"))
        except PermissionError:
            return False
        return True


tool = MockSynth
