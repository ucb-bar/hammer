#  hammer-vlsi plugin for Cadence Joules.
#
#  See LICENSE for licence details.

from typing import List, Dict, Optional

import os

from hammer.vlsi import HammerPowerTool, HammerToolStep, MMMCCornerType, FlowLevel
from hammer.logging import HammerVLSILogging

from hammer.common.cadence import CadenceTool


class Joules(HammerPowerTool, CadenceTool):

    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None

    def tool_config_prefix(self) -> str:
        return "power.joules"

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = dict(super().env_vars)
        new_dict["JOULES_BIN"] = self.get_setting("power.joules.joules_bin")
        return new_dict

    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.check_level,
            self.init_technology,
            self.init_design,
            self.read_stimulus,
            self.synthesize_design,
            self.compute_power,
            self.report_power,
            self.run_joules
        ])

    def check_level(self) -> bool:
        if self.level == FlowLevel.RTL or self.level == FlowLevel.SYN:
            return True
        else:
            self.logger.error("The FlowLevel is invalid. The Joules plugin only supports RTL and post-synthesis analysis. Check your power tool setting and flow step.")
            return False

    def init_technology(self) -> bool:
        # libs, define RAMs, define corners
        verbose_append = self.verbose_append
        verbose_append("set_multi_cpu_usage -local_cpu {}".format(self.get_setting("vlsi.core.max_threads")))

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
        verbose_append = self.verbose_append

        top_module = self.get_setting("power.inputs.top_module")
        tb_name = self.tb_name
        # Replace . to / formatting in case argument passed from sim tool
        tb_dut = self.tb_dut.replace(".", "/")

        # We are switching working directories and Joules still needs to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))  # type: List[str]
        if self.level == FlowLevel.RTL:
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
            verbose_append("read_netlist {}".format(" ".join(abspath_input_files)))

            # Read in the post-synth SDCs
            verbose_append("read_sdc {}".format(self.sdc))

        return True

    def read_stimulus(self) -> bool:
        verbose_append = self.verbose_append

        top_module = self.get_setting("power.inputs.top_module")
        tb_name = self.tb_name
        # Replace . to / formatting in case argument passed from sim tool
        tb_dut = self.tb_dut.replace(".", "/")

        # Generate average power report for all waveforms
        waveforms = self.waveforms
        for i, waveform in enumerate(waveforms):
            waveform = os.path.join(os.getcwd(), waveform)
            verbose_append("read_stimulus -file {WAVE} -dut_instance {TB}/{DUT} -alias {WAVE_NAME}_{NUM} -append".format(WAVE=waveform, TB=tb_name, DUT=tb_dut, WAVE_NAME=os.path.basename(waveform), NUM=i))

        # Generate Specified and Custom Reports
        reports = self.get_power_report_configs()

        for i, report in enumerate(reports):
            waveform = os.path.basename(report.waveform_path)
            waveform = os.path.join(os.getcwd(), waveform)

            read_stim_cmd = "read_stimulus -file {WAVE_PATH} -dut_instance {TB}/{DUT} -append".format(WAVE_PATH=report.waveform_path, TB=tb_name, DUT=tb_dut)

            if report.start_time:
                read_stim_cmd += " -start {STIME}".format(STIME=report.start_time.value_in_units("ns"))

            if report.end_time:
                read_stim_cmd += " -end {ETIME}".format(ETIME=report.end_time.value_in_units("ns"))

            if report.toggle_signal:
                if report.num_toggles:
                    read_stim_cmd += " -cycles {NUM} {SIGNAL}".format(NUM=report.num_toggles, SIGNAL=report.toggle_signal)
                else:
                    self.logger.error("Must specify the number of toggles if the toggle signal is specified.")
                    return False

            if report.frame_count:
                read_stim_cmd += " -frame_count {FRAME_COUNT}".format(FRAME_COUNT=report.frame_count)


            read_stim_cmd += " -alias report_{WAVE}_{NUM}".format(WAVE=waveform, NUM=i)

            verbose_append(read_stim_cmd)

        saifs = self.get_setting("power.inputs.saifs")
        for saif in saifs:
            saif_basename = os.path.basename(saif)
            verbose_append("read_stimulus {SAIF} -dut_instance {TB}/{DUT} -format saif -alias {NAME} -append".format(SAIF=saif, TB=tb_name, DUT=tb_dut, NAME=saif_basename))

        return True


    def synthesize_design(self) -> bool:
        verbose_append = self.verbose_append

        if self.level == FlowLevel.RTL:
            # Generate and read the SDCs
            sdc_files = self.generate_sdc_files()  # type: List[str]
            verbose_append("read_sdc {}".format(" ".join(sdc_files)))
            verbose_append("syn_power -effort medium")

        return True


    def compute_power(self) -> bool:
        verbose_append = self.verbose_append

        verbose_append("compute_power -mode time_based")

        return True


    def report_power(self) -> bool:
        verbose_append = self.verbose_append

        top_module = self.get_setting("power.inputs.top_module")
        tb_name = self.tb_name
        # Replace . to / formatting in case argument passed from sim tool
        tb_dut = self.tb_dut.replace(".", "/")

        for i, wave in enumerate(self.waveforms):
            verbose_append("report_power -stims {WAVE}_{NUM} -indent_inst -unit mW -append -out waveforms.report".format(WAVE=os.path.basename(wave), NUM=i))

        reports = self.get_power_report_configs()

        for i, report in enumerate(reports):
            waveform = os.path.basename(report.waveform_path)

            module_str = ""
            if report.module:
                module_str = " -module {MODULE}".format(MODULE=report.module)

            levels_str = ""
            if report.levels:
                levels_str = " -levels {LEVELS}".format(LEVELS=report.levels)

            stim_alias = "report_{WAVE}_{NUM}".format(WAVE=waveform, NUM=i)
            if report.report_name:
                report_name = report.report_name
            else:
                report_name = stim_alias + ".report"

            verbose_append("report_power -frames [get_sdb_frames {STIM_ALIAS}] -collate none -cols total -by_hierarchy{MODULE}{LEVELS} -indent_inst -unit mW -out {REPORT_NAME}".format(
                STIM_ALIAS=stim_alias,
                MODULE=module_str,
                LEVELS=levels_str,
                REPORT_NAME=report_name))

        saifs = self.get_setting("power.inputs.saifs")
        for saif in saifs:
            saif_basename = os.path.basename(saif)
            verbose_append("report_power -stims {SAIF} -indent_inst -unit mW -out {SAIF}.report".format(SAIF=saif_basename))

        return True

    def run_joules(self) -> bool:
        verbose_append = self.verbose_append

        """Close out the power script and run Joules"""
        # Quit Joules
        verbose_append("exit")

        # Create power analysis script
        joules_tcl_filename = os.path.join(self.run_dir, "joules.tcl")
        self.write_contents_to_path("\n".join(self.output), joules_tcl_filename)

        # Build args
        args = [
            self.get_setting("power.joules.joules_bin"),
            "-files", joules_tcl_filename,
            "-common_ui"
        ]

        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False

        self.run_executable(args, cwd=self.run_dir)

        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        return True



tool = Joules
