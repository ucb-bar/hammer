#  hammer-vlsi plugin for Cadence Conformal.
#
#  See LICENSE for licence details.

from typing import List, Dict, Tuple

import os
import errno

from hammer.vlsi import HammerFormalTool, HammerToolStep
from hammer.logging import HammerVLSILogging
import hammer.tech as hammer_tech
from hammer.common.cadence import CadenceTool

# Notes: Tcl mode is enabled for harmonization with other Cadence tools and additional Tcl functionality.
# There is a minor performance hit with database operations vs. native language.

class Conformal(HammerFormalTool, CadenceTool):

    def tool_config_prefix(self) -> str:
        return "formal.conformal"

    @property
    def env_vars(self) -> Dict[str, str]:
        v = dict(super().env_vars)
        if self.check in ["constraint", "cdc"]:
            v["CONFORMAL_BIN"] = self.get_setting("formal.conformal.conformal_ccd_bin")
        else:
            v["CONFORMAL_BIN"] = self.get_setting("formal.conformal.conformal_lec_bin")
        return v

    @property
    def start_cmd(self) -> List[str]:
        """ Generate required startup command based on the requested check and license level """
        lec_bin = self.get_setting("formal.conformal.conformal_lec_bin")
        ccd_bin = self.get_setting("formal.conformal.conformal_ccd_bin")
        license = self.get_setting("formal.conformal.license")
        cmd = ["", ""]
        if not license in ["L", "XL", "GXL"]:
            self.logger.error("License must be L, XL, or GXL. For CCD, -MCC is equivalent to GXL here.")

        if self.check == "lec":
            cmd = [lec_bin, f"-{license}"]
        elif self.check == "power":
            if license == "L":
                self.logger.error("power not supported with L license")
            else:
                cmd = [lec_bin, f"-LP{license}"]
        elif self.check == "eco":
            if license == "L":
                self.logger.error("eco not supported with L license")
            elif license == "XL":
                cmd = [lec_bin, "-ECO"]
            else:
                cmd = [lec_bin, "-ECOGXL"]
        elif self.check == "property":
            return [lec_bin, "-VERIFY"]
        elif self.check in ["constraint", "cdc"]:
            if license == "GXL":
                cmd = [ccd_bin, "-MCC"]
            else:
                cmd = [ccd_bin, f"-{license}"]
        else:
            self.logger.error("Unsupported check type")

        return cmd

    def check_reference_files(self, extensions: List[str]) -> bool:
        """
        Verify that reference files exist and have the specified extensions.
        Analogous to check_input_files in HammerTool.

        :param extensions: List of extensions e.g. [".v", ".sv"]
        :return: True if all files exist and have the specified extensions.
        """
        refs = self.reference_files
        error = False
        for r in refs:
            if not r.endswith(tuple(extensions)):
                self.logger.error(f"Input of unsupported type {r} detected!")
                error = True
            if not os.path.isfile(r):
                self.logger.error(f"Input file {r} does not exist!")
                error = True
        return not error

    @property
    def restart_checkpoint(self) -> str:
        """ Name of checkpoint to be restarted from (set by do_pre_steps) """
        return self.attr_getter("_restart_checkpoint", "")

    @restart_checkpoint.setter
    def restart_checkpoint(self, val: str) -> None:
        self.attr_setter("_restart_checkpoint", val)

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
            self.restart_checkpoint = f"pre_{first_step.name}"
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.append(f"checkpoint pre_{next.name} -replace")
        # Symlink the checkpoint to latest for open_checkpoint script later.
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
            last = f"post_{self._step_transitions[-1][1]}"
            self.append(f"checkpoint {last} -replace")
            # Symlink the database to latest for open_checkpoint script later.
            self.append(f"ln -sfn {last} latest")

        return self.generate_open_checkpoint() and self.run_conformal()

    @property
    def steps(self) -> List[HammerToolStep]:
        if self.check != "lec":
            self.logger.error("Check type {self.check} not yet supported!")
        steps = [
            self.setup_designs,
            self.compare_designs
        ]
        return self.make_steps_from_methods(steps)

    def setup_designs(self) -> bool:
        """ Setup the designs """
        append = self.append

        # Exit on dofile error
        append("set_dofile_abort exit")

        # Multithreading (max 16 allowed by tool)
        max_threads = min(self.get_setting("vlsi.core.max_threads"), 16)
        append(f"set_parallel_option -threads 1,{max_threads}")

        # Read libraries (macros, stdcells)
        # TODO: support VHDL + Liberty. For now, -sva = SystemVerilog w/ assertion support.
        lib_v_files = self.technology.read_libs(
                [hammer_tech.filters.verilog_synth_filter],
                hammer_tech.HammerTechnologyUtils.to_plain_item)
        lib_v_files.extend(self.technology.read_libs(
                [hammer_tech.filters.verilog_sim_filter],
                hammer_tech.HammerTechnologyUtils.to_plain_item))
        append(f"read_library {' '.join(lib_v_files)} -sva -bboxsolver -both")

        # Read designs
        valid_exts = [".v", ".v.gz", ".sv", ".sv.gz"]
        if not self.check_input_files(valid_exts) or not self.check_reference_files(valid_exts):
            return False
        golden_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.reference_files))
        append(f"read_design {' '.join(golden_files)} -sva -golden")
        revised_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))
        append(f"read_design {' '.join(revised_files)} -sva -revised")

        # Set top module
        append(f"set_root_module {self.top_module} -both")

        # Auto setup analysis optimizations
        if self.get_setting("formal.conformal.license") != "L":
            append("set_analyze_option -auto")

        # Setup reports
        append("report_design_data")

        return True

    def compare_designs(self) -> bool:
        """ Depending on license, performs flat or hierarchical comparison """
        append = self.append

        if self.get_setting("formal.conformal.license") == "L":
            append("report_black_box")
            append("set_system_mode lec")
            append("add_compare_point -all")
            append("compare")
            append("report_compare_data")
        else:
            # TODO: need resource file for DC-mapped netlists
            append('write_hier_compare_dofile hier_compare.tcl -replace '\
                   '-prepend_string "analyze_datapath -module; analyze_datapath"')
            append("run_hier_compare hier_compare.tcl")
            append("set_system_mode lec")

        append("report_statistics")

        return True

    def generate_open_checkpoint(self) -> bool:
        # Make sure that generated-scripts exists.
        generated_scripts_dir = os.path.join(self.run_dir, "generated-scripts")
        os.makedirs(generated_scripts_dir, exist_ok=True)

        # Script to open results checkpoint
        self.create_enter_script()
        open_checkpoint_tcl = os.path.join(generated_scripts_dir, "open_checkpoint.tcl")
        with open(open_checkpoint_tcl, "w") as f:
            f.write("set_gui -mapping")
        open_checkpoint_script = os.path.join(generated_scripts_dir, "open_checkpoint")
        with open(open_checkpoint_script, "w") as f:
            assert super().do_pre_steps(self.first_step)
            args = self.start_cmd
            args.extend(["-gui", "-restart_checkpoint", "latest"])
            f.write("#!/bin/bash\n")
            f.write(f"cd {self.run_dir}\n")
            f.write("source enter\n")
            f.write(f"$CONFORMAL_BIN -restart_checkpoint latest -dofile {open_checkpoint_tcl}")
        os.chmod(open_checkpoint_script, 0o755)

        return True

    def run_conformal(self) -> bool:
        # Quit
        self.append("exit")

        # Write main dofile
        dofile = os.path.join(self.run_dir, f"{self.check}.tcl")
        self.write_contents_to_path("\n".join(self.output), dofile)

        # Build args
        args = self.start_cmd
        args.extend([
            "-nogui",
            "-color",
            "-tclmode",
            "-dofile", dofile
        ])
        if self.restart_checkpoint != "":
            args.extend([
                "-restart_checkpoint",
                self.restart_checkpoint
            ])

        # Temporarily disable colours/tag to make run output more readable.
        # TODO: think of a more elegant way to do this?
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir)
        # TODO: check for errors and deal with them
        # According to user guide:
        # Bit   Condition
        # 0     Internal error
        # 1     Exit status before comparison
        # 2     Command error
        # 3     Unmapped points
        # 4     Non-equivalent points
        # 5     Abort or uncompared points exist during any comparison
        # 6     Abort or uncompared points exist during last comparison
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # TODO: check that formal run was successful

        return True

tool = Conformal
