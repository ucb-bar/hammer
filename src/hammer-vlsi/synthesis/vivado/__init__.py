from hammer_vlsi import HammerSynthesisTool, HammerToolStep, deepdict
from typing import Dict, List, Any
import os
class VivadoSynth(HammerSynthesisTool):
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        new_dict.update({
            "VIVADO_BIN": self.get_setting("synthesis.vivado.vivado_bin"),
            "VIVADO_SETUP_SH": self.get_setting("synthesis.vivado.vivado_setup_script"),
        })
        return new_dict
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
        self.output_files = ["post_opt.dcp"]
        return True

tool = VivadoSynth
 
