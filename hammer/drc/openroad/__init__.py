# OpenROAD-flow klayout drc plugin for Hammer
#
# See LICENSE for licence details.

import glob
import os
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any

from hammer.logging import HammerVLSILogging
from hammer.utils import deepdict
from hammer.vlsi import HammerToolStep
from hammer.vlsi.vendor import OpenROADDRCTool

class OpenROADDRC(OpenROADDRCTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_design,
            self.run_drc_tool,
        ])

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        assert super().do_pre_steps(first_step)
        self.cmds = []  # type: List[str]
        return True

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_openroad()

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        new_dict.update({})  # TODO: stuffs
        return new_dict

    def fill_outputs(self) -> bool:
        return True

    def tool_config_prefix(self) -> str:
        return "drc.openroad"

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def run_openroad(self) -> bool:
        run_script = os.path.join(self.run_dir, "drc.sh")

        self.validate_openroad_installation()
        self.setup_openroad_rundir()

        with open(run_script, "w") as f:
            f.write(dd("""\
              #!/bin/bash
              cd "{rundir}"
              mkdir -p logs/{tech}/{name}
              mkdir -p objects/{tech}/{name}
              mkdir -p reports/{tech}/{name}
              mkdir -p results/{tech}/{name}
            """.format(
              rundir=self.run_dir,
              tech=self.get_setting("vlsi.core.technology"),
              name=self.top_module,
            )))
            f.write("\n".join(self.cmds))
        os.chmod(run_script, 0o755)

        if bool(self.get_setting("drc.openroad.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + \
                             " ".join(self.cmds))
        else:
            # Temporarily disable colors/tag to make run output more readable
            # TODO: think of a more elegant way to do this?
            HammerVLSILogging.enable_colour = False
            HammerVLSILogging.enable_tag = False
            self.run_executable([run_script]) # TODO: check for errors
            HammerVLSILogging.enable_colour = True
            HammerVLSILogging.enable_tag = True

        return True

    #========================================================================
    # drc main steps
    #========================================================================
    def init_design(self) -> bool:
        # TODO: currently hardlinking the par outputs, otherwise the
        # OpenROAD-flow's default makefile will rebuild syn in this directory
        par_dirs = {
          "results": self.par_results_path(),
          "objects": self.par_objects_path()
        }
        for par_dir in ["results", "objects"]:
          for src in glob.glob(os.path.join(par_dirs[par_dir], "*")):
              dst = "{par_dir}/{tech}/{name}/{base}".format(
                  par_dir=par_dir,
                  tech=self.get_setting("vlsi.core.technology"),
                  name=self.top_module,
                  base=os.path.basename(src))
              self.cmds += [
                  "rm -f {}".format(dst),
                  "ln {} {}".format(src, dst)
              ]
        return True

    def run_drc_tool(self) -> bool:
        # TODO: currently using OpenROAD's default drc script
        self.cmds += [
          "make DESIGN_CONFIG={conf} -f {make} drc".format(
            conf=self.design_config_path(),
            make=self.openroad_flow_makefile_path()
        )]
        return True

tool = OpenROADDRC
