from typing import Dict, List, Any

import os
import errno
import pkg_resources
from itertools import chain

from jinja2 import Template

from hammer_vlsi import HammerSynthesisTool, HammerToolStep, deepdict

_temp_dir = 'file_templates'
_synth_tag = 'vivado_synth'

class VivadoSynth(HammerSynthesisTool):


    _base_files = ['board.tcl', 'paths.tcl', 'project.tcl']
    
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.run_synthesis,
            self.run_place_and_route,
        ])

    def _get_dcp_path(self):
        return os.path.join(self.run_dir, _synth_tag, 'obj', 'post_opt.dcp')
    
    def setup_workspace(self, tag_name, add_files, run_script, **kwargs) -> bool:
        work_dir = os.path.join(self.run_dir, tag_name)
        # make working directory
        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(os.path.join(work_dir, 'obj'), exist_ok=True)
        # create symlink to constraint file
        cons_fname = self.get_setting('synthesis.vivado.constraints_file')
        cons_dir = os.path.join(work_dir, 'constrs')
        os.makedirs(cons_dir, exist_ok=True)
        cons_targ = os.path.join(cons_dir, os.path.basename(cons_fname))
        try:
            os.symlink(cons_fname, cons_targ)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(cons_targ)
                os.symlink(cons_fname, cons_targ)
            else:
                raise e
        # write tcl files and run script
        verilog_files = ' '.join((os.path.abspath(fname) for fname in self.input_files))
        file_params = {
            'board_name': self.get_setting('synthesis.vivado.board_name'),
            'part_fpga': self.get_setting('synthesis.vivado.part_fpga'),
            'part_board': self.get_setting('synthesis.vivado.part_board'),
            'board_files': self.get_setting('synthesis.vivado.board_files') or '""',
            'dcp_macro_dir': self.get_setting('synthesis.vivado.dcp_macro_dir') or '""',
            'work_dir': work_dir,
            'verilog_files': verilog_files,
            'top_module': self.top_module,
            'env_setup_script': self.get_setting('synthesis.vivado.setup_script'),
            'vivado_cmd': self.get_setting('synthesis.vivado.binary'),
        }
        file_params.update(kwargs)

        for fname in chain(self._base_files, add_files, [run_script]):
            content = pkg_resources.resource_string(__name__,
                                                    os.path.join(_temp_dir, fname)).decode('ascii')
            content = Template(content).render(**file_params)
            fpath = os.path.join(work_dir, fname)
            with open(fpath, 'w') as f:
                f.write(content)
            # make sure run script is executable
            if fname == run_script:
                os.chmod(fpath, 0o755)

        return work_dir
            
    def run_synthesis(self) -> bool:
        run_script = 'run-synthesis'
        add_files = ['prologue.tcl', 'init.tcl', 'syn.tcl', 'ip.tcl']
        work_dir = self.setup_workspace(_synth_tag, add_files, run_script)
        self.run_executable([os.path.join(work_dir, run_script)])
        return True

    def run_place_and_route(self) -> bool:
        run_script = 'run-par'
        add_files = ['synth_dcp_path.tcl', 'par.tcl', 'mcs.tcl']
        work_dir = self.setup_workspace('vivado_par', add_files, run_script,
                                        dcp_path=self._get_dcp_path())
        self.run_executable([os.path.join(work_dir, run_script)])
        return True
    
    def fill_outputs(self) -> bool:
        # This tool doesn't really have outputs
        self.output_files = [self._get_dcp_path()]
        return True

    
tool = VivadoSynth
 
