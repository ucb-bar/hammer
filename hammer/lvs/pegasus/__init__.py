#  hammer-vlsi plugin for Cadence Pegasus.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerToolStep
from hammer.vlsi import HammerLVSTool
from hammer.common.cadence import CadenceTool
from hammer.logging import HammerVLSILogging
from hammer.utils import HammerFiletype, get_filetype
import hammer.tech as hammer_tech

from typing import Dict, List, Optional

import os
import textwrap


class PegasusLVS(HammerLVSTool, CadenceTool):

    def tool_config_prefix(self) -> str:
        return "lvs.pegasus"

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
        steps = [self.generate_lvs_ctl_file]  # TODO: LVS steps require multiple runs of the tool how do we support this?
        return self.make_steps_from_methods(steps)

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return self.run_pegasus()

    def globally_waived_erc_rules(self) -> List[str]:
        return []

    def run_pegasus(self) -> bool:
        self.create_enter_script()

        rules = list(map(lambda d: d.path, self.get_lvs_decks()))

        # set the command arguments
        pegasus_bin = self.get_setting("lvs.pegasus.pegasus_bin")
        args = [
            pegasus_bin,
            "-lvs",  # LVS mode
            "-dp", str(self.get_setting("vlsi.core.max_threads")),
            "-license_dp_continue",  # don't quit if requested dp license not available
            "-automatch",  # hierarchical correspondence
            "-check_schematic",  # check schematic integrity
            "-control", self.lvs_ctl_file,
            "-log_dir", f"{self.top_module}_logs",
            "-ui_data"  # for results viewer
            ] + rules

        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = False
        self.run_executable(args, cwd=self.run_dir)  # TODO: check for errors and deal with them
        HammerVLSILogging.enable_colour = True
        HammerVLSILogging.enable_tag = True

        # TODO: check that lvs run was successful

        # Create view_lvs script & design review macro script file
        # See the README for how this works
        os.makedirs(self.generated_scripts_dir, exist_ok=True)

        technology = self.get_setting("vlsi.core.technology").split(".")[-1]
        with open(self.view_lvs_script, "w") as f:
            f.write(textwrap.dedent(f"""
        cd {self.run_dir}
        source ./enter
        {pegasus_bin}DesignReview -qrv -tech {technology} -data {self.layout_file} -post {self.dr_rv_macro} -verbose
        """))
        os.chmod(self.view_lvs_script, 0o755)

        with open(self.dr_rv_macro, "w") as f:
            f.write(textwrap.dedent(f'''
        PVS::invoke_pvsrv("{self.run_dir}");
        '''))

        return True

    def generate_lvs_ctl_file(self) -> bool:
        """ Generate the LVS control file self.lvs_ctl_file and fill its contents """
        library_spice_files = self.technology.read_libs([hammer_tech.filters.spice_filter], hammer_tech.HammerTechnologyUtils.to_plain_item)
        ilms = list(map(lambda x: x.netlist, self.get_input_ilms()))  # type: List[str]

        all_files = library_spice_files + self.schematic_files + ilms
        spice_files = list(filter(lambda x: get_filetype(x) is HammerFiletype.SPICE, all_files))
        verilog_files = list(filter(lambda x: get_filetype(x) is HammerFiletype.VERILOG, all_files))
        unmatched = set(all_files).symmetric_difference(set(spice_files + verilog_files))
        if unmatched:
            raise NotImplementedError("Unsupported netlist type for files: " + str(unmatched))

        power_list="\n".join(map(lambda x: x.name, self.get_independent_power_nets()))
        ground_list="\n".join(map(lambda x: x.name, self.get_independent_ground_nets()))

        with open(self.lvs_ctl_file, "w") as f:
            f.write(self.header.replace("#","//") + "\n")
            for sf in spice_files:
                if os.path.basename(sf).split(".")[0] in ["cdl", "CDL"]:
                    f.write(f'schematic_path "{sf}" cdl;\n')
                else:
                    f.write(f'schematic_path "{sf}" spice;\n')
            for vf in verilog_files:
                f.write(f'schematic_path "{vf}" verilog -keep_backslash -detect_buses -check_inconsistent_instances -ignore_instances_with_missing_cell_master;\n')
            f.write(textwrap.dedent(f'''
            schematic_primary {self.top_module};
            layout_path "{self.layout_file}";
            layout_primary {self.top_module};
            lvs_power_name {power_list};
            lvs_ground_name {ground_list};
            lvs_find_shorts yes;
            lvs_report_opt S;
            results_db -erc "{self.erc_results_db}" -ascii;
            report_summary -erc "{self.erc_results_file}" -replace;
            lvs_report_file "{self.lvs_results_file}";
            '''))
            f.write(self.get_additional_lvs_text())
        return True

    @property
    def hcells_file(self) -> str:
        return os.path.join(self.run_dir, "hcells")

    def generate_hcells_file(self) -> None:
        with open(self.hcells_file, "w") as f:
            f.write("")
            # TODO

    @property
    def generated_scripts_dir(self) -> str:
        return os.path.join(self.run_dir, "generated-scripts")

    @property
    def view_lvs_script(self) -> str:
        return os.path.join(self.generated_scripts_dir, "view_lvs")

    @property
    def dr_rv_macro(self) -> str:
        return os.path.join(self.generated_scripts_dir, "dr.mac")

    @property
    def lvs_ctl_file(self) -> str:
        return os.path.join(self.run_dir, "pegasuslvsctl")

    @property
    def erc_results_db(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".erc_errors.ascii")

    @property
    def erc_results_file(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".erc_results")

    @property
    def lvs_results_file(self) -> str:
        return os.path.join(self.run_dir, self.top_module + ".lvs_results")

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        v = dict(super().env_vars)
        v["PEGASUS_BIN"] = self.get_setting("lvs.pegasus.pegasus_bin")
        return v

    @property
    def post_synth_sdc(self) -> Optional[str]:
        pass

tool = PegasusLVS
