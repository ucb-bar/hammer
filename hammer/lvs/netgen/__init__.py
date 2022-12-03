# Netgen LVS plugin for Hammer
#
# See LICENSE for licence details.

import os
from textwrap import dedent as dd
from typing import List, Optional, Dict, Any

from hammer.logging import HammerVLSILogging
from hammer.utils import deepdict, get_or_else
from hammer.vlsi import HammerToolStep
from hammer.vlsi import HammerLVSTool, TCLTool
import hammer.tech as hammer_tech

class Netgen(HammerLVSTool, TCLTool):

    #=========================================================================
    # overrides from parent classes
    #=========================================================================
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.run_ext2spice,
            self.run_lvs
        ])

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_netgen()

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = deepdict(super().env_vars)
        return new_dict

    def fill_outputs(self) -> bool:
        return True

    def tool_config_prefix(self) -> str:
        return "lvs.netgen"

    def erc_results_pre_waived(self) -> Dict[str, int]:
        return {}

    def globally_waived_erc_rules(self) -> List[str]:
        return []

    def lvs_results(self) -> List[str]:
        #TODO: extract LVS descriptions from netgen output
        return []

    def version_number(self, version:str) -> int:
        """Get version from netgen bin"""
        version = self.run_executable([self.get_setting("lvs.netgen.netgen_bin"), "-batch"])
        return int(version.replace(".", ""))

    @property
    def ext2spice_netlist(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".ext.sp")

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def view_lvs_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_lvs")

    #=========================================================================
    # useful subroutines
    #=========================================================================

    def run_netgen(self) -> bool:
        run_script = os.path.join(self.run_dir, "lvs.tcl")
        with open(run_script, "w") as f:
            f.write("\n".join(self.output))

        """
        Create view_lvs script. This opens interactive window but has to run LVS
        all over again because there is no LVS database that can be loaded in.
        TODO: parse the JSON output too, like OpenLane
        """
        os.makedirs(self.generated_scripts_dir, exist_ok=True)
        with open(self.view_lvs_script, "w") as f:
            f.write(dd("""
            cd {run_dir}
            {netgen_bin} source {run_script}
            """.format(
                run_dir = self.run_dir,
                netgen_bin = self.get_setting("lvs.netgen.netgen_bin"),
                run_script = run_script
                )))
        os.chmod(self.view_lvs_script, 0o755)

        args = [self.get_setting("lvs.netgen.netgen_bin"), "-batch", "source", run_script]


        # Finally append the no GUI options and full Tcl run script
        if bool(self.get_setting("lvs.netgen.generate_only")):
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
    # LVS main steps
    #========================================================================
    def run_ext2spice(self) -> bool:
        """
        Run magic ext2spice
        Adapted from OpenLane
        """
        # Skip if generated netlist newer than layout file
        if os.path.exists(self.ext2spice_netlist):
            if os.path.getmtime(self.layout_file) < os.path.getmtime(self.ext2spice_netlist):
                self.logger.info("Layout Spice file already generated, skipping...")
                return True

        # Magic args
        args = [self.get_setting("drc.magic.magic_bin"), "-noconsole", "-dnull"]
        rcfile = self.get_setting("drc.magic.rcfile")
        # Equivalent to get_drc_decks() for DRCTool
        techfile = self.technology.get_drc_decks_for_tool(self.get_setting("vlsi.core.drc_tool"))

        if rcfile is not None:
            args.extend(["-rcfile", rcfile])
        else:
            # DRC deck should be the tech file. There should only be 1.
            if len(techfile) == 0 or len(techfile) > 1:
                self.logger.error("None or more than 1 tech file (DRC deck) found. netgen only supports 1.")
            args.extend(["-T", techfile[0]])

        ext2spice_script = os.path.join(self.run_dir, "ext2spice.tcl")
        args.append(ext2spice_script)

        # Create folder for all .ext files
        os.makedirs(os.path.join(self.run_dir, "ext2spice-rundir"), exist_ok=True)

        # ext2spice script
        self.append("gds read " + self.layout_file)
        self.append("load " + self.top_module)
        self.append("cd ext2spice-rundir")
        self.append("extract do local") # extract into ext2spice-rundir
        self.append("extract no capacitance")
        self.append("extract no coupling")
        self.append("extract no resistance")
        self.append("extract no adjust")
        if not self.get_setting("lvs.netgen.connect_by_label"):
            self.append("extract unique")
        self.append("extract warn all")
        self.append("extract")
        self.append("ext2spice lvs")
        self.append("ext2spice -o " + self.ext2spice_netlist)
        self.append("feedback save ext2spice.log")
        self.append("quit")

        with open(ext2spice_script, "w") as f:
            f.write("\n".join(self.output))
        self.output.clear()

        if bool(self.get_setting("lvs.netgen.generate_only")):
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

    def run_lvs(self) -> bool:
        """
        Read all libraries (stdcells, macros), then run comparison
        Additional LVS text can then modify netlists
        TODO: break up lvs command into constituent parts for more control
        """
        # libs for circuit1. spice format must be specified.
        self.append('puts "Reading layout..."')
        self.append("readnet spice {} 1".format(self.ext2spice_netlist))

        # libs for circuit2. auto format detection (somewhat dangerous).
        self.append('puts "Reading schematics..."')
        library_spice_files = self.technology.read_libs([hammer_tech.filters.spice_filter], hammer_tech.HammerTechnologyUtils.to_plain_item)
        ilms = list(map(lambda x: x.netlist, self.ilms))  # type: List[str]
        for sch in self.schematic_files + ilms + library_spice_files:
            self.append('puts "Reading {}..."'.format(sch))
            self.append("readnet {} 2".format(sch))

        self.append(self.get_additional_lvs_text())

        self.append('puts "Running LVS..."')
        setup_file = self.get_setting("lvs.netgen.setup_file")
        self.append("lvs {{{top} 1}} {{{top} 2}} {setup} {top}.lvs.log -json".format(
                    top=self.top_module,
                    setup=get_or_else(setup_file, "nosetup")))
        return True

tool = Netgen
