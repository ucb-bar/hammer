#  Common code shared between all Vivado plugins.
#
#  See LICENSE for licence details.

from typing import Dict, List, Optional

import os
import shutil
from abc import ABCMeta

from hammer.utils import deepdict
from hammer.vlsi import HammerTool


class VivadoCommon(HammerTool, metaclass=ABCMeta):
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    def append(self, cmd: str) -> None:
        self.tcl_append(cmd, self.output)

    def setup_workspace(self) -> bool:
        # make object directory
        os.makedirs(os.path.join(self.run_dir, 'obj'), exist_ok=True)
        # copy constraint file
        cons_fname = os.path.abspath(
            self.get_setting('synthesis.vivado.constraints_file'))
        cons_dir = os.path.join(self.run_dir, 'constrs')
        os.makedirs(cons_dir, exist_ok=True)
        cons_targ = os.path.join(cons_dir, os.path.basename(cons_fname))
        shutil.copyfile(cons_fname, cons_targ)

        self.output = []  # type: List[str]
        return True

    def get_file_contents(self, file_name: str,
                          file_params: Optional[Dict[str, str]]) -> str:
        if os.path.isabs(file_name):
            fname = file_name  # type: str
        else:
            raise RuntimeError("No clue what's going on here - tool_dir no longer exists, this plugin should use Python resources")
            # fname = os.path.join(self.tool_dir, 'file_templates', file_name)
        with open(fname, 'r') as f:
            content = f.read()
            if file_params:
                content = content.format(**file_params)
            return content

    def append_file(self, file_name: str, file_params: Optional[Dict[str, str]]) -> None:
        for line in self.get_file_contents(file_name,
                                           file_params).splitlines():
            self.append(line)

    def generate_board_defs(self) -> bool:
        file_params = {
            'board_name': self.get_setting('synthesis.vivado.board_name'),
            'part_fpga': self.get_setting('synthesis.vivado.part_fpga'),
            'part_board': self.get_setting('synthesis.vivado.part_board'),
        }
        self.append_file('board.tcl', file_params)
        return True

    def generate_paths_and_src_defs(self) -> bool:
        verilog_files = ' '.join((os.path.abspath(fname)
                                  for fname in self.input_files
                                  if fname.endswith('.v')))
        file_params = {
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
        }
        self.append_file('paths.tcl', file_params)
        return True

    def generate_project_defs(self) -> bool:
        file_params = {
            'part_fpga': self.get_setting('synthesis.vivado.part_fpga'),
            'part_board': self.get_setting('synthesis.vivado.part_board'),
        }
        self.append_file('project.tcl', file_params)
        return True

    def generate_run_script(self, script_name: str,
                            file_params: Dict[str, str]) -> str:
        content = self.get_file_contents(script_name, file_params)
        fpath = os.path.join(self.run_dir, script_name)
        with open(fpath, 'w') as f:
            f.write(content)
        os.chmod(fpath, 0o755)
        return fpath
