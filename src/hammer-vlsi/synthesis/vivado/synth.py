from typing import List

import os

from hammer_vlsi import HammerSynthesisTool, HammerToolStep

from .core import VivadoCommon


class VivadoSynth(HammerSynthesisTool, VivadoCommon):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.setup_workspace,
            self.generate_board_defs,
            self.generate_paths_and_src_defs,
            self.generate_project_defs,
            self.generate_prologue,
            self.generate_ip_defs,
            self.generate_messaging_params,
            self.generate_synth_cmds,
            self.run_synthesis,
        ])

    def generate_prologue(self) -> bool:
        self.append_file('prologue.tcl', None)
        return True

    def generate_ip_defs(self) -> bool:
        ip_file = self.get_setting('synthesis.vivado.ip_def_tcl')
        if ip_file:
            _sym_link_force(ip_file, os.path.join(self.run_dr, 'ip.tcl'))
            self.append_file('init.tcl', None)
        return True

    def generate_messaging_params(self) -> bool:
        self.append_file('msg.tcl', None)
        return True

    def generate_synth_cmds(self) -> bool:
        ip_file = self.get_setting('synthesis.vivado.ip_def_tcl')
        if ip_file:
            self.append(
                'read_ip [glob -directory $ipdir [file join * {*.xci}]]')
        self.append_file('syn.tcl', None)
        return True

    def run_synthesis(self) -> bool:
        # Create synthesis script.
        syn_tcl_filename = os.path.join(self.run_dir, "syn.tcl")

        with open(syn_tcl_filename, "w") as f:
            f.write("\n".join(self.output))

        # create executable
        file_params = {
            'env_setup_script':
            self.get_setting('synthesis.vivado.setup_script'),
            'work_dir': self.run_dir,
            'vivado_cmd': self.get_setting('synthesis.vivado.binary'),
        }
        run_script = self.generate_run_script('run-synthesis', file_params)

        # run executable
        self.run_executable([run_script])
        return True

    def fill_outputs(self) -> bool:
        dcp_path = os.path.join(self.run_dir, 'obj', 'post_opt.dcp')
        dcp_dir = os.path.dirname(dcp_path)
        self.output_files = [
            dcp_path,
            os.path.join(dcp_dir, self.top_module + '_post_synth.v')
        ]
        return True


tool = VivadoSynth
