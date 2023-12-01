#  hammer-vlsi plugin for Synopsys IC Validator.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerToolStep
from hammer.vlsi import HammerLVSTool
from hammer.common.synopsys import SynopsysTool
from hammer.logging import HammerVLSILogging
from hammer.utils import HammerFiletype, get_filetype
import hammer.tech as hammer_tech

from typing import Dict, List, Optional

import os
import textwrap


class ICVLVS(HammerLVSTool, SynopsysTool):

    def tool_config_prefix(self) -> str:
        return "lvs.icv"

    def erc_results_pre_waived(self) -> Dict[str, int]:
        return {}

    def lvs_results(self) -> List[str]:
        return []

    def fill_outputs(self) -> bool:
        return True

    # TODO: placeholder empty step
    def empty_step(self) -> bool:
        return True

    @property
    def steps(self) -> List[HammerToolStep]:
        steps = [self.generate_lvs_run_file, self.generate_lvs_args_file]  # TODO: LVS steps require multiple runs of the tool how do we support this?
        return self.make_steps_from_methods(steps)

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_icv()

    def globally_waived_erc_rules(self) -> List[str]:
        return []

    def run_icv(self) -> bool:
        self.create_enter_script()

        # translate all spice & verilog netlists with vue_nettran
        self.generate_top_icv_file()
        # generate the hcells file if needed
        self.generate_hcells_file()

        # set the command arguments
        args = [
            self.get_setting("lvs.icv.icv_lvs_bin"),
            "-64"]  # always want to be in 64-bit mode
        if self.version() >= self.version_number("R-2020.09"):
            args.extend(["-host_init", str(self.get_setting("vlsi.core.max_threads"))])
        else:
            args.append("-dp{}".format(self.get_setting("vlsi.core.max_threads")))
        args.extend([
            "-clf",
            self.lvs_args_file,
            "-vue",  # needed to view results in VUE
            "-verbose" # get more than % complete
        ])
        args.append(self.lvs_run_file)

        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir)  # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # TODO: check that lvs run was successful

        # Create view_lvs script & icvwb macro script file
        # See the README for how this works
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        with open(self.icvwb_macrofile, "w") as f:
            # Open socket
            f.write("user_socket open 0\n")
            # Layer mapping
            layerprops_file = self.get_setting("synopsys.layerprops")
            if layerprops_file is not None:
                f.writelines(l for l in open(layerprops_file))

        with open(self.view_lvs_script, "w") as f:
            f.write("""
        cd {run_dir}
        source ./enter
        # Start Synopsys IC Validator WorkBench and wait for port to open before starting VUE
        {icvwb} -socket {port} -run {macrofile} {gds} &
        while ! nc -z localhost {port}; do
            sleep 0.1
        done
        {icv_vue} -64 -load {results} -lay icwb -layArgs Port {port}
            """.format(
                run_dir=self.run_dir,
                icvwb=self.get_setting("lvs.icv.icvwb_bin"),
                port=self.get_setting("lvs.icv.icvwb_port"),
                macrofile=self.icvwb_macrofile,
                gds=self.layout_file,
                icv_vue=self.get_setting("lvs.icv.icv_vue_bin"),
                results=self.lvs_results_db
            ))
        os.chmod(self.view_lvs_script, 0o755)

        return True

    @property
    def hcells_file(self) -> str:
        return os.path.join(self.run_dir, "hcells")

    def generate_hcells_file(self) -> None:
        with open(self.hcells_file, "w") as f:
            f.write("")
            # TODO

    def generate_top_icv_file(self) -> None:
        library_spice_files = self.technology.read_libs([hammer_tech.filters.spice_filter], hammer_tech.HammerTechnologyUtils.to_plain_item)
        ilms = list(map(lambda x: x.netlist, self.get_input_ilms()))  # type: List[str]

        all_files = library_spice_files + self.schematic_files + ilms
        spice_files = list(filter(lambda x: get_filetype(x) is HammerFiletype.SPICE, all_files))
        verilog_files = list(filter(lambda x: get_filetype(x) is HammerFiletype.VERILOG, all_files))
        unmatched = set(all_files).symmetric_difference(set(spice_files + verilog_files))
        if unmatched:
            raise NotImplementedError("Unsupported netlist type for files: " + str(unmatched))

        args = [self.get_setting("lvs.icv.icv_nettran_bin"), "-sp-autoDetectBusdelimiter", "FIRST", "-sp"]
        args.extend(spice_files)
        args.extend(["-verilog"] + verilog_files)
        args.extend(["-outName", self.converted_icv_file])
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir)  # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

    def generate_lvs_run_file(self) -> bool:
        """ Generate the LVS run file self.lvs_run_file and fill its contents """
        with open(self.lvs_run_file, "w") as f:
            f.write(self.header.replace("#","//") + "\n\n")
            f.write(self.get_additional_lvs_text())
            # Include paths to all supplied decks
            for rule in self.get_lvs_decks():
                f.write("#include <{}>\n".format(rule.path))
        return True

    def generate_lvs_args_file(self) -> bool:
        """ Generate the LVS args file self.lvs_args_file and fill its contents """
        with open(self.lvs_args_file, "w") as f:
            f.write(textwrap.dedent("""
            # Generated by HAMMER
            -i {gds}\
            -c {top}\
            -f GDSII\
            -s {sch}\
            -sf ICV
            """).format(
                gds=self.layout_file,
                top=self.top_module,
                sch=self.converted_icv_file
            )
            )
            # Symbolic variables to set via command. Can also use #define <var> <value> in additional_lvs_text.
            defines = self.get_setting("lvs.icv.defines")  # type: List[Dict[str, str]]
            assert isinstance(defines, list)
            if len(defines) > 0:
                # Most comprehensive way of covering all List[Dict] possibilities
                f.write(" -D " + " -D ".join(map(lambda x: " -D ".join("=".join(_) for _ in x.items()), defines)))

            # Preprocessor directories to include
            include_dirs = self.get_setting("lvs.icv.include_dirs")  # type: List[str]
            assert isinstance(include_dirs, list)
            if len(include_dirs) > 0:
                f.write(" -I " + " -I ".join(include_dirs))

            # Config runset file
            config_rs = self.get_setting("lvs.icv.config_runset")  # type: Optional[str]
            if config_rs is not None:
                f.write(" -runset_config " + config_rs)
        return True

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def view_lvs_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_lvs")

    @property
    def icvwb_macrofile(self) -> str:
        return os.path.join(self.generated_scripts_dir, "icvwb_macrofile")

    @property
    def lvs_run_file(self) -> str:
        return os.path.join(self.run_dir, "lvs_run_file")

    @property
    def lvs_args_file(self) -> str:
        return os.path.join(self.run_dir, "lvs_args_file")

    @property
    def erc_results_file(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".LAYOUT_ERRORS")

    @property
    def lvs_results_db(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".vue")

    @property
    def lvs_results_file(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".LVS_ERRORS")

    @property
    def converted_icv_file(self) -> str:
        return os.path.join(self.run_dir, "{top}.icv".format(top=self.top_module))

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        result = dict(super().env_vars)
        result.update({
            "ICV_HOME_DIR": self.get_setting("lvs.icv.ICV_HOME_DIR"),
            "PATH": "{path}:{icv_home}/bin/LINUX.64".format(path=os.environ.copy()["PATH"], icv_home=self.get_setting("lvs.icv.ICV_HOME_DIR"))
        })
        return result


tool = ICVLVS
