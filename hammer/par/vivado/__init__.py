#  Vivado place-and-route plugin for Hammer.
#
#  See LICENSE for licence details.

from typing import List

import os

from hammer.vlsi import HammerPlaceAndRouteTool, HammerToolStep

from hammer.common.vivado.vivado_core import VivadoCommon


class VivadoPlaceAndRoute(HammerPlaceAndRouteTool, VivadoCommon):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.setup_workspace,
            self.generate_board_defs,
            self.generate_paths_and_src_defs,
            self.generate_project_defs,
            self.generate_dcp_path_defs,
            self.generate_par_cmds,
            self.generate_mcs_cmds,
            self.run_place_and_route,
        ])

    def generate_dcp_path_defs(self) -> bool:
        dcp_files = ' '.join((os.path.abspath(fname)
                              for fname in self.input_files
                              if fname.endswith('.dcp')))
        self.append('set post_synth_dcp_path {}'.format(dcp_files))
        return True

    def generate_par_cmds(self) -> bool:
        self.append_file('par.tcl', None)
        return True

    def generate_mcs_cmds(self) -> bool:
        self.append_file('mcs.tcl', None)
        return True

    def run_place_and_route(self) -> bool:
        # Create tcl script.
        tcl_filename = os.path.join(self.run_dir, "par.tcl")

        with open(tcl_filename, "w") as f:
            f.write("\n".join(self.output))

        # create executable
        file_params = {
            'env_setup_script':
            self.get_setting('synthesis.vivado.setup_script'),
            'work_dir': self.run_dir,
            'vivado_cmd': self.get_setting('synthesis.vivado.binary'),
        }
        run_script = self.generate_run_script('run-par', file_params)

        # run executable
        self.run_executable([run_script])
        return True


tool = VivadoPlaceAndRoute
