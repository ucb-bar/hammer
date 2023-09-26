#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer-vlsi plugin for Cadence Joules.
#
#  See LICENSE for licence details.

import shutil
from typing import List, Dict, Optional, Callable, Tuple, Set, Any, cast
from itertools import product

import os
import errno
import json
from datetime import datetime
from textwrap import dedent

from hammer.utils import get_or_else, optional_map, coerce_to_grid, check_on_grid, lcm_grid
from hammer.vlsi import HammerPowerTool, HammerToolStep, MMMCCornerType, FlowLevel, TimeValue, PowerReport
from hammer.logging import HammerVLSILogging
import hammer.tech as hammer_tech

from hammer.common.cadence import CadenceTool

class Joules(HammerPowerTool, CadenceTool):

    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None
    
    @property
    def power_db_path(self) -> str:
        power_db_path = os.path.join(self.run_dir, "power_db")
        os.makedirs(power_db_path, exist_ok=True)
        return power_db_path

    def tool_config_prefix(self) -> str:
        return "power.joules"

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = dict(super().env_vars)
        new_dict["JOULES_BIN"] = self.get_setting("power.joules.joules_bin")
        return new_dict
    
    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def load_power_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "load_power")
    
    @property
    def load_power_tcl(self) -> str:
        return self.load_power_script + ".tcl"

    @property
    def _step_transitions(self) -> List[Tuple[str, str]]:
        """
        Private helper property to keep track of which steps we ran so that we
        can create symlinks.
        This is a list of (pre, post) steps
        """
        return self.attr_getter("__step_transitions", [])

    @_step_transitions.setter
    def _step_transitions(self, value: List[Tuple[str, str]]) -> None:
        self.attr_setter("__step_transitions", value)

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        assert super().do_pre_steps(first_step)
        # TODO: is this the best place to put this? settings should run before ANY step
        self.joules_settings()
        # Restore from the last checkpoint if we're not starting over.
        if first_step != self.first_step:
            self.verbose_append("read_db pre_{step}".format(step=first_step.name))
            # NOTE: reading stimulus from this sdb file just errors out, unsure why
            # if os.path.exists(self.sdb_path):
            #     self.verbose_append(f"read_stimulus -format sdb -file {self.sdb_path}")
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.verbose_append("write_db -to_file pre_{step}".format(step=next.name))
        # Symlink the database to latest for load_power script later.
        self.verbose_append("ln -sfn pre_{step} latest".format(step=next.name))
        self._step_transitions = self._step_transitions + [(prev.name, next.name)]
        return True

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        # Create symlinks for post_<step> to pre_<step+1> to improve usability.
        try:
            for prev, next in self._step_transitions:
                os.symlink(
                    os.path.join(self.run_dir, "pre_{next}".format(next=next)), # src
                    os.path.join(self.run_dir, "post_{prev}".format(prev=prev)) # dst
                )
        except OSError as e:
            if e.errno != errno.EEXIST:
                self.logger.warning("Failed to create post_* symlinks: " + str(e))

        # Create db post_<last step>
        # TODO: this doesn't work if you're only running the very last step
        if len(self._step_transitions) > 0:
            last = "post_{step}".format(step=self._step_transitions[-1][1])
            self.verbose_append("write_db -to_file {last}".format(last=last))
            # Symlink the database to latest for load_power script later.
            self.verbose_append("ln -sfn {last} latest".format(last=last))

        return self.run_joules()
    
    # def get_tool_hooks(self) -> List[HammerToolHookAction]:
    #     return [self.make_persistent_hook(joules_global_settings)]

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_design,
            self.synthesize_design,
            self.report_power,
        ])
    
    def joules_settings(self) -> bool:
        max_threads = self.get_setting("vlsi.core.max_threads")
        self.verbose_append(f"set_multi_cpu_usage -local_cpu {max_threads}")
        # use super-threading to parallelize synthesis (up to 8 CPUs)
        self.verbose_append("set_db auto_super_thread 1")
        # self.verbose_append(f"set_db super_thread_servers localhost")
        self.verbose_append(f"set_db max_cpus_per_server {max_threads}")
        self.verbose_append("set_db max_frame_count 100000000") # default is 1000, too low for most use-cases
        return True

    def check_level(self) -> bool:
        if self.level == FlowLevel.RTL or self.level == FlowLevel.SYN:
            return True
        else:
            self.logger.error("The FlowLevel is invalid. The Joules plugin only supports RTL and post-synthesis analysis. Check your power tool setting and flow step.")
            return False
    
    def power_db_basename(self, stim_alias) -> str:
        return os.path.join(self.power_db_path, stim_alias)
    
    # stimulus database
    def sdb_path(self, stim_alias) -> str:
        return os.path.join(self.power_db_path, stim_alias+'.sdb')
    
    # no clue what ADB is
    def adb_path(self, stim_alias) -> str:
        return os.path.join(self.power_db_path, stim_alias+'.adb')
    
    def pdb_path(self, stim_alias) -> str:
        return os.path.join(self.power_db_path, stim_alias+'.pdb')

    def init_technology(self) -> bool:
        # libs, define RAMs, define corners
        verbose_append = self.verbose_append

        corners = self.get_mmmc_corners()
        if MMMCCornerType.Extra in list(map(lambda corner: corner.type, corners)):
            for corner in corners:
                if corner.type is MMMCCornerType.Extra:
                    verbose_append("read_libs {EXTRA_LIBS} -domain extra -infer_memory_cells".format(EXTRA_LIBS=self.get_timing_libs(corner)))
                    break
        elif MMMCCornerType.Setup in list(map(lambda corner: corner.type, corners)):
            for corner in corners:
                if corner.type is MMMCCornerType.Setup:
                    verbose_append("read_libs {SETUP_LIBS} -domain setup -infer_memory_cells".format(SETUP_LIBS=self.get_timing_libs(corner)))
                    break
        elif MMMCCornerType.Hold in list(map(lambda corner: corner.type, corners)):
            for corner in corners:
                if corner.type is MMMCCornerType.Hold:
                    verbose_append("read_libs {HOLD_LIBS} -domain hold -infer_memory_cells".format(HOLD_LIBS=self.get_timing_libs(corner)))
                    break
        else:
            self.logger.error("No corners found")
            return False
        return True

    def init_design(self) -> bool:
        if not self.check_level(): return False
        if not self.init_technology(): return False
        verbose_append = self.verbose_append

        top_module = self.get_setting("power.inputs.top_module")
        # Replace . to / formatting in case argument passed from sim tool
        tb_dut = self.tb_dut.replace(".", "/")

        if self.level == FlowLevel.RTL:
            # We are switching working directories and Joules still needs to find paths.
            abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))  # type: List[str]
            # Read in the design files
            verbose_append("read_hdl -sv {}".format(" ".join(abspath_input_files)))

        # Setup the power specification
        power_spec_arg = self.map_power_spec_name()
        power_spec_file = self.create_power_spec()
        if not power_spec_arg or not power_spec_file:
            return False

        verbose_append("read_power_intent -{tpe} {spec} -module {TOP_MODULE}".format(tpe=power_spec_arg, spec=power_spec_file, TOP_MODULE=top_module))

        # Set options pre-elaboration
        verbose_append("set_db leakage_power_effort medium")
        verbose_append("set_db lp_insert_clock_gating true")

        if self.level == FlowLevel.RTL:
            # Elaborate the design
            verbose_append("elaborate {TOP_MODULE}".format(TOP_MODULE=top_module))
        elif self.level == FlowLevel.SYN:
            # Read in the synthesized netlist
            verbose_append("read_netlist {}".format(" ".join(self.input_files)))

            # Read in the post-synth SDCs
            verbose_append("read_sdc {}".format(self.sdc))
        
        return True


    def synthesize_design(self) -> bool:
        verbose_append = self.verbose_append

        if self.level == FlowLevel.RTL:
            # Generate and read the SDCs
            sdc_files = self.generate_sdc_files()  # type: List[str]
            verbose_append("read_sdc {}".format(" ".join(sdc_files)))
            verbose_append("syn_power -effort medium")

        return True


    @property
    def stim_aliases(self) -> List[str]:
        """
        Private helper property to keep track of which stimuli aliases have already been read
        """
        return self.attr_getter("__stim_aliases", [])
    @stim_aliases.setter
    def stim_aliases(self, value: List[str]) -> None:
        self.attr_setter("__stim_aliases", value)
    
    @property
    def _waveform_name(self) -> str:
        """
        Private helper property to keep track of which stimuli aliases have already been read
        """
        return self.attr_getter("__waveform_name", "")
    @_waveform_name.setter
    def _waveform_name(self, value: str) -> None:
        self.attr_setter("__waveform_name", value)

    # def get_alias_name(self, waveform, report=None) -> Tuple[str, bool]:
    def get_alias_name(self, read_stim_cmd) -> Tuple[str, bool]:
        """
        Return Tuple(
            stim alias, 
            whether we already ran read_stim for this waveform
                - this is determined by alias name, which contains all possible 
                  arguments to read_stim that are currently supported by this plugin
        )

            stim alias parsing notes:
                - replace . with _ to disambiguate stimulus name with any file extension
                - replace - with _ to avoid errors with reading the cached stimulus (write_sdb -> read_stim)
                    (Joules throws an error when trying to read an SDB file where the stimulus ID contained dashes)
        """
        cmds = read_stim_cmd.split()
        idx_waveform = cmds.index('-file')+1
        waveform_path = cmds[idx_waveform]
        waveform = os.path.basename(waveform_path)
        self._waveform_name = waveform.split('.')[0]
        alias = waveform + "_".join(cmds[idx_waveform+1:])
        for c in "./-": # symbols that will likely cause an error
            alias = alias.replace(c,'_')
        new_stim = not (alias in self.stim_aliases)
        self.stim_aliases = self.stim_aliases + [alias]
        return alias, new_stim
    

    def report_power(self) -> bool:
        verbose_append = self.verbose_append
        top_module = self.get_setting("power.inputs.top_module")
        # Replace . to / formatting in case argument passed from sim tool
        tb_dut = self.tb_dut.replace(".", "/")

        power_report_configs = []
        for waveform in self.waveforms:
            waveform_name = os.path.basename(waveform).split('.')[0]
            power_report_configs.append(
                PowerReport(
                    waveform_path=waveform,
                    inst=None, module=None,
                    levels=None, start_time=None,
                    end_time=None, interval_size=None,
                    toggle_signal=None, num_toggles=None,
                    frame_count=None,
                    report_name=waveform_name, output_formats=['report']
                )
                            )
        power_report_configs += self.get_power_report_configs()
        for report in power_report_configs:
            abspath_waveform = os.path.join(os.getcwd(), report.waveform_path)
            read_stim_cmd = f"read_stimulus -file {abspath_waveform} -dut_instance {self.tb_name}/{tb_dut}"

            if report.start_time:
                read_stim_cmd += " -start {STIME}ns".format(STIME=report.start_time.value_in_units("ns"))
            if report.end_time:
                read_stim_cmd += " -end {ETIME}ns".format(ETIME=report.end_time.value_in_units("ns"))

            frame_based_analysis = (report.interval_size or (report.toggle_signal and report.num_toggles))
            if report.interval_size:
                read_stim_cmd += " -interval_size {INTERVAL}ns".format(INTERVAL=report.interval_size.value_in_units("ns"))
                if report.toggle_signal:
                    self.logger.warning("Both interval_size and toggle_signal/num_toggles specified...only using interval_size for frame-based analysis.")
            elif report.toggle_signal:
                if report.num_toggles:
                    read_stim_cmd += " -cycles {NUM} {SIGNAL}".format(NUM=report.num_toggles, SIGNAL=report.toggle_signal)
                else:
                    self.logger.error("Must specify the number of toggles if the toggle signal is specified.")
                    return False

            if report.frame_count:
                read_stim_cmd += " -frame_count {FRAME_COUNT}".format(FRAME_COUNT=report.frame_count)

            stim_alias, new_stim = self.get_alias_name(read_stim_cmd)

            if new_stim:
                verbose_append(f"{read_stim_cmd} -alias {stim_alias} -append")
                # verbose_append(f"write_sdb -out {alias}.sdb") # NOTE: subsequent read_sdb command errors when reading this file back in, so don't cache for now
                # TODO: avg mode saves time, run this based on output_formats mode?
                # verbose_append(f"compute_power -mode average -stim {stim_alias} -append")
                verbose_append(f"compute_power -mode time_based -stim {stim_alias} -append")

            # remove only file extension (last .*) in filename
            waveform_name = '.'.join(os.path.basename(report.waveform_path).split('.')[0:-1])

            inst_str = f"-inst {report.inst}" if report.inst else ""
            module_str = f"-module {report.module}" if report.module else ""
            levels_str = f"-levels {report.levels}" if report.levels else ""
            report_name = report.report_name if report.report_name else waveform_name
            output_formats = set(report.output_formats) if report.output_formats else {'report'}                

            # frames TCL variable to be used across different commands
            self.append(f"set frames [get_sdb_frames -stims {stim_alias}]")

            # use set intersection to determine whether two lists have at least one element in common
            if {'report','all'} & output_formats:
                report_path = report_name
                if not report_path.startswith('/'):
                    save_dir = os.path.join(self.run_dir, 'report')
                    os.makedirs(save_dir, exist_ok=True)
                    report_path = os.path.join(save_dir, report_path)
                # -frames $frames explodes the runtime & doesn't seem to change result
                # NOTE: module_str causes it to error
                if levels_str == "": levels_str = "-levels all"
                self.block_append(f"report_power -stims {stim_alias} -by_hierarchy {levels_str} -unit mW -out {report_path}.rpt")
            if {'plot_profile','profile','all'} & output_formats:
                if not frame_based_analysis:
                    self.logger.error("Must specify either interval_size or toggle_signal+num_toggles in power.inputs.report_configs to generate plot_profile report (frame-based analysis).")
                    return False
                report_path = report_name
                if not report_path.startswith('/'):
                    save_dir = os.path.join(self.run_dir, 'plot_profile')
                    os.makedirs(save_dir, exist_ok=True)
                    report_path = os.path.join(save_dir, report_path)
                # NOTE: including the '-frames $frames ' argument results in this Joules error: "Error: Cannot specify frame#0 if other frames are specified with -frames.""
                # NOTE: we don't include levels_str here bc category is total power anyways
                self.block_append(f"plot_power_profile -stims {stim_alias} {inst_str} {module_str} -by_category {{total}} -types {{total}} -unit mW -format png -out {report_path}.png")
            if {'write_profile','profile','all'} & output_formats:
                report_path = report_name
                if not report_path.startswith('/'):
                    save_dir = os.path.join(self.run_dir, 'write_profile')
                    os.makedirs(save_dir, exist_ok=True)
                    report_path = os.path.join(save_dir, report_path)
                verbose_append(f"write_power_profile -stims {stim_alias} -root [get_insts -rtl_type hier] {levels_str} -unit mW -format fsdb -out {report_path}")

        saifs = self.get_setting("power.inputs.saifs")
        for saif in saifs:
            saif_basename = os.path.basename(saif)
            verbose_append("compute_power -mode time_based -stim {SAIF}".format(SAIF=saif_basename))
            verbose_append("report_power -stims {SAIF} -indent_inst -unit mW -out {SAIF}.report".format(SAIF=saif_basename))

        return True

    def run_joules(self) -> bool:
        verbose_append = self.verbose_append

        """Close out the power script and run Joules"""
        # Quit Joules
        verbose_append("exit")

        # Create power analysis script
        now = datetime.now().strftime("%Y%m%d-%H%M%S")  # uniquefy TCL scripts so that multiple runs don't overwrite each other
        joules_tcl_filename = os.path.join(self.run_dir, f"joules-{self._waveform_name}-{now}.tcl")
        self.write_contents_to_path("\n".join(self.output), joules_tcl_filename)

        # Make sure that generated-scripts exists.
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        # Create load_power script pointing to latest (symlinked to post_<last ran step>).
        self.output.clear()
        assert self.do_pre_steps(self.first_step)
        self.append("read_db latest")
        self.write_contents_to_path("\n".join(self.output), self.load_power_tcl)

        with open(self.load_power_script, "w") as f:
            f.write(dedent(f"""
        #!/bin/bash
        cd {self.run_dir}
        source enter
        $JOULES_BIN -common_ui -files {self.load_power_tcl}
        """))
        os.chmod(self.load_power_script, 0o755)

        self.create_enter_script()

        # Build args
        args = [
            self.get_setting("power.joules.joules_bin"),
            "-files", joules_tcl_filename,
            "-common_ui",
            "-batch"
        ]

        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False

        self.run_executable(args, cwd=self.run_dir)

        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        return True

# def joules_global_settings(ht: HammerTool) -> bool:
#     """Settings that need to be reapplied at every tool invocation"""
#     assert isinstance(ht, HammerPlaceAndRouteTool)
#     assert isinstance(ht, CadenceTool)
#     ht.create_enter_script()

#     return True


tool = Joules
