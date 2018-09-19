from typing import Dict, List, Any

import os
import errno
import pkg_resources

from jinja2 import Template

from hammer_vlsi import HammerSynthesisTool, HammerToolStep, deepdict

_temp_dir = 'file_templates'
_run_script = 'run-synthesis'


class VivadoSynth(HammerSynthesisTool):


    _files = ['board.tcl', 'paths.tcl', 'project.tcl', 'prologue.tcl', 'init.tcl',
              'syn.tcl', 'ip.tcl', _run_script]
    
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.setup_workspace,
            self.run_synthesis,
        ])

    def setup_workspace(self) -> bool:
        work_dir = os.path.join(self.run_dir, 'vivado')
        # make working directory
        os.makedirs(work_dir, exist_ok=True)
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
            'work_dir': work_dir,
            'verilog_files': verilog_files,
            'top_module': self.top_module,
            'env_setup_script': self.get_setting('synthesis.vivado.setup_script'),
            'vivado_cmd': self.get_setting('synthesis.vivado.binary'),
        }

        for fname in self._files:
            content = pkg_resources.resource_string(__name__,
                                                    os.path.join(_temp_dir, fname)).decode('ascii')
            content = Template(content).render(**file_params)
            fpath = os.path.join(work_dir, fname)
            with open(fpath, 'w') as f:
                f.write(content)
            # make sure run script is executable
            if fname == _run_script:
                os.chmod(fpath, 0o755)

        return True
            
    def run_synthesis(self) -> bool:
        work_dir = os.path.join(self.run_dir, 'vivado')
        self.run_executable([os.path.join(work_dir, _run_script)])
        return True

    def fill_outputs(self) -> bool:
        work_dir = os.path.join(self.run_dir, 'vivado')
        # This tool doesn't really have outputs
        self.output_files = [os.path.join(work_dir, 'obj', 'post_opt.dcp')]
        return True

    
tool = VivadoSynth
 
