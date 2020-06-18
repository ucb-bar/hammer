#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Yosys synthesis plugin for Hammer (as part of OpenROAD installation).
#
#  See LICENSE for licence details.

from typing import List, Optional, Dict, Any

import os
import shutil
from textwrap import dedent as dd

from hammer_vlsi import HammerSynthesisTool, HammerToolStep, \
                        PlacementConstraintType, TimeValue, \
                        HasSDCSupport, TCLTool
import hammer_tech


class YosysSynth(HammerSynthesisTool, HasSDCSupport, TCLTool):
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.setup_env,
            self.create_synth_script,
            self.create_design_config,
            self.run_synthesis,
        ])

    def fill_outputs(self) -> bool:
        # mapped verilog files
        self.output_files = [self.mapped_v_path()]
        # mapped sdc
        self.output_sdc = self.mapped_sdc_path()

        #----------------------------------------
        # TODO: fix the following for simulation
        # file with list of all output pin of all registers in design
        self.output_all_regs = ""
        # file with list of all seq-cell paths in design
        self.output_seq_cells = ""
        # output sdf file
        self.sdf_file = ""
        #----------------------------------------

        # OpenROAD: also need to output design_config for later stages
        self.design_config = self.design_config_path()

        return True

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["synthesis.outputs.sdc"] = self.output_sdc
        outputs["synthesis.outputs.seq_cells"] = self.output_seq_cells
        outputs["synthesis.outputs.all_regs"] = self.output_all_regs
        outputs["synthesis.outputs.sdf_file"] = self.sdf_file
        # for OpenROAD only
        outputs["synthesis.outputs.design_config"] = self.design_config
        return outputs


    def tool_config_prefix(self) -> str:
        return "synthesis.yosys"

    def version_number(self, version: str) -> int:
        print("VERSION IS: {}".format(version))
        return version

    def post_synth_sdc(self) -> Optional[str]:
        # No post-synth SDC input for synthesis...
        return None

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


    def openroad_flow_path(self) -> str:
        """return the root of the OpenROAD-flow installation"""
        return os.path.realpath(os.path.join(os.environ['OPENROAD'], "../.."))

    def flow_makefile_path(self) -> str:
        openroad = self.openroad_flow_path()
        return os.path.join(openroad, "flow/Makefile")


    def synth_script_path(self) -> str:
        openroad = self.openroad_flow_path()
        return os.path.join(openroad, "flow/scripts/synth.tcl")


    def design_config_path(self) -> str:
        return os.path.join(self.run_dir, "design_config.mk")

    def clock_period_value(self) -> str:
        """this string is used in the makefile fragment used by OpenROAD"""

        for clock_port in self.get_setting("vlsi.inputs.clocks"):
            return TimeValue(clock_port["period"]).value_in_units("ns")

        raise Exception("no clock was found")


    def floorplan_bbox(self) -> str:
        """this string is used in the makefile fragment used by OpenROAD"""

        floorplan_constraints = self.get_placement_constraints()

        for constraint in floorplan_constraints:
            new_path = "/".join(constraint.path.split("/")[1:])

            if new_path == "":
                assert constraint.type == PlacementConstraintType.TopLevel, \
                    "Top must be a top-level/chip size constraint"
                margins = constraint.margins
                assert margins is not None
                # Set top-level chip dimensions.
                return "{} {} {} {}".format(
                    constraint.x, constraint.y, 
                    constraint.width, constraint.height)

        raise Exception("no top-level placement constraint was found")


    #========================================================================
    # synthesis steps below
    #========================================================================

    def setup_env(self) -> bool:
        """OPENROAD must be sucessfully installed before using it"""

        if "OPENROAD" not in os.environ:
            raise Exception("OPENROAD is not defined in environment!")
        if not shutil.which("klayout"):
            raise Exception("klayout is not in PATH")

        # TODO: for now, just symlink in the read-only OpenROAD stuff, since
        # the $OPENROAD/flow/Makefile expects these in the current directory.
        # in the future, $OPENROAD/flow/Makefile should use ?= instead of =
        openroad = self.openroad_flow_path()
        for subpath in ["platforms", "scripts", "util", "test"]:
          src = os.path.join(openroad, "flow/{}".format(subpath))
          dst = os.path.join(self.run_dir, subpath)

          try:
            os.remove(dst)
          except:
            pass

          os.symlink(src, dst)

        return True

    def create_synth_script(self) -> bool:
        """right now, just using the OpenROAD built-in synth script"""
        return True

    def create_design_config(self) -> bool:
        design_config = self.design_config_path()

        # Load input files and check that they are all Verilog.
        if not self.check_input_files([".v", ".sv"]):
            return False
        abspath_input_files = list(map(lambda name: 
          os.path.join(os.getcwd(), name), self.input_files))

        # Add any verilog_synth wrappers (which are needed in some 
        # technologies e.g. for SRAMs) which need to be synthesized.
        abspath_input_files += self.technology.read_libs([
            hammer_tech.filters.verilog_synth_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)

        # Generate constraints
        input_sdc = os.path.join(self.run_dir, "input.sdc")
        unit = self.get_time_unit().value_prefix + self.get_time_unit().unit
        with open(input_sdc, "w") as f:
            f.write("set_units -time {}\n".format(unit))
            f.write(self.sdc_clock_constraints)
            f.write("\n")
            f.write(self.sdc_pin_constraints)

        # TODO: i am blindly reading in all libs for all corners.
        extra_lefs = list(set(filter(lambda x: x is not None,
                        map(lambda x: x.library.lef_file,
                            self.technology.get_extra_libraries()))))
        extra_libs = list(set(filter(lambda x: x is not None,
                        map(lambda x: x.library.nldm_liberty_file,
                            self.technology.get_extra_libraries()))))

        with open(design_config, "w") as f:
            f.write(dd("""
            export DESIGN_NICKNAME = {design}
            export DESIGN_NAME     = {design}
            export PLATFORM        = {node}
            export VERILOG_FILES   = {verilogs}
            export SDC_FILE        = {sdc}

            export ADDITIONAL_LEFS = {extra_lefs}
            export ADDITIONAL_LIBS = {extra_libs}

            # These values must be multiples of placement site, which is
            # (x=0.19 y=1.4) for nangate45
            export DIE_AREA    = {die_area}
            export CORE_AREA   = {core_area}

            export CLOCK_PERIOD = {period}

            """.format(
              design=self.top_module,
              node=self.get_setting("vlsi.core.technology"),
              verilogs=" ".join(abspath_input_files),
              sdc=input_sdc,
              extra_lefs=" ".join(extra_lefs),
              extra_libs=" ".join(extra_libs),
              die_area=self.floorplan_bbox(),
              core_area=self.floorplan_bbox(),
              period=self.clock_period_value(),
            )))

        return True

    def run_synthesis(self) -> bool:
        run_script    = os.path.join(self.run_dir, "run.sh")
        makefile      = self.flow_makefile_path()
        design_config = self.design_config_path()
        synth_script  = self.synth_script_path()

        with open(run_script, "w") as f:
            f.write(dd("""\
            #!/bin/bash
            cd "{}"
            mkdir -p results/{}/{}
            make DESIGN_CONFIG={} SYNTH_SCRIPT={} -f {} synth
            """.format(
              self.run_dir,
              self.get_setting("vlsi.core.technology"), self.top_module, 
              design_config, synth_script, makefile)))
        os.chmod(run_script, 0o755)

        # run executable
        self.run_executable([run_script])

        return True

tool = YosysSynth
