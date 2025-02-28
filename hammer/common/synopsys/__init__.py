import datetime
import inspect
import os
from typing import Optional, Dict

from hammer.vlsi import HasSDCSupport, TCLTool, HammerTool


class SynopsysTool(HasSDCSupport, TCLTool, HammerTool):
    """Mix-in trait with functions useful for Synopsys-based tools."""

    ## FIXME: not used by any Synopsys tool
    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        result = dict(super().env_vars)
        result.update({
            "SNPSLMD_LICENSE_FILE": self.get_setting("synopsys.SNPSLMD_LICENSE_FILE"),
            # TODO: this is actually a Mentor Graphics licence, not sure why the old dc scripts depend on it.
            "MGLS_LICENSE_FILE": self.get_setting("synopsys.MGLS_LICENSE_FILE")
        })
        return result

    def version_number(self, version: str) -> int:
        """
        Assumes versions look like NAME-YYYY.MM-SPMINOR.
        Assumes less than 100 minor versions.
        
        Handles various version formats:
        - NAME-YYYY.MM (no minor version)
        - NAME-YYYY.MM-N (where N is a number like 4)
        - NAME-YYYY.MM-SPN (where SP is a prefix and N is a number)
        - NAME-YYYY.MM-PREFIXN (where PREFIX is any text and N is a number)
        """
        date = "-".join(version.split("-")[1:])  # type: str
        year = int(date.split(".")[0])  # type: int
        month = int(date.split(".")[1][:2])  # type: int
        minor_version = 0  # type: int
        if "-" in date:
            minor_part = date.split("-")[1]
            # Try to handle both formats: with prefix (like "SP4") and without (like "4")
            # If the minor part starts with non-digits, skip them
            for i, char in enumerate(minor_part):
                if char.isdigit():
                    minor_version = int(minor_part[i:])
                    break
        return (year * 100 + month) * 100 + minor_version

    @property
    def header(self) -> str:
        """
        Header for all generated Tcl scripts
        """
        header_text = f"""
        # ---------------------------------------------------------------------------------
        # Portions Copyright ©{datetime.date.today().year} Synopsys, Inc. All rights reserved. Portions of
        # these TCL scripts are proprietary to and owned by Synopsys, Inc. and may only be
        # used for internal use by educational institutions (including United States
        # government labs, research institutes and federally funded research and
        # development centers) on Synopsys tools for non-profit research, development,
        # instruction, and other non-commercial uses or as otherwise specifically set forth
        # by written agreement with Synopsys. All other use, reproduction, modification, or
        # distribution of these TCL scripts is strictly prohibited.
        # ---------------------------------------------------------------------------------
        """
        return inspect.cleandoc(header_text)

    def get_synopsys_rm_tarball(self, product: str, settings_key: str = "") -> str:
        """Locate reference methodology tarball.

        :param product: Either "DC" or "ICC"
        :param settings_key: Key to retrieve the version for the product. Leave blank for DC and ICC.
        """
        key = self.tool_config_prefix() + "." + "version" # type: str

        synopsys_rm_tarball = os.path.join(self.get_setting("synopsys.rm_dir"), "%s-RM_%s.tar" % (product, self.get_setting(key)))
        if not os.path.exists(synopsys_rm_tarball):
            # TODO: convert these to logger calls
            raise FileNotFoundError("Expected reference methodology tarball not found at %s. Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a DC reference methodology. If these tarballs have been pre-downloaded, you can set synopsys.rm_dir instead of generating them yourself." % (synopsys_rm_tarball))
        else:
            return synopsys_rm_tarball