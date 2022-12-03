# Magic DRC plugin for Hammer
#
# See LICENSE for licence details.

import os
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any

from hammer.logging import HammerVLSILogging
from hammer.utils import deepdict
from hammer.vlsi import HammerToolStep
from hammer.vlsi import HammerDRCTool, TCLTool

class Magic(HammerDRCTool, TCLTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.init_design,
            self.run_drc
        ])

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_magic()

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
        """Get version from magic bin"""
        version = self.run_executable([self.get_setting("drc.magic.magic_bin"), "--version"])
        return int(version.replace(".", ""))

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def view_drc_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_drc")

    @property
    def view_drc_tcl(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_drc.tcl")

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def run_magic(self) -> bool:
        self.append("quit")

        run_script = os.path.join(self.run_dir, "drc.tcl")
        with open(run_script, "w") as f:
            f.write("\n".join(self.output))

        args = [self.get_setting("drc.magic.magic_bin")]
        rcfile = self.get_setting("drc.magic.rcfile")
        techfile = self.get_drc_decks()

        if rcfile is not None:
            args.extend(["-rcfile", rcfile])
        else:
            # DRC deck should be the tech file. There should only be 1.
            if len(techfile) == 0 or len(techfile) > 1:
                self.logger.error("None or more than 1 tech file (DRC deck) found. netgen only supports 1.")
            args.extend(["-T", techfile[0]])

        """
        Create view_drc script. This opens interactive window but has to run DRC
        all over again because there is no DRC database that can be loaded in.
        """
        os.makedirs(self.generated_scripts_dir, exist_ok=True)
        with open(self.view_drc_script, "w") as f:
            f.write(dd("""
            cd {run_dir}
            {args} {gds} {run_script}
            """.format(
                run_dir = self.run_dir,
                args = " ".join(args),
                gds = self.layout_file,
                run_script = self.view_drc_tcl
                )))
        os.chmod(self.view_drc_script, 0o755)
        with open(self.view_drc_tcl, "w") as f:
            f.write(dd("""
            load {top}
            select top cell
            drc check
            """.format(top = self.top_module)))

        # Finally append the no GUI options and full Tcl run script
        args.extend(["-noconsole", "-dnull", run_script])

        if bool(self.get_setting("drc.magic.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + \
                             " ".join(args))
        else:
            # Temporarily disable colors/tag to make run output more readable
            # TODO: think of a more elegant way to do this?
            HammerVLSILogging.enable_colour = False
            HammerVLSILogging.enable_tag = False
            self.run_executable(args, cwd=self.run_dir) # TODO: check for errors
            HammerVLSILogging.enable_colour = True
            HammerVLSILogging.enable_tag = True

        return True

    #========================================================================
    # drc main steps
    #========================================================================
    def init_design(self) -> bool:
        """Read design and set up results outputs"""
        self.append("gds read " + self.layout_file)
        self.append("load " + self.top_module)
        self.append("select top cell")
        self.append("set oscale [cif scale out]")

        # Results output is taken from output of certain commands
        # Hooks that also write to it should use the $fout variable
        self.append("set fout [open drc.out w]")

        self.append(self.get_additional_drc_text())
        return True

    def run_drc(self) -> bool:
        """Run DRC and dump error boxes"""
        self.append('puts "Running DRC..."')
        self.append("drc check")
        self.append("set flat_count 0")

        # Adapted from OpenLane
        self.append('puts $fout "----------------------------------------"')
        self.append("set drcresult [drc listall why]")
        self.append('''
        foreach {errtype coordlist} $drcresult {
            puts $fout $errtype
            puts $fout "----------------------------------------"
            foreach coord $coordlist {
                set bllx [expr {$oscale * [lindex $coord 0]}]
                set blly [expr {$oscale * [lindex $coord 1]}]
                set burx [expr {$oscale * [lindex $coord 2]}]
                set bury [expr {$oscale * [lindex $coord 3]}]
                set coords [format " %.3fum %.3fum %.3fum %.3fum" $bllx $blly $burx $bury]
                puts $fout "$coords"
                incr flat_count
            }
            puts $fout "----------------------------------------"
        }
        puts $fout ""
        close $fout
        ''')

        # Error counts
        # TODO: hierarchical counts don't work in noconsole mode...
        #self.append('puts "Hierarchical DRC error counts:"')
        #self.append("puts [drc listall count]")
        self.append('puts "Flat DRC error count: $flat_count"')
        return True

tool = Magic
