#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer-vlsi plugin for Cadence Genus.
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

from hammer_vlsi import HammerTool
from hammer_vlsi import CadenceTool
from hammer_vlsi import HammerSynthesisTool
from hammer_vlsi import HammerVLSILogging

import hammer_tech

from functools import reduce
from typing import Callable, Dict, List, Iterable, Any

import os

class Genus(HammerSynthesisTool, CadenceTool):
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = dict(super().env_vars)
        new_dict.update({}) # TODO: stuffs
        return new_dict

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["synthesis.outputs.sdc"] = self.output_sdc
        return outputs

    def do_run(self) -> bool:
        self.create_enter_script()

        top = self.top_module

        output = []  # type: List[str]

        # Python doesn't have Scala's nice currying syntax (e.g. val newfunc = func(_, fixed_arg))
        def verbose_append(cmd: str) -> None:
            self.verbose_tcl_append(cmd, output)

        # TODO(edwardw): figure out how to make Genus quit instead of hanging on error.
        # Set up libraries.
        verbose_append("set_db library {{ {} }}".format(self.get_liberty_libs()))

        # Load input files and check that they are all Verilog.
        if not self.check_input_files([".v", ".sv"]):
            return False
        # We are switching working directories and Genus still needs to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        verbose_append("read_hdl {{ {} }}".format(" ".join(abspath_input_files)))

        # Elaborate/parse the RTL.
        verbose_append("elaborate")

        # Set units to pF and ns.
        # Must be done after elaboration.
        verbose_append("set_units -capacitance 1.0pF")
        verbose_append("set_load_unit -picofarads 1")
        verbose_append("set_units -time 1.0ns")

        # Apply constraints.
        constraint_files = [] # type: List[str]
        # Generate clock constraints.
        clock_constraints_fragment = os.path.join(self.run_dir, "clock_constraints_fragment.sdc")
        with open(clock_constraints_fragment, "w") as f:
            f.write(self.sdc_clock_constraints)
        constraint_files.append(clock_constraints_fragment)
        # Generate port constraints.
        pin_constraints_fragment = os.path.join(self.run_dir, "pin_constraints_fragment.sdc")
        with open(pin_constraints_fragment, "w") as f:
            f.write(self.sdc_pin_constraints)
        constraint_files.append(pin_constraints_fragment)

        verbose_append("create_constraint_mode -name func -sdc_files [list {}]".format(" ".join(constraint_files)))
        # Apparently it also needs to be sourced to work?
        for i in constraint_files:
            verbose_append("source -echo -verbose {}".format(i))

        # Synthesize and map.
        verbose_append("syn_generic")
        verbose_append("syn_map")

        # TODO: generate reports

        # Write output files.
        output_verilog = os.path.join(self.run_dir, "{}.mapped.v".format(top))
        output_sdc = os.path.join(self.run_dir, "{}.mapped.sdc".format(top))
        verbose_append("write_hdl > {}".format(output_verilog))
        verbose_append("write_script > {}.mapped.scr".format(top))
        verbose_append("write_sdc > {}".format(output_sdc))
        verbose_append("write_design -innovus -gzip_files {}".format(top))

        # Quit Genus.
        verbose_append("quit")

        # Create synthesis script.
        syn_tcl_filename = os.path.join(self.run_dir, "syn.tcl")

        with open(syn_tcl_filename, "w") as f:
            f.write("\n".join(output))

        # Build args.
        args = [
            self.get_setting("synthesis.genus.genus_bin"),
            "-f", syn_tcl_filename
        ]

        # Temporarily disable colours/tag to make run output more readable.
        # TODO: think of a more elegant way to do this?
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir) # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # Check that the mapped.v exists if the synthesis run was successful
        # TODO: move this check upwards?
        mapped_v = output_verilog
        if not os.path.isfile(mapped_v):
            raise ValueError("Output mapped verilog %s not found" % (mapped_v)) # better error?
        self.output_files = [mapped_v]

        if not os.path.isfile(output_sdc):
            raise ValueError("Output SDC %s not found" % (output_sdc)) # better error?
        self.output_sdc = output_sdc

        return True


tool = Genus()
