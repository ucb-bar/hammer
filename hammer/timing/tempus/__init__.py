#  hammer-vlsi plugin for Cadence Tempus.
#
#  See LICENSE for licence details.

from typing import List, Dict, Tuple

import os
import errno

from hammer.vlsi import HammerTool, HammerTimingTool, HammerToolStep, HammerToolHookAction, \
       MMMCCornerType
from hammer.logging import HammerVLSILogging
import hammer.tech as hammer_tech
from hammer.common.cadence import CadenceTool

# Notes: this plugin should only use snake_case (common UI) commands.

class Tempus(HammerTimingTool, CadenceTool):

    def tool_config_prefix(self) -> str:
        return "timing.tempus"

    @property
    def env_vars(self) -> Dict[str, str]:
        v = dict(super().env_vars)
        v["TEMPUS_BIN"] = self.get_setting("timing.tempus.tempus_bin")
        return v

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
        # Restart from the last checkpoint if we're not starting over.
        # Not in the dofile, must be a command-line option
        if first_step != self.first_step:
            self.append("read_db pre_{step}".format(step=first_step.name))
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.append("write_db -overwrite pre_{step}".format(step=next.name))
        # Symlink the checkpoint to latest for open_db script later.
        self.append(f"ln -sfn pre_{next.name} latest")
        self._step_transitions = self._step_transitions + [(prev.name, next.name)]
        return True

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        # Create symlinks for post_<step> to pre_<step+1> to improve usability.
        try:
            for prev, next in self._step_transitions:
                os.symlink(
                    os.path.join(self.run_dir, f"pre_{next}"), # src
                    os.path.join(self.run_dir, f"post_{prev}") # dst
                )
        except OSError as e:
            if e.errno != errno.EEXIST:
                self.logger.warning("Failed to create post_* symlinks: " + str(e))

        # Create checkpoint post_<last step>
        # TODO: this doesn't work if you're only running the very last step
        if len(self._step_transitions) > 0:
            last = "post_{step}".format(step=self._step_transitions[-1][1])
            self.append("write_db -overwrite {last}".format(last=last))
            # Symlink the database to latest for open_db script later.
            self.append(f"ln -sfn {last} latest")

        return self.run_tempus() and self.generate_open_db()

    def get_tool_hooks(self) -> List[HammerToolHookAction]:
        return [self.make_persistent_hook(tempus_global_settings)]

    @property
    def steps(self) -> List[HammerToolStep]:
        steps = [
            self.init_design,
            self.run_sta
        ]
        return self.make_steps_from_methods(steps)

    def init_design(self) -> bool:
        """ Load design and analysis corners """
        verbose_append = self.verbose_append

        # Read timing libraries and generate timing constraints.
        # TODO: support non-MMMC mode, use standalone SDC instead
        # TODO: read AOCV or SOCV+LVF libraries if available
        mmmc_path = os.path.join(self.run_dir, "mmmc.tcl")
        self.write_contents_to_path(self.generate_mmmc_script(), mmmc_path)
        verbose_append("read_mmmc {mmmc_path}".format(mmmc_path=mmmc_path))

        # Read physical LEFs (optional in Tempus)
        lef_files = self.technology.read_libs([
            hammer_tech.filters.lef_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_lefs = list(map(lambda ilm: ilm.lef, self.get_input_ilms(full_tree=True)))
            lef_files.extend(ilm_lefs)
        verbose_append("read_physical -lef {{ {files} }}".format(
            files=" ".join(lef_files)
        ))

        # Read netlist.
        # Tempus only supports structural Verilog for the netlist; the Verilog can be optionally compressed.
        if not self.check_input_files([".v", ".v.gz"]):
            return False

        # We are switching working directories and we still need to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        verbose_append("read_netlist {{ {files} }} -top {top}".format(
            files=" ".join(abspath_input_files),
            top=self.top_module
        ))

        if self.hierarchical_mode.is_nonleaf_hierarchical():
            # Read ILMs.
            for ilm in self.get_input_ilms(full_tree=True):
                # Assumes that the ILM was created by Innovus (or at least the file/folder structure).
                # TODO: support non-Innovus hierarchical (read netlists, etc.)
                verbose_append("set_ilm -cell {module} -in_dir {dir}".format(dir=ilm.dir, module=ilm.module))

        # Read power intent
        if self.get_setting("vlsi.inputs.power_spec_mode") != "empty":
            # Setup power settings from cpf/upf
            for l in self.generate_power_spec_commands():
                verbose_append(l)

        verbose_append("init_design")

        if self.def_file is not None:
            verbose_append("read_def " + os.path.join(os.getcwd(), self.def_file))

        # Read parasitics
        if self.spefs is not None: # post-P&R
            corners = self.get_mmmc_corners()
            if corners:
                rc_corners = [] # type: List[str]
                for corner in corners:
                    # Setting up views for all defined corner types: setup, hold, extra
                    if corner.type is MMMCCornerType.Setup:
                        corner_name = "{n}.{t}".format(n=corner.name, t="setup")
                    elif corner.type is MMMCCornerType.Hold:
                        corner_name = "{n}.{t}".format(n=corner.name, t="hold")
                    elif corner.type is MMMCCornerType.Extra:
                        corner_name = "{n}.{t}".format(n=corner.name, t="extra")
                    else:
                        raise ValueError("Unsupported MMMCCornerType")
                    rc_corners.append("{n}_rc".format(n=corner_name))

                # Match spefs with corners. Ordering must match (ensured here by get_mmmc_corners())!
                for (spef, rc_corner) in zip(self.spefs, rc_corners):
                    verbose_append("read_spef {spef} -rc_corner {corner}".format(spef=os.path.join(os.getcwd(), spef), corner=rc_corner))

            else:
                verbose_append("read_spef " + os.path.join(os.getcwd(), self.spefs[0]))

        # Read delay data (optional in Tempus)
        if self.sdf_file is not None:
            verbose_append("read_sdf " + os.path.join(os.getcwd(), self.sdf_file))

        if self.hierarchical_mode.is_nonleaf_hierarchical() and len(self.get_input_ilms(full_tree=True)):
            verbose_append("read_ilm")
            verbose_append("flatten_ilm")

        # Set some default analysis settings for max accuracy
        # Clock path pessimism removal
        verbose_append("set_db timing_analysis_cppr both")
        # On-chip variation analysis
        verbose_append("set_db timing_analysis_type ocv")
        # Partial path-based analysis even in graph-based analysis mode
        verbose_append("set_db timing_analysis_graph_pba_mode true")
        # Equivalent waveform model w/ waveform propagation
        verbose_append("set_db delaycal_equivalent_waveform_model propagation")

        # Enable signal integrity delay and glitch analysis
        if self.get_setting("timing.tempus.si_glitch"):
            verbose_append("set_db si_num_iteration 3")
            verbose_append("set_db si_delay_enable_report true")
            verbose_append("set_db si_delay_separate_on_data true")
            verbose_append("set_db si_delay_enable_logical_correlation true")
            verbose_append("set_db si_glitch_enable_report true")
            verbose_append("set_db si_enable_glitch_propagation true")
            verbose_append("set_db si_enable_glitch_overshoot_undershoot true")
            verbose_append("set_db delaycal_enable_si true")
            verbose_append("set_db timing_enable_timing_window_pessimism_removal true")
            # Check for correct noise models (ECSMN, CCSN, etc.)
            verbose_append("check_noise")

        return True

    def run_sta(self) -> bool:
        """ Run Static Timing Analysis """
        verbose_append = self.verbose_append

        # report_timing
        verbose_append("set_db timing_report_timing_header_detail_info extended")
        # Note this reports everything - setup, hold, recovery, etc.
        verbose_append(f"report_timing -retime path_slew_propagation -max_paths {self.max_paths} > timing.rpt")
        verbose_append(f"report_timing -unconstrained -debug unconstrained -max_paths {self.max_paths} > unconstrained.rpt")

        if self.get_setting("timing.tempus.si_glitch"):
            # SI max/min delay
            verbose_append("report_noise -delay max -out_file max_si_delay")
            verbose_append("report_noise -delay min -out_file min_si_delay")
            # Glitch and summary histogram
            verbose_append("report_noise -out_file glitch")
            verbose_append("report_noise -histogram")

        return True

    def generate_open_db(self) -> bool:
        # Make sure that generated-scripts exists.
        generated_scripts_dir = os.path.join(self.run_dir, "generated-scripts")
        os.makedirs(generated_scripts_dir, exist_ok=True)

        # Script to open results checkpoint
        self.output.clear()
        self.create_enter_script()
        open_db_tcl = os.path.join(generated_scripts_dir, "open_db.tcl")
        assert super().do_pre_steps(self.first_step)
        self.append("read_db latest")
        self.write_contents_to_path("\n".join(self.output), open_db_tcl)
        open_db_script = os.path.join(generated_scripts_dir, "open_db")
        with open(open_db_script, "w") as f:
            f.write("""#!/bin/bash
        cd {run_dir}
        source enter
        $TEMPUS_BIN -stylus -files {open_db_tcl}
                """.format(run_dir=self.run_dir, open_db_tcl=open_db_tcl))
        os.chmod(open_db_script, 0o755)

        return True

    def run_tempus(self) -> bool:
        # Quit
        self.append("exit")

        # Write main dofile
        timing_script = os.path.join(self.run_dir, "timing.tcl")
        self.write_contents_to_path("\n".join(self.output), timing_script)

        # Build args
        # TODO: enable Signoff ECO with -tso (-eco?) option
        args = [
            self.get_setting("timing.tempus.tempus_bin"),
            "-no_gui", # no GUI
            "-stylus", # common UI
            "-files", timing_script
        ]

        # Temporarily disable colours/tag to make run output more readable.
        # TODO: think of a more elegant way to do this?
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir)
        # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # TODO: check that timing run was successful

        return True

def tempus_global_settings(ht: HammerTool) -> bool:
    """Settings that need to be reapplied at every tool invocation"""
    assert isinstance(ht, HammerTimingTool)
    assert isinstance(ht, CadenceTool)
    ht.create_enter_script()

    # Python sucks here for verbosity
    verbose_append = ht.verbose_append

    # Generic settings
    verbose_append("set_db design_process_node {}".format(ht.get_setting("vlsi.core.node")))
    verbose_append("set_multi_cpu_usage -local_cpu {}".format(ht.get_setting("vlsi.core.max_threads")))

    return True

tool = Tempus
