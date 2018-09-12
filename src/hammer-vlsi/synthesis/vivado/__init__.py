from hammer_vlsi import HammerSynthesisTool, HammerToolStep, deepdict

from typing import Dict, List, Any

import os

class VivadoSynth(HammerSynthesisTool):
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
            self.run_synthesis,
        ])

    def run_synthesis(self) -> bool:
        self.run_executable([
            os.path.join(self.tool_dir, "run-synthesis"),
            "-o", self.run_dir,
            "--top", self.top_module,
        ] + self.input_files)
        return True

    def fill_outputs(self) -> bool:
        # This tool doesn't really have outputs
        self.output_files = []
        return True

tool = VivadoSynth
