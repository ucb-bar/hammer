#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# OpenROAD-flow par plugin for Hammer
#
# See LICENSE for licence details.

import glob
import os
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any

from hammer_logging import HammerVLSILogging
from hammer_utils import deepdict
from hammer_vlsi import HammerToolStep
from hammer_vlsi.vendor import OpenROADPlaceAndRouteTool

class OpenROADPlaceAndRoute(OpenROADPlaceAndRouteTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_design,
            self.floorplan_design,
            self.place_bumps, # nop
            self.place_tap_cells, # nop
            self.power_straps, # nop
            self.place_pins, # nop
            self.place_opt_design,
            self.clock_tree,
            self.add_fillers, # nop
            self.route_design,
            self.opt_design, # nop
            self.write_regs, # nop
            self.write_design,
        ])

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        assert super().do_pre_steps(first_step)
        self.cmds = []
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
        # TODO: no support for ILM
        self.output_ilms = []

        self.output_gds = self.output_gds_path()
        self.output_netlist = self.output_v_path()
        self.output_sim_netlist = self.output_v_path()

        # TODO: support outputting the following
        self.hcells_list = []
        self.output_all_regs = ""
        self.output_seq_cells = ""
        self.sdf_file = ""

        return True


    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["par.outputs.seq_cells"] = self.output_seq_cells
        outputs["par.outputs.all_regs"] = self.output_all_regs
        outputs["par.outputs.sdf_file"] = self.sdf_file
        return outputs

    def tool_config_prefix(self) -> str:
        return "par.openroad"

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def output_gds_path(self) -> str:
        return os.path.join(self.run_dir, 
          "results/{}/{}/6_final.gds".format(
            self.get_setting("vlsi.core.technology"),
            self.top_module))

    def output_v_path(self) -> str:
        return os.path.join(self.run_dir, 
          "results/{}/{}/5_route.v".format(
            self.get_setting("vlsi.core.technology"),
            self.top_module))

    def run_openroad(self) -> bool:
        run_script = os.path.join(self.run_dir, "run.sh")

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

        if bool(self.get_setting("par.openroad.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + \
                             " ".join(args))
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
    # par main steps
    #========================================================================
    def init_design(self) -> bool:
        # TODO: currently hardlinking the syn outputs, otherwise the 
        # OpenROAD-flow's default makefile will rebuild syn in this directory
        syn_dirs = {
          "results": self.syn_results_path(),
          "objects": self.syn_objects_path()
        }
        for syn_dir in ["results", "objects"]:
          for src in glob.glob(os.path.join(syn_dirs[syn_dir], "*")):
              dst = "{syn_dir}/{tech}/{name}/{base}".format(
                  syn_dir=syn_dir,
                  tech=self.get_setting("vlsi.core.technology"),
                  name=self.top_module,
                  base=os.path.basename(src))
              self.cmds += [
                  "rm -f {}".format(dst), 
                  "ln {} {}".format(src, dst)
              ]
        return True

    def floorplan_design(self) -> bool:
        # TODO: currently using OpenROAD's default floorplan script
        self.cmds += [
          "make DESIGN_CONFIG={conf} -f {make} floorplan".format(
            conf=self.design_config_path(), 
            make=self.openroad_flow_makefile_path()
        )]
        return True

    def place_bumps(self) -> bool:
        # TODO: currently using OpenROAD's default floorplan script
        return True

    def place_tap_cells(self) -> bool:
        # TODO: currently using OpenROAD's default floorplan script
        return True

    def power_straps(self) -> bool:
        # TODO: currently using OpenROAD's default floorplan script
        return True

    def place_pins(self) -> bool:
        # TODO: currently using OpenROAD's default floorplan script
        return True

    def place_opt_design(self) -> bool:
        # TODO: currently using OpenROAD's default place script
        self.cmds += [
          "make DESIGN_CONFIG={conf} -f {make} place".format(
            conf=self.design_config_path(), 
            make=self.openroad_flow_makefile_path()
        )]
        return True

    def clock_tree(self) -> bool:
        # TODO: currently using OpenROAD's default cts script
        self.cmds += [
          "make DESIGN_CONFIG={conf} -f {make} cts".format(
            conf=self.design_config_path(), 
            make=self.openroad_flow_makefile_path()
        )]
        return True

    def add_fillers(self) -> bool:
        # TODO: currently using OpenROAD's default cts script
        return True

    def route_design(self) -> bool:
        # TODO: currently using OpenROAD's default route script
        self.cmds += [
          "make DESIGN_CONFIG={conf} -f {make} route".format(
            conf=self.design_config_path(), 
            make=self.openroad_flow_makefile_path()
        )]
        return True

    def opt_design(self) -> bool:
        # TODO: currently no analagous OpenROAD default script
        return True

    def write_regs(self) -> bool:
        # TODO: currently using OpenROAD's default cts script
        return True

    def write_design(self) -> bool:
        # TODO: currently using OpenROAD's default finish script
        self.cmds += [
          "make DESIGN_CONFIG={conf} -f {make} finish".format(
            conf=self.design_config_path(), 
            make=self.openroad_flow_makefile_path()
        )]
        return True

tool = OpenROADPlaceAndRoute
