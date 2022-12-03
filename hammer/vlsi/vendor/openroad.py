# common tool settings and functions for OpenROAD tools
#
# See LICENSE for licence details.

from decimal import Decimal
from functools import reduce
import os
import re
import shutil
from subprocess import Popen, PIPE
from textwrap import dedent as dd
from typing import List, Optional, Dict, Set, Union

from hammer.utils import add_dicts
from hammer.vlsi import HasSDCSupport, HammerSynthesisTool, \
    HammerPlaceAndRouteTool, HammerDRCTool, \
    PlacementConstraintType, TimeValue, \
    TCLTool, HammerTool
import hammer.tech as hammer_tech


class OpenROADTool(HasSDCSupport, TCLTool, HammerTool):
    """ Mix-in trait with functions useful for OpenROAD-flow tools."""

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from 
        super().env_vars!
        """
        list_of_vars = self.get_setting("openroad.extra_env_vars")
        assert isinstance(list_of_vars, list)
        return reduce(add_dicts, [dict(super().env_vars)] + list_of_vars, {})

    def validate_openroad_installation(self) -> None:
        """
        make sure OPENROAD env-var is set, and klayout is in the path (since
        klayout is not installed with OPENROAD as of version 1.1.0. this 
        should be called in steps that actually run tools or touch filepaths
        """
        if not shutil.which("openroad"):
            raise Exception("openroad is not in PATH")
        if not shutil.which("klayout"):
            raise Exception("klayout is not in PATH")

    def openroad_flow_path(self) -> str:
        """return the root of the OpenROAD-flow installation"""
        self.validate_openroad_installation()
        return os.path.realpath(os.path.join(os.environ['OPENROAD'], "../.."))

    def openroad_flow_makefile_path(self) -> str:
        """drive OpenROAD-flow's top-level Makefile from hammer"""
        openroad = self.openroad_flow_path()
        return os.path.join(openroad, "flow/Makefile")

    def syn_rundir_path(self) -> str:
        # TODO: leaking info from driver into this tool. figure out a better
        # way to get "syn-rundir" than duplicating a constant
        return os.path.realpath(os.path.join(self.run_dir, "../syn-rundir"))

    def syn_objects_path(self) -> str:
        """where the intermediate synthesis output objects are located"""
        return os.path.join(self.syn_rundir_path(), "objects",
                            self.get_setting("vlsi.core.technology"),
                            self.top_module)

    def syn_results_path(self) -> str:
        """where the intermediate synthesis final results are located"""
        return os.path.join(self.syn_rundir_path(), "results",
                            self.get_setting("vlsi.core.technology"),
                            self.top_module)

    def design_config_path(self) -> str:
        """
        the initial design_config is written by the synthesis step. any other
        tool must refer to this design_config
        """
        return os.path.join(self.syn_rundir_path(), "design_config.mk")

    def par_rundir_path(self) -> str:
        # TODO: leaking info from driver into this tool. figure out a better
        # way to get "par-rundir" than duplicating a constant
        return os.path.realpath(os.path.join(self.run_dir, "../par-rundir"))

    def par_objects_path(self) -> str:
        """where the intermediate par output objects are located"""
        return os.path.join(self.par_rundir_path(), "objects",
                            self.get_setting("vlsi.core.technology"),
                            self.top_module)

    def par_results_path(self) -> str:
        """where the intermediate par final results are located"""
        return os.path.join(self.par_rundir_path(), "results",
                            self.get_setting("vlsi.core.technology"),
                            self.top_module)

    def version_number(self, version: str) -> int:
        """get OPENROAD-flow's version from one of its header files"""

        filepath = os.path.join(self.openroad_flow_path(),
                                "tools/OpenROAD/include/openroad/Version.hh")
        process = Popen(["grep", "OPENROAD_VERSION", filepath], stdout=PIPE)
        (output, err) = process.communicate()
        code = process.wait()
        assert code == 0, "grep failed with code {}".format(code)
        text = output.decode("utf-8")
        match = re.search(r"OPENROAD_VERSION \"(\d+)\.(\d+)\.(\d+)\"", text)
        if match is None:
            raise Exception("OPENROAD_VERSION could not be found!")
        return int(match.group(1)) * 10000 + \
               int(match.group(2)) * 100 + \
               int(match.group(3))

    def setup_openroad_rundir(self) -> bool:
        """
        OpenROAD expects several files/dirs in the current run_dir, so we 
        symlink them in from the OpenROAD-flow installation
        """
        # TODO: for now, just symlink in the read-only OpenROAD stuff, since
        # the $OPENROAD/flow/Makefile expects these in the current directory.
        # in the future, $OPENROAD/flow/Makefile should use ?= instead of =
        # for these symlinked dirs
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


class OpenROADSynthesisTool(HammerSynthesisTool, OpenROADTool):
    """ Mix-in trait with functions for OpenROAD-flow synthesis tools."""

    # =========================================================================
    # overrides from parent classes
    # =========================================================================
    # @property
    # don't overrride this!
    # def post_synth_sdc(self) -> Optional[str]:
    #     return None

    # =========================================================================
    # OpenROAD synthesis-specific stuff
    # =========================================================================
    def _clock_period_value(self) -> str:
        """this string is used in the makefile fragment used by OpenROAD"""

        assert len(self.get_clock_ports()) == 1, "openroad only supports 1 root clock"
        return str(self.get_clock_ports()[0].period.value_in_units("ns"))

    def _floorplan_bbox(self) -> str:
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

    def create_design_config(self) -> bool:
        """
        the design-config is the main configuration for the OpenROAD built-in
        scripts. initially, we are using OpenROAD's tool scripts as-is, so
        we need to create a design-config that their scripts understand. the
        synthesis tool is the only tool that will write this
        """
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

        # TODO: i am blindly reading in all libs for all corners. but this is
        #       not a performance issue for nangate45
        extra_lefs = set([extra_lib.library.lef_file for extra_lib in self.technology.get_extra_libraries()
                          if extra_lib.library.lef_file is not None])
        extra_libs = set([extra_lib.library.nldm_liberty_file for extra_lib in self.technology.get_extra_libraries()
                          if extra_lib.library.nldm_liberty_file is not None])

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
                die_area=self._floorplan_bbox(),
                core_area=self._floorplan_bbox(),
                period=self._clock_period_value(),
            )))
        return True


class OpenROADPlaceAndRouteTool(HammerPlaceAndRouteTool, OpenROADTool):
    """ Mix-in trait with functions for OpenROAD-flow par tools."""

    # =========================================================================
    # overrides from parent classes
    # =========================================================================
    def specify_power_straps(self, layer_name: str,
                             bottom_via_layer_name: str, blockage_spacing: Decimal, pitch: Decimal,
                             width: Decimal, spacing: Decimal, offset: Decimal,
                             bbox: Optional[List[Decimal]], nets: List[str],
                             add_pins: bool) -> List[str]:
        # TODO: currently using openroad's powerstrap script
        return []

    def specify_std_cell_power_straps(self, blockage_spacing: Decimal,
                                      bbox: Optional[List[Decimal]], nets: List[str]) -> List[str]:
        # TODO: currently using openroad's powerstrap script
        return []


class OpenROADDRCTool(HammerDRCTool, OpenROADTool):
    """ Mix-in trait with functions for OpenROAD-flow drc tools."""

    # =========================================================================
    # overrides from parent classes
    # =========================================================================
    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None

    def globally_waived_drc_rules(self) -> List[str]:
        # TODO: i suppose the actual implementation should implement this
        return []

    def drc_results_pre_waived(self) -> Dict[str, int]:
        # TODO: i suppose the actual implementation should implement this
        return {}
