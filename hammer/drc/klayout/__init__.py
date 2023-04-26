# Klayout DRC plugin for Hammer
#
# See LICENSE for licence details.

import os
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any

from hammer.logging import HammerVLSILogging
from hammer.utils import deepdict
from hammer.vlsi import HammerToolStep
from hammer.vlsi import HammerDRCTool, TCLTool

class Klayout(HammerDRCTool, TCLTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            # no steps
        ])

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_klayout()

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    def fill_outputs(self) -> bool:
        return True
    
    def tool_config_prefix(self) -> str:
        return "drc.magic"

    def drc_results_pre_waived(self) -> Dict[str, int]:
        return {}

    def globally_waived_drc_rules(self) -> List[str]:
        return []

    def version_number(self, version:str) -> int:
        """Get version from klayout bin"""
        version = self.run_executable([self.get_setting("drc.klayout.klayout_bin"), "-v"])
        return int(version.replace(".", ""))

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def view_drc_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_drc")
    
    @property 
    def report_name(self) -> str:
        return os.path.join(self.run_dir, f"{self.top_module}.lydrc")

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def run_klayout(self) -> bool:
        drc_decks = self.get_drc_decks()
        if len(drc_decks) == 0 or len(drc_decks) > 1:
            self.logger.error("None or more than 1 tech file (DRC deck) found. Klayout only supports 1.")

        klayout_bin = self.get_setting('drc.klayout.klayout_bin')
        args = [
            klayout_bin,
            "-b", # batch mode    
            "-r", drc_decks[0].path, # Execute main script on startup (after having loaded files etc.)
            # script variables:
            "-rd", f"input={self.layout_file}",
            "-rd", f"report={self.report_name}",
        ]
        """
        Create view_drc script. This opens interactive window but has to run DRC
        all over again because there is no DRC database that can be loaded in.
        """
        os.makedirs(self.generated_scripts_dir, exist_ok=True)
        lyp_file = self.get_setting('drc.klayout.layout_properties_file')
        lyp_arg = "" if lyp_file is None else f"-l {lyp_file}"
        with open(self.view_drc_script, "w") as f:
            f.write(dd(f"""
            cd {self.run_dir}
            {klayout_bin} {self.layout_file} -m {self.report_name} {lyp_arg}
            #   -m: load RDB (report database) file (into previous layout view)
            """))
        os.chmod(self.view_drc_script, 0o755)

        if bool(self.get_setting("drc.klayout.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + \
                             " ".join(args))
        else:
            self.run_executable(args, cwd=self.run_dir) # TODO: check for errors

        return True

tool = Klayout
