#  hammer-vlsi plugin for Cadence Pegasus.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerToolStep
from hammer.vlsi import HammerDRCTool
from hammer.common.cadence import CadenceTool
from hammer.logging import HammerVLSILogging

from typing import Dict, List, Optional

import os
import textwrap


class PegasusDRC(HammerDRCTool, CadenceTool):

    def tool_config_prefix(self) -> str:
        return "drc.pegasus"

    def drc_results_pre_waived(self) -> Dict[str, int]:
        return {}

    def fill_outputs(self) -> bool:
        return True

    # TODO: placeholder empty step
    def empty_step(self) -> bool:
        return True

    @property
    def steps(self) -> List[HammerToolStep]:
        steps = [self.generate_drc_ctl_file]  # TODO: DRC steps require multiple runs of the tool how do we support this?
        return self.make_steps_from_methods(steps)

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_pegasus()

    def globally_waived_drc_rules(self) -> List[str]:
        return []

    def run_pegasus(self) -> bool:
        self.create_enter_script()

        rules = list(map(lambda d: d.path, self.get_drc_decks()))

        # set the command arguments
        pegasus_bin = self.get_setting("drc.pegasus.pegasus_bin")
        args = [
            pegasus_bin,
            "-drc",  # DRC mode
            "-dp", str(self.get_setting("vlsi.core.max_threads")),
            "-license_dp_continue",  # don't quit if requested dp license not available
            "-control", self.drc_ctl_file,
            "-log_dir", f"{self.top_module}_logs",
            "-ui_data"  # for results viewer
            # TODO: -interactive for block level
            ] + rules

        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir)  # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # TODO: check that drc run was successful

        # Create view_drc script & design review macro script file
        # See the README for how this works
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        technology = self.get_setting("vlsi.core.technology").split(".")[-1]
        with open(self.view_drc_script, "w") as f:
            f.write(textwrap.dedent(f"""
        cd {self.run_dir}
        source ./enter
        {pegasus_bin}DesignReview -qrv -tech {technology} -data {self.layout_file} -post {self.dr_rv_macro} -verbose
        """))
        os.chmod(self.view_drc_script, 0o755)

        with open(self.dr_rv_macro, "w") as f:
            f.write(textwrap.dedent(f'''
        PVS::invoke_pvsrv("{self.run_dir}");
        '''))

        return True

    def generate_drc_ctl_file(self) -> bool:
        """ Generate the DRC control file self.drc_ctl_file and fill its contents """
        with open(self.drc_ctl_file, "w") as f:
            f.write(self.header.replace("#","//"))
            f.write(textwrap.dedent(f'''
            virtual_connect -report yes;
            layout_path "{self.layout_file}";
            layout_primary {self.top_module};
            results_db -drc "{self.drc_results_db}" -ascii;
            report_summary -drc "{self.drc_results_file}" -replace;
            '''))
            f.write(self.get_additional_drc_text())
        return True

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def view_drc_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_drc")

    @property
    def dr_rv_macro(self) -> str:
        return os.path.join(self.generated_scripts_dir, "dr.mac")

    @property
    def drc_ctl_file(self) -> str:
        return os.path.join(self.run_dir, "pegasusdrcctl")

    @property
    def drc_results_db(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".drc_errors.ascii")

    @property
    def drc_results_file(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".drc_results")

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        v = dict(super().env_vars)
        v["PEGASUS_BIN"] = self.get_setting("drc.pegasus.pegasus_bin")
        return v

    @property
    def post_synth_sdc(self) -> Optional[str]:
        pass

tool = PegasusDRC
