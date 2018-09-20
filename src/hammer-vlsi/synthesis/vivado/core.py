from typing import Dict, List

import os
import errno
import pkg_resources
from itertools import chain

from jinja2 import Template

from hammer_vlsi import deepdict


class VivadoCommon(object):
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    def sym_link_force(self, source: str, dest: str) -> None:
        try:
            os.symlink(source, dest)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(dest)
                os.symlink(source, dest)
            else:
                raise e

    def setup_workspace(self, add_files: List[str], run_script: str,
                        extra_params: Dict[str, str]) -> None:
        # make working directory
        os.makedirs(self.run_dir, exist_ok=True)
        os.makedirs(os.path.join(self.run_dir, 'obj'), exist_ok=True)
        # create symlink to constraint file
        cons_fname = os.path.abspath(
            self.get_setting('synthesis.vivado.constraints_file'))
        cons_dir = os.path.join(self.run_dir, 'constrs')
        os.makedirs(cons_dir, exist_ok=True)
        cons_targ = os.path.join(cons_dir, os.path.basename(cons_fname))
        self.sym_link_force(cons_fname, cons_targ)
        # write tcl files and run script
        verilog_files = ' '.join((os.path.abspath(fname)
                                  for fname in self.input_files
                                  if fname.endswith('.v')))
        file_params = {
            'board_name':
            self.get_setting('synthesis.vivado.board_name'),
            'part_fpga':
            self.get_setting('synthesis.vivado.part_fpga'),
            'part_board':
            self.get_setting('synthesis.vivado.part_board'),
            'board_files':
            self.get_setting('synthesis.vivado.board_files') or '""',
            'dcp_macro_dir':
            self.get_setting('synthesis.vivado.dcp_macro_dir') or '""',
            'work_dir':
            self.run_dir,
            'verilog_files':
            verilog_files,
            'top_module':
            self.top_module,
            'env_setup_script':
            self.get_setting('synthesis.vivado.setup_script'),
            'vivado_cmd':
            self.get_setting('synthesis.vivado.binary'),
        }
        file_params.update(extra_params)

        for fname in chain(['board.tcl', 'paths.tcl', 'project.tcl'],
                           add_files, [run_script]):
            content = pkg_resources.resource_string(
                __name__, os.path.join('file_templates',
                                       fname)).decode('ascii')
            content = Template(content).render(**file_params)
            fpath = os.path.join(self.run_dir, fname)
            with open(fpath, 'w') as f:
                f.write(content)
            # make sure run script is executable
            if fname == run_script:
                os.chmod(fpath, 0o755)
