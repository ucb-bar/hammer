#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Yosys synthesis plugin for Hammer (as part of OpenROAD-flow installation).
# mostly adoped from OpenLANE scripts found here: https://github.com/The-OpenROAD-Project/OpenLane/tree/master/scripts
#
# See LICENSE for licence details.

from textwrap import dedent as dd

# from hammer_utils import deepdict
from hammer_vlsi.vendor import OpenROADTool, OpenROADSynthesisTool

###########
from hammer_vlsi import HammerTool, HammerToolStep, HammerToolHookAction, HierarchicalMode
from hammer_vlsi.constraints import MMMCCorner, MMMCCornerType
from hammer_utils import VerilogUtils, optional_map
from hammer_vlsi import HammerSynthesisTool
from hammer_logging import HammerVLSILogging
from hammer_vlsi import MMMCCornerType
import hammer_tech

from typing import Dict, List, Any, Optional

import specialcells
from specialcells import CellType, SpecialCell

import os
import json
from collections import Counter

class YosysSynth(HammerSynthesisTool, OpenROADTool):

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
        new_dict["YOSYS_BIN"] = self.get_setting("synthesis.yosys.binary")
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
        mapped_v = self.mapped_hier_v_path if self.hierarchical_mode.is_nonleaf_hierarchical() else self.mapped_v_path
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
        # outputs["synthesis.outputs.sdf_file"] = self.sdf_file
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

    def synth_script_path(self) -> str:
        # TODO: generate this internally
        openroad = self.openroad_flow_path()
        return os.path.join(openroad, "flow/scripts/synth.tcl")

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
        return " ".join(lib_args)

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
            self.get_setting("synthesis.yosys.binary"),
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
                f.write(f"""\
create_clock [get_ports {self.clock_port_name}]  -name {self.clock_port_name}  -period {self.clock_period}

set_max_fanout {self.max_fanout}

set clk_indx [lsearch [all_inputs] [get_port {self.clock_port_name}]]
set all_inputs_wo_clk_rst [lreplace [all_inputs] $clk_indx $clk_indx]

# correct resetn
# IO_PCT default: 0.2
set_input_delay  [expr {self.clock_period} * 0.2]  -clock [get_clocks {self.clock_port_name}] $all_inputs_wo_clk_rst
set_output_delay [expr {self.clock_period} * 0.2]  -clock [get_clocks {self.clock_port_name}] [all_outputs]

set_driving_cell -lib_cell {self.driving_cell} -pin {self.driving_cell_pin} [all_inputs]
set_load [expr {self.synth_cap_load} / 1000.0] [all_outputs]

set_clock_uncertainty {self.clock_uncertainty} [get_clocks {self.clock_port_name}]

# default SYNTH_CLOCK_TRANSITION = 0.15
set_clock_transition {self.clock_transition} [get_clocks {self.clock_port_name}]

# default SYNTH_TIMING_DERATE = "+5%/-5%"
set_timing_derate -early [expr 1-"+5%/-5%"]
set_timing_derate -late [expr 1+"+5%/-5%"]
""")

    #========================================================================
    # synthesis main steps
    #========================================================================
    def init_environment(self) -> bool:

        # set variables to match global variables in OpenLANE
        self.driving_cell = "sky130_fd_sc_hd__inv_1" # SYNTH_DRIVING_CELL
        self.driving_cell_pin = "Y" # SYNTH_DRIVING_CELL_PIN
        self.buffer_cell = "sky130_fd_sc_hd__buf_2 A X"

        time_unit = self.get_time_unit().value_prefix + self.get_time_unit().unit
        clock_port = self.get_clock_ports()[0]
        self.clock_port_name = clock_port.name
        self.clock_period = int(clock_port.period.value_in_units(time_unit))
        self.clock_uncertainty = int(clock_port.period.value_in_units(time_unit))
        self.clock_transition = 0.15 # SYNTH_CLOCK_TRANSITION

        self.synth_cap_load = 33.5 # SYNTH_CAP_LOAD
        self.max_fanout = 5 # default SYNTH_MAX_FANOUT = 5

        # get typical corner liberty file
        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        corner_tt = next((corner for corner in corners if corner.type == MMMCCornerType.Extra), None)
        self.liberty_file = self.get_timing_libs(corner_tt)

#         self.append(f"""
# # Set env variables based on defaults in OpenLANE
# # TODO: LIB_SYNTH should technically be set to trimmed.lib, a trimmed version of the sky130_fd_sc_hd__tt_025C_1v80 library. there's a script to generate this, should figure out its purpose
# set ::env(LIB_SYNTH) "{self.get_timing_libs(corner_tt)}"

# """)
        # fyi:  synthesis_tmpfiles = self.run_dir
        #       synth_report_prefix = self.run_dir/gcd
#         self.append("""
# set ::env(synth_report_prefix) "$::env(synthesis_tmpfiles)/gcd"
# """)
        
        self.append("yosys -import")
        
        self.append("""
########################################################
# from openlane/scripts/tcl_commands/utils.tcl
########################################################
proc index_file {args} {
	set file_full_name [lindex $args 0]

	if { $file_full_name == "/dev/null" } {
		# Can't index that :)
		return $file_full_name
	}

	set file_path [file dirname $file_full_name]
	set fbasename [file tail $file_full_name]
	set fbasename "0-$fbasename"

	set new_file_full_name "$file_path/$fbasename"
    set replace [string map {/ \\/} 0]
	return $new_file_full_name
}
""")
        # for now, just ignore this pg_pin conversion/removal

#         self.append(r"""
# ########################################################
# # from openlane/scripts/tcl_commands/synthesis.tcl
# ########################################################
# proc convert_pg_pins {lib_in lib_out} {
# 	exec sed -E {s/^([[:space:]]+)pg_pin(.*)/\1pin\2\n\1    direction : "inout";/g} $lib_in > $lib_out
# }
# """)
#         self.append("""
# set ::env(LIB_SYNTH_COMPLETE_NO_PG) [list]
# foreach lib $::env(LIB_SYNTH_COMPLETE) {
#     set fbasename [file rootname [file tail $lib]]
#     set lib_path [index_file $::env(synthesis_tmpfiles)/$fbasename.no_pg.lib]
#     convert_pg_pins $lib $lib_path
#     lappend ::env(LIB_SYNTH_COMPLETE_NO_PG) $lib_path
# }
# """)
        
#         self.append("""
# if { [info exists ::env(SYNTH_DEFINES) ] } {
# 	foreach define $::env(SYNTH_DEFINES) {
# 		log "Defining $define"
# 		verilog_defines -D$define
# 	}
# }
# """)
        # input pin cap of IN_3VX8
        self.append("set max_FO 5") 
        self.append(f"set max_Tran {0.1*self.clock_period}")
        self.append(f"""

# Mapping parameters
set A_factor  0.00
set B_factor  0.88
set F_factor  0.00

# Don't change these unless you know what you are doing
set stat_ext    ".stat.rpt"
set chk_ext     ".chk.rpt"

""")

        self.write_sdc_file()

        # get old sdc, add library specific stuff for abc scripts
        self.append(f'set sdc_file "{self.mapped_sdc_path}"')
        self.append(f"set outfile [open {self.mapped_sdc_path} w]")
        self.append(f'puts $outfile "set_driving_cell {self.driving_cell}"')
        self.append(f'puts $outfile "set_load {self.synth_cap_load}"')
        self.append("close $outfile")

        
        self.append("setundef -zero")

        # We are switching working directories and Yosys still needs to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))  # type: List[str]

        # If we are in hierarchical, we need to remove hierarchical sub-modules/sub-blocks.
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            abspath_input_files = list(map(self.remove_hierarchical_submodules_from_file, abspath_input_files))

        # Add any verilog_synth wrappers (which are needed in some technologies e.g. for SRAMs) which need to be
        # synthesized.
        abspath_input_files += self.technology.read_libs([
            hammer_tech.filters.verilog_synth_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        self.append("read_verilog -sv {}".format(" ".join(abspath_input_files)))

        return True

    def syn_generic(self) -> bool:
        self.append("yosys proc") # TODO: verify this, it was in yosys manual but not in OpenLANE script
        self.append(f"hierarchy -check -top {self.top_module}")
        self.append(f"synth -top {self.top_module} -run :fine")
        self.append("opt -fast -full")
        self.append("memory_map")
        self.append("opt -full")
        # TODO: figure out why techmap path is required for server install but not conda install
        self.append("techmap -map /usr/local/share/yosys/techmap.v")
        self.append("opt -fast")
        self.append("abc -fast")
        self.append("opt -fast")
        self.append("synth -top gcd -run check:")
        # write a post techmap dot file - from OpenLANE I think this is in the wrong place??
        # self.append("show -format dot -prefix $::env(synthesis_tmpfiles)/post_techmap")
        self.append('share -aggressive') # default SYNTH_SHARE_RESOURCES = 1
        self.append("opt")
        self.append("opt_clean -purge")
        self.append(f'tee -o "{self.run_dir}/{self.top_module}_pre.stat" stat')
        return True

    def syn_map(self) -> bool:
        self.append(r"""
# ABC Scrips
set abc_rs_K    "resub,-K,"
set abc_rs      "resub"
set abc_rsz     "resub,-z"
set abc_rw_K    "rewrite,-K,"
set abc_rw      "rewrite"
set abc_rwz     "rewrite,-z"
set abc_rf      "refactor"
set abc_rfz     "refactor,-z"
set abc_b       "balance"

set abc_resyn2        "${abc_b}; ${abc_rw}; ${abc_rf}; ${abc_b}; ${abc_rw}; ${abc_rwz}; ${abc_b}; ${abc_rfz}; ${abc_rwz}; ${abc_b}"
set abc_share         "strash; multi,-m; ${abc_resyn2}"
set abc_resyn2a       "${abc_b};${abc_rw};${abc_b};${abc_rw};${abc_rwz};${abc_b};${abc_rwz};${abc_b}"
set abc_resyn3        "balance;resub;resub,-K,6;balance;resub,-z;resub,-z,-K,6;balance;resub,-z,-K,5;balance"
set abc_resyn2rs      "${abc_b};${abc_rs_K},6;${abc_rw};${abc_rs_K},6,-N,2;${abc_rf};${abc_rs_K},8;${abc_rw};${abc_rs_K},10;${abc_rwz};${abc_rs_K},10,-N,2;${abc_b},${abc_rs_K},12;${abc_rfz};${abc_rs_K},12,-N,2;${abc_rwz};${abc_b}"

set abc_choice        "fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; fraig_restore"
set abc_choice2      "fraig_store; balance; fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; ${abc_resyn2}; fraig_store; fraig_restore"

set abc_map_old_cnt			"map,-p,-a,-B,0.2,-A,0.9,-M,0"
set abc_map_old_dly         "map,-p,-B,0.2,-A,0.9,-M,0"
set abc_retime_area         "retime,-D,{D},-M,5"
set abc_retime_dly          "retime,-D,{D},-M,6"
set abc_map_new_area        "amap,-m,-Q,0.1,-F,20,-A,20,-C,5000"

set abc_area_recovery_1       "${abc_choice}; map;"
set abc_area_recovery_2       "${abc_choice2}; map;"

set map_old_cnt			    "map,-p,-a,-B,0.2,-A,0.9,-M,0"
set map_old_dly			    "map,-p,-B,0.2,-A,0.9,-M,0"
set abc_retime_area   	"retime,-D,{D},-M,5"
set abc_retime_dly    	"retime,-D,{D},-M,6"
set abc_map_new_area  	"amap,-m,-Q,0.1,-F,20,-A,20,-C,5000"

set abc_fine_tune       ""
""")

        self.append(r"""
set delay_scripts [list \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_resyn2};${abc_retime_dly}; scleanup;${abc_map_old_dly};retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_resyn2};${abc_retime_dly}; scleanup;${abc_choice2};${abc_map_old_dly};${abc_area_recovery_2}; retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_resyn2};${abc_retime_dly}; scleanup;${abc_choice};${abc_map_old_dly};${abc_area_recovery_1}; retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_old_dly};retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	]

set area_scripts [list \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_resyn2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_new_area};retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	"+read_constr,${sdc_file};fx;mfs;strash;refactor;${abc_choice2};${abc_retime_area};scleanup;${abc_choice2};${abc_map_new_area};${abc_choice2};${abc_map_new_area};retime,-D,{D};${abc_fine_tune};stime,-p;print_stats -m" \
	]
""")

        self.append("""
set all_scripts [list {*}$delay_scripts {*}$area_scripts]

set strategy_type AREA
set strategy_type_idx 0

if { $strategy_type == "DELAY" } {
	set strategy $strategy_type_idx
} else {
	set strategy [expr {[llength $delay_scripts]+$strategy_type_idx}]
}

""")
        self.append(f"dfflibmap -liberty {self.liberty_file}")
        self.append(f'tee -o "{self.run_dir}/{self.top_module}_dff.stat" stat')
        self.append(f"""
log "\[INFO\]: ABC: WireLoad : S_$strategy"
abc -D {self.clock_period} \\
    -constr {self.mapped_sdc_path} \\
    -liberty {self.liberty_file} \\
    -script [lindex $all_scripts $strategy] \\
    -showtmp;
""")
        return True

    def add_tieoffs(self) -> bool:
        tie_hi_cells = self.technology.get_special_cell_by_type(CellType.TieHiCell)
        tie_lo_cells = self.technology.get_special_cell_by_type(CellType.TieLoCell)
        tie_hilo_cells = self.technology.get_special_cell_by_type(CellType.TieHiLoCell)

        if len(tie_hi_cells) != 1 or len (tie_lo_cells) != 1:
            if len(tie_hilo_cells) != 1:
                self.logger.warning("Hi and Lo tiecells are unspecified or improperly specified and will not be added during synthesis.")
                return True
            tie_hi_cells = tie_hilo_cells
            tie_lo_cells = tie_hilo_cells            

        tie_hi_cell = tie_hi_cells[0].name[0]
        tie_lo_cell = tie_lo_cells[0].name[0]
        
        self.append(f'hilomap -hicell "{tie_hi_cell}" -locell "{tie_lo_cell}"')
        # need buffers in synthesis?
        # self.append(f"insbuf -buf {*}sky130_fd_sc_hd__buf_2 A X")
        return True

    def write_regs(self) -> bool:
        # TODO: what is the purpose of splitnets?
        # get rid of the assignments that make init_floorplan fail
        self.append("splitnets") # split multi-bit nets into signle-bit nets
        self.append("opt_clean -purge")
        
        # TODO: generate find_regs_cells.json / find_regs_paths.json here
        self.ran_write_regs = True
        return True

    def generate_reports(self) -> bool:
        # TODO: generate all reports (not sure how...?)
        self.append(f'tee -o "{self.run_dir}/{self.top_module}$chk_ext.strategy$strategy" check')
        self.append(f'tee -o "{self.run_dir}/{self.top_module}$stat_ext.strategy$strategy" stat -top {self.top_module} -liberty {self.liberty_file}')
        return True
    
    def write_outputs(self) -> bool:
        self.append(f'write_verilog -noattr -noexpr -nohex -nodec -defparam "{self.mapped_v_path}"')
        # BLIF file seems to be easier to parse than mapped verilog for find_regs functions so leave for now
        self.append(f'write_blif -top gcd "{self.mapped_blif_path}"')
        # self.append(f'write_json gcd.json')
        # TODO: figure out why the OpenLANE script re-runs synthesis & flattens design, when we explicitly requested hierarchical mode
#         self.append(f"""
# design -reset
# read_liberty -lib -ignore_miss_dir -setattr blackbox $::env(LIB_SYNTH_COMPLETE_NO_PG)
# file copy -force {self.mapped_v_path} {self.run_dir}/{self.top_module}.mapped.hierarchical.v
# read_verilog -sv {self.mapped_v_path}
# synth -top {self.top_module} -flatten
# splitnets
# opt_clean -purge
# insbuf -buf {self.buffer_cell}
# write_verilog -noattr -noexpr -nohex -nodec -defparam "{self.mapped_v_path}"
# tee -o "$::env(synth_report_prefix)$chk_ext.strategy$strategy" check
# tee -o "$::env(synth_report_prefix)$stat_ext.strategy$strategy" stat -top {self.top_module} -liberty [lindex $::env(LIB_SYNTH_COMPLETE_NO_PG) 0]    
# """)
        self.ran_write_outputs = True
        return True
    
tool = YosysSynth
