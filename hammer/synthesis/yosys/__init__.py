# Yosys synthesis plugin for Hammer (as part of OpenROAD-flow installation).
# mostly adoped from OpenLANE scripts found here: https://github.com/The-OpenROAD-Project/OpenLane/tree/master/scripts
#
# See LICENSE for licence details.

from hammer.vlsi.vendor import OpenROADTool, OpenROADSynthesisTool

from hammer.vlsi import HammerTool, HammerToolStep, HammerToolHookAction, HierarchicalMode, TCLTool
from hammer.vlsi.constraints import MMMCCorner, MMMCCornerType
from hammer.utils import VerilogUtils, optional_map
from hammer.vlsi import HammerSynthesisTool
from hammer.logging import HammerVLSILogging
from hammer.vlsi import MMMCCornerType
import hammer.tech as hammer_tech

from typing import Dict, List, Any, Optional, Callable
import importlib.resources
from pathlib import Path

import hammer.tech.specialcells as specialcells
from hammer.tech.specialcells import CellType, SpecialCell

import os
import json
from collections import Counter

class YosysSynth(HammerSynthesisTool, OpenROADTool, TCLTool):

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
            self.write_outputs
        ])

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_yosys()

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = dict(super().env_vars)
        new_dict["YOSYS_BIN"] = self.get_setting("synthesis.yosys.yosys_bin")
        return new_dict

    @property
    def post_synth_sdc(self) -> Optional[str]:
        # No post-synth SDC input for synthesis...
        return None

    @property
    def all_regs_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_paths.json")

    @property
    def all_cells_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_cells.json")

    def fill_outputs(self) -> bool:
        # TODO: actually generate the following for simulation
        # Check that the regs paths were written properly if the write_regs step was run
        self.output_seq_cells = self.all_cells_path
        self.output_all_regs = self.all_regs_path
        if self.ran_write_regs:
            if not os.path.isfile(self.all_cells_path):
                raise ValueError("Output find_regs_cells.json %s not found" % (self.all_cells_path))

            if not os.path.isfile(self.all_regs_path):
                raise ValueError("Output find_regs_paths.json %s not found" % (self.all_regs_path))

            # if not self.process_reg_paths(self.all_regs_path):
            #     self.logger.error("Failed to process all register paths")
        else:
            self.logger.info("Did not run write_regs")

        # Check that the synthesis outputs exist if the synthesis run was successful
        mapped_v = self.mapped_v_path
        self.output_files = [mapped_v]
        self.output_sdc = self.mapped_sdc_path
        # self.sdf_file = self.output_sdf_path
        if self.ran_write_outputs:
            if not os.path.isfile(mapped_v):
                raise ValueError("Output mapped verilog %s not found" % (mapped_v)) # better error?

            if not os.path.isfile(self.mapped_sdc_path):
                raise ValueError("Output SDC %s not found" % (self.mapped_sdc_path)) # better error?

            # if not os.path.isfile(self.output_sdf_path):
            #     raise ValueError("Output SDF %s not found" % (self.output_sdf_path))
        else:
            self.logger.info("Did not run write_outputs")

        return True

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["synthesis.outputs.sdc"] = self.output_sdc
        outputs["synthesis.outputs.seq_cells"] = self.output_seq_cells
        outputs["synthesis.outputs.all_regs"] = self.output_all_regs
        outputs["synthesis.outputs.sdf_file"] = ""
        return outputs

    def tool_config_prefix(self) -> str:
        return "synthesis.yosys"

    #=========================================================================
    # useful subroutines
    #=========================================================================
    @property
    def mapped_v_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.v".format(self.top_module))

    @property
    def mapped_sdc_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.sdc".format(self.top_module))

    @property
    def mapped_blif_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.blif".format(self.top_module))

    def get_timing_libs(self, corner: Optional[MMMCCorner] = None) -> str:
        """
        Helper function to get the list of ASCII timing .lib files in space separated format.

        :param corner: Optional corner to consider. If supplied, this will use filter_for_mmmc to select libraries that
        match a given corner (voltage/temperature).
        :return: List of lib files separated by spaces
        """
        pre_filters = optional_map(corner, lambda c: [self.filter_for_mmmc(voltage=c.voltage,
                                                                           temp=c.temp)])  # type: Optional[List[Callable[[hammer_tech.Library],bool]]]

        lib_args = self.technology.read_libs([hammer_tech.filters.timing_lib_with_ecsm_filter],
                                             hammer_tech.HammerTechnologyUtils.to_plain_item,
                                             extra_pre_filters=pre_filters)

        # lib files are often in a zipped format, so unzip them if they are
        lib_args_unzipped = self.technology.extract_gz_files(lib_args)

        return " ".join(lib_args_unzipped)

    def run_yosys(self) -> bool:
        """Close out the synthesis script and run Yosys."""
        # Quit Yosys.
        self.append("exit")

        # Create synthesis script.
        syn_tcl_filename = os.path.join(self.run_dir, "syn.tcl")

        with open(syn_tcl_filename, "w") as f:
            f.write("\n".join(self.output))

        # Build args.
        args = [
            self.get_setting("synthesis.yosys.yosys_bin"),
            "-c", syn_tcl_filename,
        ]

        if bool(self.get_setting("synthesis.yosys.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + " ".join(args))
        else:
            # Temporarily disable colours/tag to make run output more readable.
            # TODO: think of a more elegant way to do this?
            HammerVLSILogging.enable_colour = False
            HammerVLSILogging.enable_tag = False
            self.run_executable(args, cwd=self.run_dir) # TODO: check for errors and deal with them
            HammerVLSILogging.enable_colour = True
            HammerVLSILogging.enable_tag = True

        return True

    def write_sdc_file(self) -> bool:
        with open(self.mapped_sdc_path,'w') as f:
            # custom sdc constraints
            if self.driver_cell is not None:
                f.write(f"set_driving_cell {self.driver_cell}\n" )
                # TODO: generate this hard-coded 5
                f.write("set_load 5\n")
        return True

    #========================================================================
    # synthesis main steps
    #========================================================================
    def init_environment(self) -> bool:

        # set variables to match global variables in OpenLANE
        time_unit = self.get_time_unit().value_prefix + self.get_time_unit().unit
        clock_port = self.get_clock_ports()[0]
        self.clock_port_name = clock_port.name
        time_unit = "ps" # yosys requires time units in ps
        self.clock_period = int(clock_port.period.value_in_units(time_unit))
        self.clock_uncertainty = int(clock_port.period.value_in_units(time_unit))
        self.clock_transition = 0.15 # SYNTH_CLOCK_TRANSITION

        self.synth_cap_load = 33.5 # SYNTH_CAP_LOAD
        self.max_fanout = 5 # default SYNTH_MAX_FANOUT = 5


        self.driver_cell = None
        driver_cells = self.technology.get_special_cell_by_type(CellType.Driver)
        if len(driver_cells) == 0:
            self.logger.warning("Driver cells are unspecified and will not be added during synthesis.")
        elif driver_cells[0].input_ports is None or driver_cells[0].output_ports is None:
            self.logger.warning("Driver cell input and output ports are unspecified and will not be added during synthesis.")
        else:
            self.driver_cell = driver_cells[0].name[0]
            self.driver_ports_in = driver_cells[0].input_ports[0]
            self.driver_ports_out = driver_cells[0].output_ports[0]

        # Yosys commands only take a single lib file
        #   so use typical corner liberty file
        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        try:
            corner_tt = next((corner for corner in corners if corner.type == MMMCCornerType.Extra), None)
        except:
            raise ValueError("An extra corner is required for Yosys.")

        self.liberty_files_tt = self.get_timing_libs(corner_tt)

        self.append("yosys -import")

        # replaces undef (x) constants with defined (0/1) constants.
        self.append("setundef -zero")

        # We are switching working directories and Yosys still needs to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))  # type: List[str]

        # Add any verilog_synth wrappers (which are needed in some technologies e.g. for SRAMs) which need to be
        # synthesized.
        abspath_input_files += self.technology.read_libs([
            hammer_tech.filters.verilog_synth_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)

        for verilog_file in abspath_input_files:
            self.append(f"read_verilog -sv {verilog_file}")

        liberty_files = self.technology.read_libs([hammer_tech.filters.timing_lib_with_ecsm_filter], hammer_tech.HammerTechnologyUtils.to_plain_item)
        for lib_file in liberty_files:
            self.append(f"read_liberty -lib {lib_file}")

        return True

    def syn_generic(self) -> bool:
        # TODO: is there a better way to do this? like self.get_setting()
        if self._database.has_setting("synthesis.yosys.latch_map_file"):
            latch_map = f"techmap -map {self.get_setting('synthesis.yosys.latch_map_file')}"
        else:  # TODO: make the else case better
            latch_map = ""

        self.block_append(f"""
        # TODO: verify this command, it was in yosys manual but not in OpenLANE script
        yosys proc
        hierarchy -check -top {self.top_module}

        synth -top {self.top_module}

        # Optimize the design
        opt -purge

        # Technology mapping of latches
        {latch_map}

        # Technology mapping of flip-flops
        """)
        for liberty_file in self.liberty_files_tt.split():
            self.verbose_append(f"dfflibmap -liberty {liberty_file}")
        self.verbose_append("opt")

        # merges shareable resources into a single resource. A SAT solver
        # is used to determine if two resources are share-able.
        # self.append('share -aggressive')

        self.write_sdc_file()
        return True

    def syn_map(self) -> bool:

        self.block_append(f"""
        # Technology mapping for cells
        # ABC supports multiple liberty files, but the hook from Yosys to ABC doesn't
        # TODO: this is a bad way of getting one liberty file, need a way to merge all std cell lib files
        abc -D {self.clock_period} \\
            -constr "{self.mapped_sdc_path}" \\
            -liberty "{self.liberty_files_tt.split()[0]}" \\
            -showtmp

        # Replace undef values with defined constants
        # TODO: do we need this??
        setundef -zero

        # Split multi-bit nets into single-bit nets.
        # Splitting nets resolves unwanted compound assign statements in netlist (assign [..] = [..])
        splitnets

        # Remove unused cells and wires
        opt_clean -purge
        """)
        return True

    def add_tieoffs(self) -> bool:
        tie_hi_cells = self.technology.get_special_cell_by_type(CellType.TieHiCell)
        tie_lo_cells = self.technology.get_special_cell_by_type(CellType.TieLoCell)
        tie_hilo_cells = self.technology.get_special_cell_by_type(CellType.TieHiLoCell)

        if len(tie_hi_cells) != 1 or len (tie_lo_cells) != 1 or tie_hi_cells[0].output_ports is None or tie_lo_cells[0].output_ports is None:
            self.logger.warning("Hi and Lo tiecells and their input ports are unspecified or improperly specified and will not be added during synthesis.")
        else:
            tie_hi_cell = tie_hi_cells[0].name[0]
            tie_hi_port = tie_hi_cells[0].output_ports[0]
            tie_lo_cell = tie_lo_cells[0].name[0]
            tie_lo_port = tie_lo_cells[0].output_ports[0]

            self.block_append(f"""
            # Technology mapping of constant hi- and/or lo-drivers
            hilomap -singleton \\
                    -hicell {{*}}{tie_hi_cell} {tie_hi_port} \\
                    -locell {{*}}{tie_lo_cell} {tie_lo_port}
            """)
        if self.driver_cell is not None:
            self.block_append(f"""
            # Insert driver cells for pass through wires
            insbuf -buf {{*}}{self.driver_cell} {self.driver_ports_in} {self.driver_ports_out}
            """)
        return True

    def write_regs(self) -> bool:
        # TODO: generate find_regs_cells.json / find_regs_paths.json here
        self.ran_write_regs = False
        return True

    def generate_reports(self) -> bool:
        # TODO: generate all reports (will probably need to parse the log file)
        self.block_append(f"""
        tee -o {self.run_dir}/{self.top_module}.synth_check.rpt check

        tee -o {self.run_dir}/{self.top_module}.synth_stat.txt stat -top {self.top_module} -liberty {self.liberty_files_tt.split()[0]}
        """)
        return True

    def write_outputs(self) -> bool:
        hier_mapped_v_path=os.path.join(self.run_dir, f"{self.top_module}.mapped.hier.v")
        self.block_append(f"""
        write_verilog -noattr -noexpr -nohex -nodec -defparam "{hier_mapped_v_path}"

        flatten

        # OpenROAD will throw an error if the verilog from Yosys is not flattened
        write_verilog -noattr -noexpr -nohex -nodec -defparam "{self.mapped_v_path}"

        # BLIF file seems to be easier to parse than mapped verilog for find_regs functions so leave for now
        write_blif -top {self.top_module} "{self.mapped_blif_path}"
        """)
        self.ran_write_outputs = True
        return True

tool = YosysSynth
