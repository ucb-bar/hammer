from functools import reduce
from typing import List, Optional, Dict, Any, Callable
import os
import json
import copy
import inspect

from hammer.vlsi import HammerTool, HasSDCSupport, HasCPFSupport, HasUPFSupport, TCLTool, ILMStruct
from hammer.vlsi.constraints import MMMCCorner, MMMCCornerType
from hammer.utils import optional_map, add_dicts, reduce_list_str, add_lists
import hammer.tech as hammer_tech


class CadenceTool(HasSDCSupport, HasCPFSupport, HasUPFSupport, TCLTool, HammerTool):
    """Mix-in trait with functions useful for Cadence-based tools."""

    constraint_mode = "my_constraint_mode"

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        # Use the base extra_env_variables and ensure that our custom variables are on top.
        try:
            list_of_vars = self.get_setting("cadence.extra_env_vars")  # type: List[Dict[str, Any]]
            assert isinstance(list_of_vars, list)
        except KeyError:
            list_of_vars = []

        cadence_vars = {
            "CDS_LIC_FILE": self.get_setting("cadence.CDS_LIC_FILE"),
            "CADENCE_HOME": self.get_setting("cadence.cadence_home")
        }

        return reduce(add_dicts, [dict(super().env_vars)] + list_of_vars + [cadence_vars], {})

    def version_number(self, version: str) -> int:
        """
        Assumes versions look like MAJOR_ISRMINOR and we will have less than 100 minor versions.
        """
        main_version = int(version.split("_")[0]) # type: int
        minor_version = 0 # type: int
        if "_" in version:
            minor_version = int(version.split("_")[1][3:])
        return main_version * 100 + minor_version

    @property
    def header(self) -> str:
        """
        Header for all generated Tcl scripts
        """
        header_text = """
        # --------------------------------------------------------------------------------
        # This script was written and developed by HAMMER at UC Berkeley; however, the
        # underlying commands and reports are copyrighted by Cadence. We thank Cadence for
        # granting permission to share our research to help promote and foster the next
        # generation of innovators.
        # --------------------------------------------------------------------------------
        """
        return inspect.cleandoc(header_text)

    def get_timing_libs(self, corner: Optional[MMMCCorner] = None) -> str:
        """
        Helper function to get the list of ASCII timing .lib files in space separated format.
        Uses a preference filter to collect NLDM, ECSM, or CCS libraries.

        :param corner: Optional corner to consider. If supplied, this will use filter_for_mmmc to select libraries that
        match a given corner (voltage/temperature).
        :return: List of lib files separated by spaces
        """

        lib_pref = self.get_setting("vlsi.technology.timing_lib_pref")  # type: str

        pre_filters = optional_map(corner, lambda c: [self.filter_for_mmmc(voltage=c.voltage,
                                                                           temp=c.temp)])  # type: Optional[List[Callable[[hammer_tech.Library],bool]]]

        lib_args = self.technology.read_libs([hammer_tech.filters.get_timing_lib_with_preference(lib_pref)],
                                             hammer_tech.HammerTechnologyUtils.to_plain_item,
                                             extra_pre_filters=pre_filters)
        return " ".join(lib_args)

    def get_mmmc_qrc(self, corner: MMMCCorner) -> str:
        lib_args = self.technology.read_libs([hammer_tech.filters.qrc_tech_filter],
                                             hammer_tech.HammerTechnologyUtils.to_plain_item,
                                             extra_pre_filters=[
                                                 self.filter_for_mmmc(voltage=corner.voltage, temp=corner.temp)])
        return " ".join(lib_args)

    def get_qrc_tech(self) -> str:
        """
        Helper function to get the list of rc corner tech files in space separated format.

        :return: List of qrc tech files separated by spaces
        """
        lib_args = self.technology.read_libs([
            hammer_tech.filters.qrc_tech_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        return " ".join(lib_args)

    def generate_sdc_files(self) -> List[str]:
        """
        Generate SDC files for use in mmmc script.
        """
        sdc_files = [] # type: List[str]

        # Generate clock constraints
        clock_constraints_fragment = os.path.join(self.run_dir, "clock_constraints_fragment.sdc")
        self.write_contents_to_path(self.sdc_clock_constraints, clock_constraints_fragment)
        sdc_files.append(clock_constraints_fragment)

        # Generate port constraints.
        pin_constraints_fragment = os.path.join(self.run_dir, "pin_constraints_fragment.sdc")
        self.write_contents_to_path(self.sdc_pin_constraints, pin_constraints_fragment)
        sdc_files.append(pin_constraints_fragment)

        return sdc_files

    def generate_mmmc_script(self) -> str:
        """
        Output for the mmmc.tcl script.
        Innovus (init_design) requires that the timing script be placed in a separate file.

        :return: Contents of the mmmc script.
        """
        mmmc_output = []  # type: List[str]

        def append_mmmc(cmd: str) -> None:
            self.verbose_tcl_append(cmd, mmmc_output)

        sdc_files = self.generate_sdc_files()

        # Append any custom SDC files.
        sdc_files.extend(self.get_setting("vlsi.inputs.custom_sdc_files"))

        # Add the post-synthesis SDC, if present.
        post_synth_sdc = self.post_synth_sdc
        if post_synth_sdc is not None:
            sdc_files.append(post_synth_sdc)

        # TODO: add floorplanning SDC
        if len(sdc_files) > 0:
            sdc_files_arg = "-sdc_files [list {sdc_files}]".format(
                sdc_files=" ".join(sdc_files)
            )
        else:
            blank_sdc = os.path.join(self.run_dir, "blank.sdc")
            self.run_executable(["touch", blank_sdc])
            sdc_files_arg = "-sdc_files {{ {} }}".format(blank_sdc)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_sdcs = reduce_list_str(add_lists, list(map(lambda ilm: ilm.sdcs, self.get_input_ilms())), [])  # type: List[str]
            ilm_sdc_files_arg = "-ilm_sdc_files [list {sdc_files}]".format(
                sdc_files=" ".join(ilm_sdcs))
        else:
            ilm_sdc_files_arg = ""
        append_mmmc("create_constraint_mode -name {name} {sdc_files_arg} {ilm_sdc_files_arg}".format(
            name=self.constraint_mode,
            sdc_files_arg=sdc_files_arg,
            ilm_sdc_files_arg=ilm_sdc_files_arg
        ))

        corners = self.get_mmmc_corners()  # type: List[MMMCCorner]
        # In parallel, create the delay corners
        if corners:
            setup_view_names = [] # type: List[str]
            hold_view_names = [] # type: List[str]
            extra_view_names = [] # type: List[str]
            for corner in corners:
                # Setting up views for all defined corner types: setup, hold, extra
                if corner.type is MMMCCornerType.Setup:
                    corner_name = "{n}.{t}".format(n=corner.name, t="setup")
                    setup_view_names.append("{n}_view".format(n=corner_name))
                elif corner.type is MMMCCornerType.Hold:
                    corner_name = "{n}.{t}".format(n=corner.name, t="hold")
                    hold_view_names.append("{n}_view".format(n=corner_name))
                elif corner.type is MMMCCornerType.Extra:
                    corner_name = "{n}.{t}".format(n=corner.name, t="extra")
                    extra_view_names.append("{n}_view".format(n=corner_name))
                else:
                    raise ValueError("Unsupported MMMCCornerType")

                # First, create Innovus library sets
                append_mmmc("create_library_set -name {name}_set -timing [list {list}]".format(
                    name=corner_name,
                    list=self.get_timing_libs(corner)
                ))
                # Skip opconds for now
                # Next, create Innovus timing conditions
                append_mmmc("create_timing_condition -name {name}_cond -library_sets [list {name}_set]".format(
                    name=corner_name
                ))
                # Next, create Innovus rc corners from qrc tech files
                append_mmmc("create_rc_corner -name {name}_rc -temperature {tempInCelsius} {qrc}".format(
                    name=corner_name,
                    tempInCelsius=str(corner.temp.value),
                    qrc="-qrc_tech {}".format(self.get_mmmc_qrc(corner)) if self.get_mmmc_qrc(corner) != '' else ''
                ))
                # Next, create an Innovus delay corner.
                append_mmmc(
                    "create_delay_corner -name {name}_delay -timing_condition {name}_cond -rc_corner {name}_rc".format(
                        name=corner_name
                    ))
                # Next, create the analysis views
                append_mmmc("create_analysis_view -name {name}_view -delay_corner {name}_delay -constraint_mode {constraint}".format(
                    name=corner_name,
                    constraint=self.constraint_mode
                ))

            # Finally, apply the analysis view.
            # TODO: should not need to analyze extra views as well. Defaulting to hold for now (min. runtime impact).
            # First extra view is assumed to be for dynamic and leakage power calculation.
            power_opts = ""
            if len(extra_view_names) > 0:
                power_opts = f"-dynamic {extra_view_names[0]} -leakage {extra_view_names[0]}"
            append_mmmc("set_analysis_view -setup {{ {setup_views} }} -hold {{ {hold_views} {extra_views} }} {power}".format(
                setup_views=" ".join(setup_view_names),
                hold_views=" ".join(hold_view_names),
                extra_views=" ".join(extra_view_names),
                power=power_opts
            ))
        else:
            # First, create an Innovus library set.
            library_set_name = "my_lib_set"
            append_mmmc("create_library_set -name {name} -timing [list {list}]".format(
                name=library_set_name,
                list=self.get_timing_libs()
            ))
            # Next, create an Innovus timing condition.
            timing_condition_name = "my_timing_condition"
            append_mmmc("create_timing_condition -name {name} -library_sets [list {list}]".format(
                name=timing_condition_name,
                list=library_set_name
            ))
            # extra junk: -opcond ...
            rc_corner_name = "rc_cond"
            append_mmmc("create_rc_corner -name {name} {qrc}".format(
                name=rc_corner_name,
                qrc="-qrc_tech {}".format(self.get_qrc_tech()) if self.get_qrc_tech() != '' else ''
            ))
            # Next, create an Innovus delay corner.
            delay_corner_name = "my_delay_corner"
            append_mmmc(
                "create_delay_corner -name {name} -timing_condition {timing_cond} -rc_corner {rc}".format(
                    name=delay_corner_name,
                    timing_cond=timing_condition_name,
                    rc=rc_corner_name
                ))
            # extra junk: -rc_corner my_rc_corner_maybe_worst
            # Next, create an Innovus analysis view.
            analysis_view_name = "my_view"
            append_mmmc("create_analysis_view -name {name} -delay_corner {corner} -constraint_mode {constraint}".format(
                name=analysis_view_name, corner=delay_corner_name, constraint=self.constraint_mode))
            # Finally, apply the analysis view.
            # TODO: introduce different views of setup/hold and true multi-corner
            append_mmmc("set_analysis_view -setup {{ {setup_view} }} -hold {{ {hold_view} }}".format(
                setup_view=analysis_view_name,
                hold_view=analysis_view_name
            ))

        return "\n".join(mmmc_output)

    def generate_dont_use_commands(self) -> List[str]:
        """
        Generate a list of dont_use commands for Cadence tools.
        """

        def map_cell(in_cell: str) -> str:
            # "*/" is needed for "get_db lib_cells <cell_expression>"
            if in_cell.startswith("*/"):
                mapped_cell = in_cell  # type: str
            else:
                mapped_cell = "*/" + in_cell

            # Check for cell existence first to avoid Genus erroring out.
            get_db_str = "[get_db lib_cells {mapped_cell}]".format(mapped_cell=mapped_cell)
            # Escaped version for puts.
            get_db_str_escaped = get_db_str.replace('[', '\[').replace(']', '\]')
            return """
puts "set_dont_use {get_db_str_escaped}"
if {{ {get_db_str} ne "" }} {{
    set_dont_use {get_db_str}
}} else {{
    puts "WARNING: cell {mapped_cell} was not found for set_dont_use"
}}
            """.format(get_db_str=get_db_str, get_db_str_escaped=get_db_str_escaped, mapped_cell=mapped_cell)

        return list(map(map_cell, self.get_dont_use_list()))

    def map_power_spec_name(self) -> str:
        """
        Return the CPF or UPF flag name for Cadence tools.
        """

        power_spec_type = str(self.get_setting("vlsi.inputs.power_spec_type"))  # type: str
        power_spec_arg = ""  # type: str
        if power_spec_type == "cpf":
            power_spec_arg = "cpf"
        elif power_spec_type == "upf":
            power_spec_arg = "1801"
        else:
            self.logger.error(
                "Invalid power specification type '{tpe}'; only 'cpf' or 'upf' supported".format(tpe=power_spec_type))
            return ""
        return power_spec_arg

    def create_power_spec(self) -> str:
        """
        Generate a power specification file for Cadence tools.
        """

        power_spec_type = str(self.get_setting("vlsi.inputs.power_spec_type"))  # type: str
        power_spec_contents = ""  # type: str
        power_spec_mode = str(self.get_setting("vlsi.inputs.power_spec_mode"))  # type: str
        if power_spec_mode == "empty":
            return ""
        elif power_spec_mode == "auto":
            if power_spec_type == "cpf":
                power_spec_contents = self.cpf_power_specification
            elif power_spec_type == "upf":
                power_spec_contents = self.upf_power_specification
        elif power_spec_mode == "manual":
            power_spec_contents = str(self.get_setting("vlsi.inputs.power_spec_contents"))
        else:
            self.logger.error("Invalid power specification mode '{mode}'; using 'empty'.".format(mode=power_spec_mode))
            return ""

        # Write the power spec contents to file and include it
        power_spec_file = os.path.join(self.run_dir, "power_spec.{tpe}".format(tpe=power_spec_type))
        self.write_contents_to_path(power_spec_contents, power_spec_file)

        return power_spec_file

    def generate_power_spec_commands(self) -> List[str]:
        """
        Generate commands to load a power specification for Cadence tools.
        """

        power_spec_file = self.create_power_spec()
        power_spec_arg = self.map_power_spec_name()

        return ["read_power_intent -{arg} {path}".format(arg=power_spec_arg, path=power_spec_file),
                "commit_power_intent"]

    def child_modules_tcl(self) -> str:
        """
        Dumps a list of child instance paths and their ilm directories.
        Should only be called when self.hierarchical_mode.is_nonleaf_hierarchical()
        """
        if self.get_setting("vlsi.inputs.hierarchical.config_source") != "manual":
            self.logger.warning('''
            Hierarchical write_regs requires having vlsi.inputs.hierarchical.manual_modules specified.
            You may have problems with register forcing in gate-level sim.
            ''')
            return '''
            set child_modules_ir "./find_child_modules.json"
            set child_modules_ir [open $child_modules_ir "w"]
            puts $child_modules_ir "\{\}"
            close $child_modules_ir
            '''
        else:
            # Write out the paths to all child find_regs_paths.json files
            child_modules = list(next(d for i,d in enumerate(self.get_setting("vlsi.inputs.hierarchical.manual_modules")) if self.top_module in d).values())[0]

            # Get all paths to the child module instances
            # For P&R, this only works in the flattened ILM state
            return '''
            set child_modules_ir "./find_child_modules.json"
            set child_modules_ir [open $child_modules_ir "w"]
            puts $child_modules_ir "\{{"

            set cells {{ {CELLS} }}
            set numcells [llength $cells]

            for {{set i 0}} {{$i < $numcells}} {{incr i}} {{
                set cell [lindex $cells $i]
                set inst_paths [get_db [get_db modules -if {{.name==$cell}}] .hinsts.name]
                set inst_paths [join $inst_paths "\\", \\""]
                if {{$i == $numcells - 1}} {{
                    puts $child_modules_ir "    \\"$cell\\": \\[\\"$inst_paths\\"\\]"
                }} else {{
                    puts $child_modules_ir "    \\"$cell\\": \\[\\"$inst_paths\\"\\],"
                }}
            }}

            puts $child_modules_ir "\}}"

            close $child_modules_ir
            '''.format(CELLS=" ".join(child_modules))

    def write_regs_tcl(self) -> str:
        return '''
        set write_cells_ir "./find_regs_cells.json"
        set write_cells_ir [open $write_cells_ir "w"]
        puts $write_cells_ir "\["

        set refs [get_db [get_db lib_cells -if .is_sequential==true] .base_name]

        set len [llength $refs]

        for {set i 0} {$i < [llength $refs]} {incr i} {
            if {$i == $len - 1} {
                puts $write_cells_ir "    \\"[lindex $refs $i]\\""
            } else {
                puts $write_cells_ir "    \\"[lindex $refs $i]\\","
            }
        }

        puts $write_cells_ir "\]"
        close $write_cells_ir
        set write_regs_ir "./find_regs_paths.json"
        set write_regs_ir [open $write_regs_ir "w"]
        puts $write_regs_ir "\["

        set regs [get_db [get_db [all_registers -edge_triggered -output_pins] -if .direction==out] .name]

        set len [llength $regs]

        for {set i 0} {$i < [llength $regs]} {incr i} {
            #regsub -all {/} [lindex $regs $i] . myreg
            set myreg [lindex $regs $i]
            if {$i == $len - 1} {
                puts $write_regs_ir "    \\"$myreg\\""
            } else {
                puts $write_regs_ir "    \\"$myreg\\","
            }
        }

        puts $write_regs_ir "\]"

        close $write_regs_ir
        '''

    def process_reg_paths(self, path: str) -> bool:
        # Post-process the all_regs list here to avoid having too much logic in TCL
        with open(path, "r+") as f:
            reg_paths = json.load(f)
            output_paths = [] #  type: List[Dict[str,str]]
            assert isinstance(reg_paths, List), "Output find_regs_paths.json should be a json list of strings"
            for i in range(len(reg_paths)):
                split = reg_paths[i].split("/")
                # If the net is part of a generate block, the generated names have a "." in them and the whole name
                # needs to be escaped.
                for index, node in enumerate(split):
                    if "." in node:
                        split[index] = "\\" + node + "\\"
                # If the last net is part of a bus, it needs to be escaped
                if split[-2][-1] == "]":
                    split[-2] = "\\" + split[-2]
                    reg_paths[i] = {"path" : '/'.join(split[0:len(split)-1]), "pin" : split[-1]}
                else:
                    reg_paths[i] = {"path" : '/'.join(split[0:len(split)-1]), "pin" : split[-1]}

            # For parent hierarchical modules, append all child instance regs
            if self.hierarchical_mode.is_nonleaf_hierarchical():
                with open(os.path.join(os.path.dirname(path), "find_child_modules.json"), "r") as cmf:
                    mod_paths = json.load(cmf)
                for mod_path in mod_paths.items():
                    ilm = next(i for i in self.get_input_ilms() if i.module == mod_path[0])  # type: ILMStruct
                    with open(os.path.join(os.path.dirname(ilm.dir), "find_regs_paths.json"), "r") as crf:
                        child_regs = json.load(crf)
                    for inst_path in mod_path[1]:
                        prefixed_regs = copy.deepcopy(child_regs)
                        for reg in prefixed_regs:
                            reg.update({'path': os.path.join(inst_path, reg['path'])})
                        reg_paths.extend(prefixed_regs)

            f.seek(0) # Move to beginning to rewrite file
            json.dump(reg_paths, f, indent=2) # Elide the truncation because we are always increasing file size
        return True
