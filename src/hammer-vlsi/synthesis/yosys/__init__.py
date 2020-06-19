#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Yosys synthesis plugin for Hammer (as part of OpenROAD-flow installation).
#
# See LICENSE for licence details.

import os
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any

from hammer_logging import HammerVLSILogging
from hammer_utils import deepdict
from hammer_vlsi import HammerToolStep, TCLTool
from hammer_vlsi.vendor import OpenROADSynthesisTool


class YosysSynth(OpenROADSynthesisTool, TCLTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_environment,
            self.syn_generic,
            self.syn_map,
            self.add_tieoffs,
            self.write_regs,
            self.generate_reports,
            self.run_synthesis
        ])

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        new_dict.update({}) # TODO: stuffs
        return new_dict

    def fill_outputs(self) -> bool:
        # mapped verilog files
        self.output_files = [self.mapped_v_path()]
        # mapped sdc
        self.output_sdc = self.mapped_sdc_path()

        # TODO: actually generate the following for simulation
        self.output_all_regs = ""
        self.output_seq_cells = ""
        self.sdf_file = ""

        return True

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["synthesis.outputs.sdc"] = self.output_sdc
        outputs["synthesis.outputs.seq_cells"] = self.output_seq_cells
        outputs["synthesis.outputs.all_regs"] = self.output_all_regs
        outputs["synthesis.outputs.sdf_file"] = self.sdf_file
        return outputs

    def tool_config_prefix(self) -> str:
        return "synthesis.yosys"

    #=========================================================================
    # useful subroutines
    #=========================================================================
    def mapped_v_path(self) -> str:
        return os.path.join(self.run_dir, 
          "results/{}/{}/1_synth.v".format(
            self.get_setting("vlsi.core.technology"),
            self.top_module))

    def mapped_sdc_path(self) -> str:
        return os.path.join(self.run_dir,
          "results/{}/{}/1_synth.sdc".format(
            self.get_setting("vlsi.core.technology"),
            self.top_module))

    def synth_script_path(self) -> str:
        # TODO: generate this internally
        openroad = self.openroad_flow_path()
        return os.path.join(openroad, "flow/scripts/synth.tcl")

    #========================================================================
    # synthesis main steps
    #========================================================================
    def init_environment(self) -> bool:
        # TODO: currently using OpenROAD's default synthesis script
        return True

    def syn_generic(self) -> bool:
        # TODO: currently using OpenROAD's default synthesis script
        return True

    def syn_map(self) -> bool:
        # TODO: currently using OpenROAD's default synthesis script
        return True

    def add_tieoffs(self) -> bool:
        # TODO: currently using OpenROAD's default synthesis script
        return True

    def write_regs(self) -> bool:
        # TODO: currently using OpenROAD's default synthesis script
        return True

    def generate_reports(self) -> bool:
        # TODO: currently using OpenROAD's default synthesis script
        return True

    def run_synthesis(self) -> bool:
        run_script    = os.path.join(self.run_dir, "run.sh")
        makefile      = self.openroad_flow_makefile_path()
        design_config = self.design_config_path()
        synth_script  = self.synth_script_path()

        self.validate_openroad_installation()
        self.setup_openroad_rundir()
        self.create_design_config()

        with open(run_script, "w") as f:
            f.write(dd("""\
              #!/bin/bash
              cd "{rundir}"
              mkdir -p results/{tech}/{name}
              make DESIGN_CONFIG={conf} SYNTH_SCRIPT={script} -f {make} synth\
            """.format(
              rundir=self.run_dir,
              tech=self.get_setting("vlsi.core.technology"),
              name=self.top_module, 
              conf=design_config, 
              script=synth_script,
              make=makefile
            )))
        os.chmod(run_script, 0o755)

        if bool(self.get_setting("synthesis.yosys.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + \
                             " ".join(args))
        else:
            # Temporarily disable colours/tag to make run output more readable
            # TODO: think of a more elegant way to do this?
            HammerVLSILogging.enable_colour = False
            HammerVLSILogging.enable_tag = False
            self.run_executable([run_script]) # TODO: check for errors
            HammerVLSILogging.enable_colour = True
            HammerVLSILogging.enable_tag = True

        return True

tool = YosysSynth
