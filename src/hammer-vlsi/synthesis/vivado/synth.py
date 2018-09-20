from typing import List

import os

from hammer_vlsi import HammerSynthesisTool, HammerToolStep

from .core import VivadoCommon


class VivadoSynth(HammerSynthesisTool, VivadoCommon):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.run_synthesis,
        ])

    def run_synthesis(self) -> bool:
        run_script = 'run-synthesis'
        add_files = ['prologue.tcl', 'init.tcl', 'syn.tcl']
        ip_file = self.get_setting('synthesis.vivado.ip_def_tcl')
        if ip_file:
            has_ip = True
            ip_file = os.path.abspath(ip_file)
        else:
            has_ip = False
        self.setup_workspace(add_files, run_script, dict(has_ip=has_ip))
        # symlink ip definition file
        if has_ip:
            _sym_link_force(ip_file, os.path.join(self.run_dir, 'ip.tcl'))
        # run executable
        self.run_executable([os.path.join(self.run_dir, run_script)])
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
