#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Yosys synthesis plugin for Hammer (as part of OpenROAD-flow installation).
#
# See LICENSE for licence details.

from textwrap import dedent as dd

# from hammer_utils import deepdict
from hammer_vlsi.vendor import OpenROADTool, OpenROADSynthesisTool

###########
from hammer_vlsi import HammerTool, HammerToolStep, HammerToolHookAction, HierarchicalMode
from hammer_vlsi.constraints import MMMCCorner, MMMCCornerType
from hammer_utils import VerilogUtils
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

    def fill_outputs(self) -> bool:
        # Check that the synthesis outputs exist if the synthesis run was successful
        mapped_v = self.mapped_hier_v_path if self.hierarchical_mode.is_nonleaf_hierarchical() else self.mapped_v_path
        self.output_files = [mapped_v]
        self.output_sdc = self.mapped_sdc_path

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
    @property
    def mapped_v_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.v".format(self.top_module))

    @property
    def mapped_sdc_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.sdc".format(self.top_module))

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
            # "-no_gui"
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

    #========================================================================
    # synthesis main steps
    #========================================================================
    def init_environment(self) -> bool:

        self.driver_cell = "sky130_fd_sc_hd__inv_1"
        self.buffer_cell = "sky130_fd_sc_hd__buf_2 A X"

        clocks = self.get_clock_ports()
        time_unit = self.get_time_unit().value_prefix + self.get_time_unit().unit
        self.clock_period = int(clocks[0].period.value_in_units(time_unit))

        # list of liberty files
        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        # append_mmmc("create_library_set -name {name}_set -timing [list {list}]".format(
        #             name=corner_name,
        #             list=self.get_timing_libs(corner)
        #         ))

        self.append("""
# Set env variables based on defaults in OpenLANE
set ::env(CURRENT_INDEX) 0
set ::env(LIB_SYNTH_COMPLETE) "/tools/commercial/skywater/swtech130/local/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

set ::env(SYNTH_BUFFERING) 0
set ::env(SYNTH_SIZING) 0
set ::env(DESIGN_NAME) gcd
set ::env(CLOCK_PORT) "clk"
set ::env(LIB_SYNTH) $::env(LIB_SYNTH_COMPLETE)
set ::env(SYNTH_READ_BLACKBOX_LIB) 0
set ::env(synthesis_tmpfiles) "/tools/B/nayiri/openroad/gcd/yosys/syn-rundir"
set ::env(SYNTH_STRATEGY) "AREA 0"
""")
        
        self.append("""
set ::env(SYNTH_NO_FLAT) 1
set ::env(SYNTH_SHARE_RESOURCES) 1
set ::env(synth_report_prefix) "$::env(synthesis_tmpfiles)/gcd"
""")
        
        self.append("yosys -import")
        
        self.append("""
########################################################
# from openlane/scripts/tcl_commands/utils.tcl
########################################################

proc puts_err {txt} {
  set message "\[ERROR\]: $txt"
  puts "$message"
  if { [info exists ::env(LOGS_DIR)] } {
    exec echo $message >> $::env(RUN_DIR)/flow_summary.log
  }
}

proc flow_fail {args} {
	if { ! [info exists ::env(FLOW_FAILED)] || ! $::env(FLOW_FAILED) } {
		set ::env(FLOW_FAILED) 1
		# calc_total_runtime -status "flow failed"
		# generate_final_summary_report
        # save_state
		puts_err "Flow failed."
	}
}

# a minimal try catch block
proc try_catch {args} {
    set exit_code [catch {eval exec $args} error_msg]
}

proc index_file {args} {
	set file_full_name [lindex $args 0]

	if { $file_full_name == "/dev/null" } {
		# Can't index that :)
		return $file_full_name
	}

	set file_path [file dirname $file_full_name]
	set fbasename [file tail $file_full_name]
	set fbasename "$::env(CURRENT_INDEX)-$fbasename"

	set new_file_full_name "$file_path/$fbasename"
    set replace [string map {/ \\/} $::env(CURRENT_INDEX)]
	return $new_file_full_name
}
""")

        self.append(r"""
########################################################
# from openlane/scripts/tcl_commands/synthesis.tcl
########################################################
proc convert_pg_pins {lib_in lib_out} {
	try_catch sed -E {s/^([[:space:]]+)pg_pin(.*)/\1pin\2\n\1    direction : "inout";/g} $lib_in > $lib_out
}
""")
        self.append("""
set ::env(LIB_SYNTH_COMPLETE_NO_PG) [list]
foreach lib $::env(LIB_SYNTH_COMPLETE) {
    set fbasename [file rootname [file tail $lib]]
    set lib_path [index_file $::env(synthesis_tmpfiles)/$fbasename.no_pg.lib]
    convert_pg_pins $lib $lib_path
    lappend ::env(LIB_SYNTH_COMPLETE_NO_PG) $lib_path
}
""")

        self.append("""
########################################################
# from openlane/scripts/yosys/synth.tcl
########################################################

# inputs expected as env vars
set buffering $::env(SYNTH_BUFFERING)
set sizing $::env(SYNTH_SIZING)
set sclib $::env(LIB_SYNTH)
#set opt $::env(SYNTH_OPT)

if { [info exists ::env(SYNTH_DEFINES) ] } {
	foreach define $::env(SYNTH_DEFINES) {
		log "Defining $define"
		verilog_defines -D$define
	}
}

set vIdirsArgs ""
if {[info exist ::env(VERILOG_INCLUDE_DIRS)]} {
	foreach dir $::env(VERILOG_INCLUDE_DIRS) {
		lappend vIdirsArgs "-I$dir"
	}
	set vIdirsArgs [join $vIdirsArgs]
}
""")

        self.append("""
if { $::env(SYNTH_READ_BLACKBOX_LIB) } {
	log "Reading $::env(LIB_SYNTH_COMPLETE_NO_PG) as a blackbox"
	foreach lib $::env(LIB_SYNTH_COMPLETE_NO_PG) {""")
        self.verbose_append("read_liberty -lib -ignore_miss_dir -setattr blackbox $lib")
        self.append("""
	}
}
""")

        self.append("""
if { [info exists ::env(EXTRA_LIBS) ] } {
	foreach lib $::env(EXTRA_LIBS) {""")
        self.verbose_append("read_liberty -lib -ignore_miss_dir -setattr blackbox $lib")
        self.append("""
	}
}
""")

        self.append("""
if { [info exists ::env(VERILOG_FILES_BLACKBOX)] } {
	foreach verilog_file $::env(VERILOG_FILES_BLACKBOX) {
		read_verilog -sv -lib {*}$vIdirsArgs $verilog_file
	}
}
""")
        # input pin cap of IN_3VX8
        self.append("set max_FO 5") # default SYNTH_MAX_FANOUT = 5
        self.append(f"set max_Tran {0.1*self.clock_period}")
        self.append(f"""

# Mapping parameters
set A_factor  0.00
set B_factor  0.88
set F_factor  0.00

# Don't change these unless you know what you are doing
set stat_ext    ".stat.rpt"
set chk_ext    ".chk.rpt"
set gl_ext      ".gl.v"
set constr_ext  ".{self.clock_period}.constr"
set timing_ext  ".timing.txt"
set abc_ext     ".abc"

""")
        # get old sdc, add library specific stuff for abc scripts
        self.append(f'set sdc_file "{self.mapped_sdc_path}"')
        self.append(f"set outfile [open {self.mapped_sdc_path} w]")
        self.append(f'puts $outfile "set_driving_cell {self.driver_cell}"')
        self.append('puts $outfile "set_load 33.5"') # default SYNTH_CAP_LOAD = 33.5
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
        self.append(f"hierarchy -check -top {self.top_module}")
        self.append(f"synth -top {self.top_module}")
        # write a post techmap dot file - from OpenLANE I think this is in the wrong place??
        # self.append("show -format dot -prefix $::env(synthesis_tmpfiles)/post_techmap")
        self.append('share -aggressive') # default SYNTH_SHARE_RESOURCES = 1
        self.append("opt")
        self.append("opt_clean -purge")
        # self.append('tee -o "$::env(synth_report_prefix)_pre.stat" stat')
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

if {$buffering==1} {
	set abc_fine_tune		"buffer,-N,${max_FO},-S,${max_Tran};upsize,{D};dnsize,{D}"
} elseif {$sizing} {
	set abc_fine_tune       "upsize,{D};dnsize,{D}"
} else {
	set abc_fine_tune       ""
}
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

set strategy_parts [split $::env(SYNTH_STRATEGY)]

proc synth_strategy_format_err { } {
	upvar area_scripts area_scripts
	upvar delay_scripts delay_scripts
	log -stderr "\[ERROR] Misformatted SYNTH_STRATEGY (\"$::env(SYNTH_STRATEGY)\")."
	log -stderr "\[ERROR] Correct format is \"DELAY|AREA 0-[expr [llength $delay_scripts]-1]|0-[expr [llength $area_scripts]-1]\"."
	exit 1
}

if { [llength $strategy_parts] != 2 } {
	synth_strategy_format_err
}

set strategy_type [lindex $strategy_parts 0]
set strategy_type_idx [lindex $strategy_parts 1]

if { $strategy_type != "AREA" && $strategy_type != "DELAY" } {
	log -stderr "\[ERROR] AREA|DELAY tokens not found. ($strategy_type)"
	synth_strategy_format_err
}

if { $strategy_type == "DELAY" && $strategy_type_idx >= [llength $delay_scripts] } {
	log -stderr "\[ERROR] strategy index ($strategy_type_idx) is too high."
	synth_strategy_format_err
}

if { $strategy_type == "AREA" && $strategy_type_idx >= [llength $area_scripts] } {
	log -stderr "\[ERROR] strategy index ($strategy_type_idx) is too high."
	synth_strategy_format_err
}

if { $strategy_type == "DELAY" } {
	set strategy $strategy_type_idx
} else {
	set strategy [expr {[llength $delay_scripts]+$strategy_type_idx}]
}

""")
        self.append("dfflibmap -liberty $sclib")
        # self.append('tee -o "$::env(synth_report_prefix)_dff.stat" stat')
        self.append(f"""
log "\[INFO\]: ABC: WireLoad : S_$strategy"
abc -D {self.clock_period} \
    -constr {self.mapped_sdc_path} \
    -liberty $sclib  \
    -script [lindex $all_scripts $strategy] \
    -showtmp;
""")
        return True

    def add_tieoffs(self) -> bool:
        tie_hi_cells = self.technology.get_special_cell_by_type(CellType.TieHiCell)
        tie_lo_cells = self.technology.get_special_cell_by_type(CellType.TieLoCell)

        if len(tie_hi_cells) != 1 or len (tie_lo_cells) != 1:
            self.logger.warning("Hi and Lo tiecells are unspecified or improperly specified and will not be added during synthesis.")
            return True

        tie_hi_cell = tie_hi_cells[0].name[0]
        tie_lo_cell = tie_lo_cells[0].name[0]
        
        self.append(f'hilomap -hicell "{tie_hi_cell}" -locell "{tie_lo_cell}"')
        # self.append(f"insbuf -buf {*}sky130_fd_sc_hd__buf_2 A X")
        return True

    def write_regs(self) -> bool:
        # TODO: what is the purpose of splitnets?
        # get rid of the assignments that make init_floorplan fail
        self.append("splitnets") # split multi-bit nets into signle-bit nets
        self.append("opt_clean -purge")

        # TODO: currently using OpenROAD's default synthesis script
        return True

    def generate_reports(self) -> bool:
        # TODO: generate all reports (not sure how...?)
        self.append(f'tee -o "{self.run_dir}/{self.top_module}$chk_ext.strategy$strategy" check')
        self.append(f'tee -o "{self.run_dir}/{self.top_module}$stat_ext.strategy$strategy" stat -top {self.top_module} -liberty [lindex $::env(LIB_SYNTH_COMPLETE_NO_PG) 0]')
        return True
    
    def write_outputs(self) -> bool:
        self.append(f'write_verilog -noattr -noexpr -nohex -nodec -defparam "{self.mapped_v_path}"')

        # TODO: figure out why the OpenLANE script re-runs synthesis & flattens design, when we explicitly requested hierarchical mode
        self.append(f"""
design -reset
read_liberty -lib -ignore_miss_dir -setattr blackbox $::env(LIB_SYNTH_COMPLETE_NO_PG)
file copy -force {self.mapped_v_path} {self.run_dir}/{self.top_module}.mapped.hierarchical.v
read_verilog -sv {self.mapped_v_path}
synth -top {self.top_module} -flatten
splitnets
opt_clean -purge
insbuf -buf {self.buffer_cell}
write_verilog -noattr -noexpr -nohex -nodec -defparam "{self.mapped_v_path}"
tee -o "$::env(synth_report_prefix)$chk_ext.strategy$strategy" check
tee -o "$::env(synth_report_prefix)$stat_ext.strategy$strategy" stat -top {self.top_module} -liberty [lindex $::env(LIB_SYNTH_COMPLETE_NO_PG) 0]    
""")
        return True
    
tool = YosysSynth
