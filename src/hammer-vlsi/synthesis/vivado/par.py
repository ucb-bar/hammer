from typing import List

import os

from hammer_vlsi import HammerPlaceAndRouteTool, HammerToolStep

from .core import VivadoCommon


class VivadoPlaceAndRoute(HammerPlaceAndRouteTool, VivadoCommon):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.run_place_and_route,
        ])

    def run_place_and_route(self) -> bool:
        run_script = 'run-par'
        add_files = ['synth_dcp_path.tcl', 'par.tcl', 'mcs.tcl']
        dcp_files = ' '.join((os.path.abspath(fname)
                              for fname in self.input_files
                              if fname.endswith('.dcp')))
        print('input files: ', self.input_files)
        self.setup_workspace(add_files, run_script, dict(dcp_path=dcp_files))
        self.run_executable([os.path.join(self.run_dir, run_script)])
        return True

    def fill_outputs(self) -> bool:
        # This tool doesn't really have outputs
        self.output_files = []
        return True


tool = VivadoPlaceAndRoute
