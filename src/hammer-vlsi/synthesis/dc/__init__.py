#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer-vlsi plugin for Synopsys DC.
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

from hammer_vlsi import HammerSynthesisTool
from hammer_vlsi import HammerVLSILogging

import hammer_tech

from functools import reduce
from typing import Callable, List, Iterable

import os
import re
import subprocess

class DC(HammerSynthesisTool):
    # TODO(edwardw): move this to a common place since this is not DC specific
    def args_from_library(self, func: Callable[[hammer_tech.Library], List[str]], arg_name: str, extra_funcs: List[Callable[[str], str]] = [], lib_filters: List[Callable[[hammer_tech.Library], bool]] = []) -> Iterable[str]:
        """
        Generate a list of --arg <variable> --arg <variable> arguments for calling shell scripts by filtering the list of libraries.

        :param func: Function to call to extract the desired component of the lib.
        :param arg_name: Argument name e.g. "--foobar" would generate --foobar 1 --foobar 2 ...
        :param extra_funcs: List of extra functions to call before wrapping them in the arg prefixes.
        :param lib_filters: Filters to filter the list of libraries before selecting desired results from them.
        :return: List of arguments to pass to a shell script
        """
        filtered_libs = reduce(lambda libs, func: filter(func, libs), lib_filters, self.technology.config.libraries)

        lib_results = list(reduce(lambda a, b: a+b, list(map(func, filtered_libs))))

        # Uniqueify results.
        # TODO: think about whether this really belongs here and whether we always need to uniqueify.
        # This is here to get stuff working since some CAD tools dislike duplicated arguments (e.g. duplicated stdcell lib, etc).
        lib_results = list(set(lib_results))

        lib_results_with_extra_funcs = reduce(lambda arr, func: map(func, arr), extra_funcs, lib_results)

        # Turn them into --arg arguments.
        return reduce(lambda a, b: a + b, list(map(lambda res: [arg_name, res], lib_results_with_extra_funcs)))

    # TODO(edwardw): this also belong in a common place
    def args_from_tarball_libraries(self, func: Callable[[hammer_tech.Library], List[str]], arg_name: str, arg_type: str, is_file: bool) -> Iterable[str]:
        """Build a list of --arg_name arguments by filtering tarball-extracted arguments from the libraries, filtered by supplies."""
        return self.args_from_library(func, arg_name, extra_funcs=[self.technology.prepend_tarball_dir, self.make_check_isfile(arg_type) if is_file else self.make_check_isdir(arg_type)], lib_filters=[self.filter_for_supplies])

    # TODO(edwardw): move this to common
    def filter_for_supplies(self, lib: hammer_tech.Library) -> bool:
        if lib.supplies is None:
            self.logger.warning("Lib %s has no supplies annotation! Using anyway." % (lib.serialize()))
            return True
        return self.get_setting("vlsi.inputs.supplies.VDD") == lib.supplies.VDD and self.get_setting("vlsi.inputs.supplies.GND") == lib.supplies.GND

    # TODO(edwardw): move this to synopsys common
    def generate_tcl_preferred_routing_direction(self):
        """
        Generate a TCL fragment for setting preferred routing directions.
        """
        output = []

        # Suppress PSYN-882 ("Warning: Consecutive metal layers have the same preferred routing direction") while the layer routing is being built.
        output.append("set suppress_errors  [concat $suppress_errors  [list PSYN-882]]")

        for library in self.technology.config.libraries:
            if library.metal_layers is not None:
                for layer in library.metal_layers:
                    output.append("set_preferred_routing_direction -layers {{ {0} }} -direction {1}".format(layer.name, layer.preferred_routing_direction))

        output.append("set suppress_errors  [lminus $suppress_errors  [list PSYN-882]]")
        output.append("") # Add newline at the end
        return "\n".join(output)

    # TODO(edwardw): move to a common place
    @staticmethod
    def make_check_isdir(description: str = "Path") -> Callable[[str], str]:
        """
        Utility function to generate functions which check whether a path exists.
        """
        def check_isdir(path: str) -> str:
            if not os.path.isdir(path):
                raise ValueError("%s %s is not a directory or does not exist" % (description, path))
            else:
                return path
        return check_isdir

    # TODO(edwardW): move to a common place
    @staticmethod
    def make_check_isfile(description: str = "File") -> Callable[[str], str]:
        """
        Utility function to generate functions which check whether a path exists.
        """
        def check_isfile(path: str) -> str:
            if not os.path.isfile(path):
                raise ValueError("%s %s is not a file or does not exist" % (description, path))
            else:
                return path
        return check_isfile

    def disable_congestion_map(self) -> None:
        """Disables the congestion map generation in rm_dc_scripts/dc.tcl since it requires a GUI and licences.
        """
        dc_tcl_path = os.path.join(self.run_dir, "rm_dc_scripts/dc.tcl")

        with open(dc_tcl_path) as f:
            dc_tcl = f.read()

        congestion_map_fragment = """
  # Use the following to generate and write out a congestion map from batch mode
  # This requires a GUI session to be temporarily opened and closed so a valid DISPLAY
  # must be set in your UNIX environment.

  if {[info exists env(DISPLAY)]} {
    gui_start
"""
        congestion_map_search = re.escape(congestion_map_fragment)
        # We want to capture & replace that condition.
        # Unfortunately, we can't replace within a group, so we'll have to replace around it.
        # e.g. foobarbaz -> foo123baz requires (foo)bar(baz) -> \1 123 \2 -> foo123baz
        cond = re.escape("[info exists env(DISPLAY)]")
        congestion_map_search_and_capture = "(" + congestion_map_search.replace(cond, ")(" + cond + ")(") + ")"

        output = re.sub(congestion_map_search_and_capture, "\g<1>false\g<3>", dc_tcl)

        f = open(dc_tcl_path, 'w')
        f.write(output)
        f.close()

    def do_run(self) -> bool:
        # TODO(edwardw): move most of this to Synopsys common since it's not DC-specific.
        # Locate reference methodology tarball.
        synopsys_rm_tarball = os.path.join(self.get_setting("synopsys.rm_dir"), "DC-RM_%s.tar" % (self.get_setting("synthesis.dc.dc_version")))
        if not os.path.exists(synopsys_rm_tarball):
            # TODO: convert these to logger calls
            raise FileNotFoundError("Expected reference methodology tarball not found at %s. Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a DC reference methodology. If these tarballs have been pre-downloaded, you can set synopsys.rm_dir instead of generating them yourself." % (synopsys_rm_tarball))

        # Locate DC binary.
        dc_bin = self.get_setting("synthesis.dc.dc_bin")
        if not os.path.isfile(dc_bin):
            self.logger.error("DC binary not found as expected at {0}".format(dc_bin))
            # TODO(edwardw): think about how to pass extra/more useful info like the specific type of error (e.g. FileNotFoundError)
            return False

        # Load input files.
        verilog_args = self.input_files
        error = False
        for v in verilog_args:
            if not (v.endswith(".v") or v.endswith(".sv")):
                self.logger.error("Non-verilog input {0} detected! DC only supports Verilog inputs.".format(v))
                error = True
            if not os.path.isfile(v):
                self.logger.error("Input file {0} does not exist!".format(v))
                error = True
        if error:
            return False

        # Generate preferred_routing_directions.
        preferred_routing_directions_fragment = os.path.join(self.run_dir, "preferred_routing_directions.tcl")
        with open(preferred_routing_directions_fragment, "w") as f:
            f.write(self.generate_tcl_preferred_routing_direction())

        # Get timing libraries.
        def select_timing_db(lib: hammer_tech.Library) -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_library_file is not None:
                return [lib.ccs_library_file]
            elif lib.nldm_library_file is not None:
                return [lib.nldm_library_file]
            else:
                return []
        timing_args = self.args_from_tarball_libraries(select_timing_db, "--lib", "CCS/NLDM timing db", is_file=True)

        # Get all the milkyway libraries.
        def select_milkyway_lib(lib: hammer_tech.Library) -> List[str]:
            if lib.milkyway_lib_in_dir is not None:
                return [os.path.dirname(lib.milkyway_lib_in_dir)]
            else:
                return []
        # Turn them into --milkyway arguments.
        milkyway_args = self.args_from_tarball_libraries(select_milkyway_lib, "--milkyway", "Milkyway lib", is_file=False)

        # Get milkyway techfiles.
        def select_milkyway_tfs(lib: hammer_tech.Library) -> List[str]:
            if lib.milkyway_techfile is not None:
                return [lib.milkyway_techfile]
            else:
                return []
        # Turn them into --milkyway arguments.
        tf_args = list(self.args_from_tarball_libraries(select_milkyway_tfs, "--tf", "Milkyway techfile", is_file=True))
        if len(tf_args) == 0:
            raise ValueError("Must have at least one milkyway tech file")

        # TLU min/max cap
        def select_tlu_max_cap(lib: hammer_tech.Library) -> List[str]:
            if lib.tluplus_files is not None and lib.tluplus_files.max_cap is not None:
                return [lib.tluplus_files.max_cap]
            else:
                return []
        def select_tlu_min_cap(lib: hammer_tech.Library) -> List[str]:
            if lib.tluplus_files is not None and lib.tluplus_files.min_cap is not None:
                return [lib.tluplus_files.min_cap]
            else:
                return []
        # Turn them into --milkyway arguments.
        tlu_max_args = self.args_from_tarball_libraries(select_tlu_max_cap, "--tlu_max", "tlu max_cap", is_file=True)
        tlu_min_args = self.args_from_tarball_libraries(select_tlu_min_cap, "--tlu_min", "tlu min_cap", is_file=True)

        # Pre-extract the tarball (so that we can make TCL modifications in Python)
        extract_args = [
            "tar", "-xf", synopsys_rm_tarball, "-C", self.run_dir, "--strip-components=1"
        ]
        self.run_executable(extract_args)

        # Disable the DC congestion map if needed.
        if not self.get_setting("synthesis.dc.enable_congestion_map"):
            self.disable_congestion_map()

        # Build args.
        args = [
            os.path.join(self.tool_dir, "tools", "run-synthesis"),
            "--dc", dc_bin,
            "--MGLS_LICENSE_FILE", self.get_setting("synopsys.MGLS_LICENSE_FILE"),
            "--SNPSLMD_LICENSE_FILE", self.get_setting("synopsys.SNPSLMD_LICENSE_FILE"),
            "--preferred_routing_directions_fragment", preferred_routing_directions_fragment,
            "--find_regs_tcl", os.path.join(self.tool_dir, "tools", "find-regs.tcl"),
            "--run_dir", self.run_dir,
            "--top", self.top_module
        ]
        args.extend(verilog_args)
        args.extend(timing_args)
        args.extend(milkyway_args)
        args.extend(tf_args)
        args.extend(tlu_max_args)
        args.extend(tlu_min_args)

        # Temporarily disable colours/tag to make DC run output more readable.
        # TODO: think of a more elegant way to do this?
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args) # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # Check that the mapped.v exists if the synthesis run was successful
        mapped_v = "%s/results/%s.mapped.v" % (self.run_dir, self.top_module)
        if not os.path.isfile(mapped_v):
            raise ValueError("Output mapped verilog %s not found" % (mapped_v)) # better error?
        self.output_files = [mapped_v]

        return True

tool = DC()
