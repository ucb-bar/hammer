from typing import Dict, List, Any

import os
import errno
import pkg_resources
from itertools import chain

from jinja2 import Template

from hammer_vlsi import HammerSynthesisTool, HammerToolStep, deepdict


def _sym_link_force(source: str, dest: str) -> None:
    try:
        os.symlink(source, dest)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(dest)
            os.symlink(source, dest)
        else:
            raise e


class VivadoCommon(HammerSynthesisTool):

    _temp_dir = 'file_templates'
    _base_files = ['board.tcl', 'paths.tcl', 'project.tcl']
    synth_tag = 'vivado_synth'

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    def get_dcp_path(self) -> str:
        return os.path.join(self.run_dir, self.synth_tag, 'obj',
                            'post_opt.dcp')

    def setup_workspace(self, tag_name: str, add_files: List[str],
                        run_script: str, **kwargs: Any) -> bool:
        work_dir = os.path.join(self.run_dir, tag_name)
        # make working directory
        os.makedirs(work_dir, exist_ok=True)
        os.makedirs(os.path.join(work_dir, 'obj'), exist_ok=True)
        # create symlink to constraint file
        cons_fname = os.path.abspath(
            self.get_setting('synthesis.vivado.constraints_file'))
        cons_dir = os.path.join(work_dir, 'constrs')
        os.makedirs(cons_dir, exist_ok=True)
        cons_targ = os.path.join(cons_dir, os.path.basename(cons_fname))
        _sym_link_force(cons_fname, cons_targ)
        # write tcl files and run script
        verilog_files = ' '.join(
            (os.path.abspath(fname) for fname in self.input_files))
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
            work_dir,
            'verilog_files':
            verilog_files,
            'top_module':
            self.top_module,
            'env_setup_script':
            self.get_setting('synthesis.vivado.setup_script'),
            'vivado_cmd':
            self.get_setting('synthesis.vivado.binary'),
        }
        file_params.update(kwargs)

        for fname in chain(self._base_files, add_files, [run_script]):
            content = pkg_resources.resource_string(
                __name__, os.path.join(self._temp_dir, fname)).decode('ascii')
            content = Template(content).render(**file_params)
            fpath = os.path.join(work_dir, fname)
            with open(fpath, 'w') as f:
                f.write(content)
            # make sure run script is executable
            if fname == run_script:
                os.chmod(fpath, 0o755)

        return work_dir

    def run_place_and_route(self) -> bool:
        run_script = 'run-par'
        add_files = ['synth_dcp_path.tcl', 'par.tcl', 'mcs.tcl']
        work_dir = self.setup_workspace(
            'vivado_par', add_files, run_script, dcp_path=self.get_dcp_path())
        self.run_executable([os.path.join(work_dir, run_script)])
        return True


class VivadoSynth(VivadoCommon):
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
        work_dir = self.setup_workspace(
            self.synth_tag, add_files, run_script, has_ip=has_ip)
        # symlink ip definition file
        if has_ip:
            _sym_link_force(ip_file, os.path.join(work_dir, 'ip.tcl'))
        # run executable
        self.run_executable([os.path.join(work_dir, run_script)])
        return True

    def fill_outputs(self) -> bool:
        dcp_path = self.get_dcp_path()
        dcp_dir = os.path.dirname(dcp_path)
        self.output_files = [
            dcp_path,
            os.path.join(dcp_dir, self.top_module + '_post_synth.v')
        ]
        return True


class VivadoPlaceAndRoute(VivadoCommon):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.run_place_and_route,
        ])

    def run_place_and_route(self) -> bool:
        run_script = 'run-par'
        add_files = ['synth_dcp_path.tcl', 'par.tcl', 'mcs.tcl']
        work_dir = self.setup_workspace(
            'vivado_par', add_files, run_script, dcp_path=self.get_dcp_path())
        self.run_executable([os.path.join(work_dir, run_script)])
        return True

    def fill_outputs(self) -> bool:
        # This tool doesn't really have outputs
        self.output_files = [self.get_dcp_path()]
        return True


tool = VivadoSynth
