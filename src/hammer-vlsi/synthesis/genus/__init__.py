#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer-vlsi plugin for Cadence Genus.
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

from hammer_vlsi import HammerTool
from hammer_vlsi import HammerSynthesisTool
from hammer_vlsi import HammerVLSILogging

import hammer_tech

from functools import reduce
from typing import Callable, Dict, List, Iterable

import os

class CadenceTool(HammerTool):
    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        return {
            "CDS_LIC_FILE": self.get_setting("cadence.CDS_LIC_FILE"),
            "CADENCE_HOME": self.get_setting("cadence.cadence_home")
        }

class Genus(HammerSynthesisTool, CadenceTool):
    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = dict(super().env_vars)
        new_dict.update({}) # TODO: stuffs
        return new_dict

    def do_run(self) -> bool:
        self.create_enter_script()

        top = self.top_module

        output = [] # type: List[str]
        def verbose_append(cmd: str) -> None:
            output.append("""puts "{0}" """.format(cmd.replace('"', '\"')))
            output.append(cmd)

        # TODO(edwardw): figure out how to make Genus quit instead of hanging on error.
        # Get libraries.
        lib_args = self.read_libs([
            self.liberty_lib_filter
        ], self.to_plain_item)
        verbose_append("set_db library {{ {} }}".format(" ".join(lib_args)))

        # Load input files and check that they are all Verilog.
        if not self.check_input_files([".v", ".sv"]):
            return False
        # We are switching working directories and Genus still needs to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        verbose_append("read_hdl {{ {} }}".format(" ".join(abspath_input_files)))

        # Elaborate/parse the RTL.
        verbose_append("elaborate")

        # TODO: generate constraints

        # Synthesize and map.
        verbose_append("syn_generic")
        verbose_append("syn_map")

        # TODO: generate reports

        # Write output files.
        output_verilog = os.path.join(self.run_dir, "{}.mapped.v".format(top))
        verbose_append("write_hdl > {}".format(output_verilog))
        verbose_append("write_script > {}.script.g".format(top))
        verbose_append("write_sdc > {}.mapped.sdc".format(top))
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

        return True


tool = Genus()
