#  hammer-vlsi plugin for Cadence Genus.
#
#  See LICENSE for licence details.

from hammer.vlsi import HammerTool, HammerToolStep, HammerToolHookAction, HierarchicalMode
from hammer.utils import VerilogUtils
from hammer.vlsi import HammerSynthesisTool, PlacementConstraintType
from hammer.logging import HammerVLSILogging
from hammer.vlsi import MMMCCornerType
import hammer.tech as hammer_tech

from typing import Dict, List, Any, Optional

from hammer.tech.specialcells import CellType

import os
from collections import Counter

from hammer.common.cadence import CadenceTool


class Genus(HammerSynthesisTool, CadenceTool):
    @property
    def post_synth_sdc(self) -> Optional[str]:
        # No post-synth SDC input for synthesis...
        return None

    def fill_outputs(self) -> bool:
        # Check that the regs paths were written properly if the write_regs step was run
        self.output_seq_cells = self.all_cells_path
        self.output_all_regs = self.all_regs_path
        if self.ran_write_regs:
            if not os.path.isfile(self.all_cells_path):
                raise ValueError("Output find_regs_cells.json %s not found" % (self.all_cells_path))

            if not os.path.isfile(self.all_regs_path):
                raise ValueError("Output find_regs_paths.json %s not found" % (self.all_regs_path))

            if not self.process_reg_paths(self.all_regs_path):
                self.logger.error("Failed to process all register paths")
        else:
            self.logger.info("Did not run write_regs")

        # Check that the synthesis outputs exist if the synthesis run was successful
        mapped_v = self.mapped_hier_v_path if self.hierarchical_mode.is_nonleaf_hierarchical() else self.mapped_v_path
        self.output_files = [mapped_v]
        self.output_sdc = self.mapped_sdc_path
        self.sdf_file = self.output_sdf_path
        if self.ran_write_outputs:
            if not os.path.isfile(mapped_v):
                raise ValueError("Output mapped verilog %s not found" % (mapped_v)) # better error?

            if not os.path.isfile(self.mapped_sdc_path):
                raise ValueError("Output SDC %s not found" % (self.mapped_sdc_path)) # better error?

            if not os.path.isfile(self.output_sdf_path):
                raise ValueError("Output SDF %s not found" % (self.output_sdf_path))
        else:
            self.logger.info("Did not run write_outputs")

        return True

    @property
    def env_vars(self) -> Dict[str, str]:
        new_dict = dict(super().env_vars)
        new_dict["GENUS_BIN"] = self.get_setting("synthesis.genus.genus_bin")
        return new_dict

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        # TODO(edwardw): find a "safer" way of passing around these settings keys.
        outputs["synthesis.outputs.sdc"] = self.output_sdc
        outputs["synthesis.outputs.seq_cells"] = self.output_seq_cells
        outputs["synthesis.outputs.all_regs"] = self.output_all_regs
        outputs["synthesis.outputs.sdf_file"] = self.output_sdf_path
        return outputs

    def tool_config_prefix(self) -> str:
        return "synthesis.genus"

    def get_tool_hooks(self) -> List[HammerToolHookAction]:
        return [self.make_persistent_hook(genus_global_settings)]

    @property
    def steps(self) -> List[HammerToolStep]:
        steps_methods = [
            self.init_environment,
            self.predict_floorplan,
            self.syn_generic,
            self.syn_map,
            self.add_tieoffs,
            self.write_regs,
            self.generate_reports,
            self.write_outputs,
            self.run_genus
        ]
        if self.get_setting("synthesis.inputs.retime_modules"):
            steps_methods.insert(1, self.retime_modules)
        return self.make_steps_from_methods(steps_methods)

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        assert super().do_pre_steps(first_step)
        # Reload from the last checkpoint if we're not starting over.
        if first_step != self.first_step:
            self.verbose_append("read_db pre_{step}".format(step=first_step.name))
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        assert super().do_between_steps(prev, next)
        # Write a checkpoint to disk.
        self.verbose_append("write_db -to_file pre_{step}".format(step=next.name))
        return True

    def do_post_steps(self) -> bool:
        assert super().do_post_steps()
        return True
    @property
    def mapped_v_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.v".format(self.top_module))

    @property
    def mapped_hier_v_path(self) -> str:
        if self.version() >= self.version_number("191"):
            return os.path.join(self.run_dir, "{}_noilm.mapped.v".format(self.top_module))
        else:
            return os.path.join(self.run_dir, "genus_invs_des/genus.v.gz")

    @property
    def mapped_sdc_path(self) -> str:
        return os.path.join(self.run_dir, "{}.mapped.sdc".format(self.top_module))

    @property
    def all_regs_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_paths.json")

    @property
    def all_cells_path(self) -> str:
        return os.path.join(self.run_dir, "find_regs_cells.json")

    @property
    def output_sdf_path(self) -> str:
        return os.path.join(self.run_dir, "{top}.mapped.sdf".format(top=self.top_module))

    @property
    def ran_write_regs(self) -> bool:
        """The write_regs step sets this to True if it was run."""
        return self.attr_getter("_ran_write_regs", False)

    @ran_write_regs.setter
    def ran_write_regs(self, val: bool) -> None:
        self.attr_setter("_ran_write_regs", val)

    @property
    def ran_write_outputs(self) -> bool:
        """The write_outputs step sets this to True if it was run."""
        return self.attr_getter("_ran_write_outputs", False)

    @ran_write_outputs.setter
    def ran_write_outputs(self, val: bool) -> None:
        self.attr_setter("_ran_write_outputs", val)

    def remove_hierarchical_submodules_from_file(self, path: str) -> str:
        """
        Remove any hierarchical submodules' implementation from the given Verilog source file in path, if it is present.
        If it is not, return the original path.
        :param path: Path to verilog source file
        :return: A path to a modified version of the original file without the given module, or the same path as before.
        """
        with open(path, "r") as f:
            source = f.read()
        submodules = list(map(lambda ilm: ilm.module, self.get_input_ilms()))

        touched = False

        for submodule in submodules:
            if VerilogUtils.contains_module(source, submodule):
                source = VerilogUtils.remove_module(source, submodule)
                touched = True

        if touched:
            # Write the modified input to a new file in run_dir.
            name, ext = os.path.splitext(os.path.basename(path))
            new_filename = str(name) + "_no_submodules" + str(ext)
            new_path = os.path.join(self.run_dir, new_filename)
            with open(new_path, "w") as f:
                f.write(source)
            return new_path
        else:
            return path

    def init_environment(self) -> bool:
        # Python sucks here for verbosity
        verbose_append = self.verbose_append

        # Clock gating setup
        if self.get_setting("synthesis.clock_gating_mode") == "auto":
            verbose_append("set_db lp_clock_gating_infer_enable  true")
            # Genus will create instances named CLKGATE_foo, CLKGATE_bar, etc.
            verbose_append("set_db lp_clock_gating_prefix  {CLKGATE}")
            verbose_append("set_db lp_insert_clock_gating  true")
            verbose_append("set_db lp_clock_gating_register_aware true")

        # Set up libraries.
        # Read timing libraries.
        mmmc_path = os.path.join(self.run_dir, "mmmc.tcl")
        self.write_contents_to_path(self.generate_mmmc_script(), mmmc_path)
        verbose_append("read_mmmc {mmmc_path}".format(mmmc_path=mmmc_path))

        if self.hierarchical_mode.is_nonleaf_hierarchical():
            # Read ILMs.
            for ilm in self.get_input_ilms():
                # Assumes that the ILM was created by Innovus (or at least the file/folder structure).
                verbose_append("read_ilm -basename {data_dir}/{module}_postRoute -module_name {module}".format(
                    data_dir=ilm.data_dir, module=ilm.module))

        # Read LEF layouts.
        lef_files = self.technology.read_libs([
            hammer_tech.filters.lef_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            ilm_lefs = list(map(lambda ilm: ilm.lef, self.get_input_ilms()))
            lef_files.extend(ilm_lefs)
        verbose_append("read_physical -lef {{ {files} }}".format(
            files=" ".join(lef_files)
        ))

        # Read qrc tech files for physical synthesis.
        qrc_files = self.technology.read_libs([
            hammer_tech.filters.qrc_tech_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)
        verbose_append("set_db qrc_tech_file {{ {files} }}".format(
            files=qrc_files[0]
        ))

        # Quit when ispatial is used with sky130
        if(not qrc_files and self.get_setting("synthesis.genus.phys_flow_effort").lower() == "high"):
            self.logger.warning("Sky130 does not support ISpatial due to missing of qrc tech files.")
            verbose_append("quit")

        # Load input files and check that they are all Verilog.
        if not self.check_input_files([".v", ".sv", "vh"]):
            return False
        # We are switching working directories and Genus still needs to find paths.
        abspath_input_files = list(map(lambda name: os.path.join(os.getcwd(), name), self.input_files))  # type: List[str]

        # If we are in hierarchical, we need to remove hierarchical sub-modules/sub-blocks.
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            abspath_input_files = list(map(self.remove_hierarchical_submodules_from_file, abspath_input_files))

        # Add any verilog_synth wrappers (which are needed in some technologies e.g. for SRAMs) which need to be
        # synthesized.
        abspath_input_files += self.technology.read_libs([
            hammer_tech.filters.verilog_synth_filter
        ], hammer_tech.HammerTechnologyUtils.to_plain_item)

        # Read the RTL.
        verbose_append("read_hdl -sv {{ {} }}".format(" ".join(abspath_input_files)))

        # Elaborate/parse the RTL.
        verbose_append("elaborate {}".format(self.top_module))
        # Preserve submodules
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            for ilm in self.get_input_ilms():
                verbose_append("set_db module:{top}/{mod} .preserve true".format(top=self.top_module, mod=ilm.module))
        verbose_append("init_design -top {}".format(self.top_module))

        # Report timing constraint issues
        verbose_append("report_timing -lint -verbose")

        # Setup power settings from cpf/upf
        # Difference from other tools: apply_power_intent after read
        power_cmds = self.generate_power_spec_commands()
        power_cmds.insert(1, "apply_power_intent -summary")
        for l in power_cmds:
            verbose_append(l)

        # Prevent floorplanning targets from getting flattened.
        # TODO: is there a way to track instance paths through the synthesis process?
        verbose_append("set_db root: .auto_ungroup none")

        # Set design effort.
        verbose_append(f"set_db phys_flow_effort {self.get_setting('synthesis.genus.phys_flow_effort')}")

        if self.get_setting("synthesis.genus.phys_flow_effort").lower() == "high":
            self.verbose_append("set_db opt_spatial_effort extreme")

        # Set "don't use" cells.
        for l in self.generate_dont_use_commands():
            self.append(l)

        return True

    def retime_modules(self) -> bool:
        retime_mods = self.get_setting("synthesis.inputs.retime_modules")

        if retime_mods:
            rt_tcl = (
                f"set rt_mods [get_designs \"{' '.join(retime_mods)}\"]\n" \
                "foreach rt_mod $rt_mods {\n" \
                "  set_db $rt_mod .retime true\n" \
                "}\n" \
                "set_db / .retime_verification_flow true"
            )
            self.append(rt_tcl)

        return True

    def dedup_ilms(self) -> None:
        """After DDI, syn_generic and syn_map will sometimes uniquify hierarchical ILMs,
        despite .preserve being set on the ILM modules. From observation, the uniquified
        modules are identical to the read-in ILM, so we can safely change_link to
        dedup.

        TODO: Correctly disable uniquification in Genus for hierarchical blocks"""

        if self.hierarchical_mode.is_nonleaf_hierarchical() and self.version() >= self.version_number("211"):
            pcs = list(filter(lambda c: c.type == PlacementConstraintType.Hierarchical, self.get_placement_constraints()))
            for pc in pcs:
                self.append("""
# Attempt to deuniquify hinst:{inst}, incase it was uniquified
set uniquified_name [get_db hinst:{inst} .module.name]
if {{ $uniquified_name ne \"{master}\" }} {{
    puts [format \"WARNING: instance hinst:{inst} was uniquified to be an instance of $uniquified_name, not {master}. Attempting to fix\"]
    change_link -copy_attributes -instances {{{inst}}} -design_name module:{top}/{master}
}}
set_db hinst:{inst} .preserve true
""".format(inst=pc.path, top=self.top_module, master=pc.master))

    def syn_generic(self) -> bool:
        # Add clock mapping flow if special cells are specified
        if self.version() >= self.version_number("211"):
            buffer_cells = self.technology.get_special_cell_by_type(CellType.CTSBuffer)
            if len(buffer_cells) > 0:
                self.append(f"set_db cts_buffer_cells {{{' '.join(buffer_cells[0].name)}}}")
            inverter_cells = self.technology.get_special_cell_by_type(CellType.CTSInverter)
            if len(inverter_cells) > 0:
                self.append(f"set_db cts_inverter_cells {{{' '.join(inverter_cells[0].name)}}}")
            gate_cells = self.technology.get_special_cell_by_type(CellType.CTSGate)
            if len(gate_cells) > 0:
                self.append(f"set_db cts_clock_gating_cells {{{' '.join(gate_cells[0].name)}}}")
            logic_cells = self.technology.get_special_cell_by_type(CellType.CTSLogic)
            if len(logic_cells) > 0:
                self.append(f"set_db cts_logic_cells {{{' '.join(logic_cells[0].name)}}}")
            # if any(c > 0 for c in [len(buffer_cells), len(inverter_cells), len(gate_cells), len(logic_cells)]):
            if len(inverter_cells) > 0 and len(logic_cells) > 0:
                # Clock mapping needs at least the attributes cts_inverter_cells and cts_logic_cells to be set
                self.append("set_db map_clock_tree true")

        if self.get_setting("synthesis.genus.phys_flow_effort").lower() == "none":
            self.verbose_append("syn_generic")
        else:
            self.verbose_append("syn_generic -physical")

        self.dedup_ilms()

        return True

    def syn_map(self) -> bool:
        if self.get_setting("synthesis.genus.phys_flow_effort").lower() == "none":
            self.verbose_append("syn_map")
        else:
            self.verbose_append("syn_map -physical")
            
        # High QoR optimization.
        if self.get_setting("synthesis.genus.phys_flow_effort").lower() == "medium":
            self.verbose_append("syn_opt")
        elif self.get_setting("synthesis.genus.phys_flow_effort").lower() == "high":
            self.verbose_append("syn_opt -spatial")

        # Need to suffix modules for hierarchical simulation if not top
        if self.hierarchical_mode not in [HierarchicalMode.Flat, HierarchicalMode.Top]:
            self.verbose_append("update_names -module -log hier_updated_names.log -suffix _{MODULE}".format(MODULE=self.top_module))

        self.dedup_ilms()

        return True
    
    def predict_floorplan(self) -> bool:
        if self.get_setting("synthesis.genus.phys_flow_effort").lower() == "none":
            self.verbose_append("set_db predict_floorplan_enable_during_generic false")
            self.verbose_append("set_db physical_force_predict_floorplan false")
        else:
            self.verbose_append("set_db invs_temp_dir temp_invs")
            self.verbose_append(f"set_db innovus_executable {self.get_setting('par.innovus.innovus_bin')}")
            self.verbose_append("set_db predict_floorplan_enable_during_generic true")
            self.verbose_append("set_db physical_force_predict_floorplan true")
            self.verbose_append(f"set_db predict_floorplan_use_innovus true")
            self.verbose_append("predict_floorplan")
        return True

    def add_tieoffs(self) -> bool:
        tie_hi_cells = self.technology.get_special_cell_by_type(CellType.TieHiCell)
        tie_lo_cells = self.technology.get_special_cell_by_type(CellType.TieLoCell)
        tie_hilo_cells = self.technology.get_special_cell_by_type(CellType.TieHiLoCell)

        if len(tie_hi_cells) != 1 or len (tie_lo_cells) != 1:
            if len(tie_hilo_cells) != 1:
                self.logger.warning("Hi and Lo tiecells are unspecified or improperly specified and will not be added during synthesis.")
                return True
            tie_hi_cells = tie_hilo_cells
            tie_lo_cells = tie_hilo_cells

        tie_hi_cell = tie_hi_cells[0].name[0]
        tie_lo_cell = tie_lo_cells[0].name[0]

        # Limit "no delay description exists" warnings
        self.verbose_append("set_db message:WSDF-201 .max_print 20")
        self.verbose_append("set_db use_tiehilo_for_const duplicate")

        # If MMMC corners specified, get the single lib cell for the active analysis view
        # Else, Genus will complain that multiple objects match for the cell name
        corners = self.get_mmmc_corners()
        if corners:
            self.verbose_append("set ACTIVE_SET [string map { .setup_view .setup_set .hold_view .hold_set .extra_view .extra_set } [get_db [get_analysis_views] .name]]")
            self.verbose_append("set HI_TIEOFF [get_db base_cell:{TIE_HI_CELL} .lib_cells -if {{ .library.library_set.name == $ACTIVE_SET }}]".format(TIE_HI_CELL=tie_hi_cell))
            self.verbose_append("set LO_TIEOFF [get_db base_cell:{TIE_LO_CELL} .lib_cells -if {{ .library.library_set.name == $ACTIVE_SET }}]".format(TIE_LO_CELL=tie_lo_cell))
            self.verbose_append("add_tieoffs -high $HI_TIEOFF -low $LO_TIEOFF -max_fanout 1 -verbose")
        else:
            self.verbose_append("add_tieoffs -high {HI_TIEOFF} -low {LO_TIEOFF} -max_fanout 1 -verbose".format(HI_TIEOFF=tie_hi_cell, LO_TIEOFF=tie_lo_cell))
        return True

    def generate_reports(self) -> bool:
        """Generate reports."""
        # TODO: extend report generation capabilities
        self.verbose_append("write_reports -directory reports -tag final")
        if self.get_setting("synthesis.genus.phys_flow_effort").lower() != "none":
            self.verbose_append("report_ple > reports/final_ple.rpt")
            #qor done by write_reports 

        # Write reports does not normally report unconstrained paths
        self.verbose_append("report_timing -unconstrained -max_paths 50 > reports/final_unconstrained.rpt")

        return True

    def write_regs(self) -> bool:
        """write regs info to be read in for simulation register forcing"""
        if self.hierarchical_mode.is_nonleaf_hierarchical():
            self.append(self.child_modules_tcl())
        self.append(self.write_regs_tcl())
        self.ran_write_regs = True
        return True

    def write_outputs(self) -> bool:
        verbose_append = self.verbose_append
        top = self.top_module

        verbose_append("write_hdl > {}".format(self.mapped_v_path))
        if self.hierarchical_mode.is_nonleaf_hierarchical() and self.version() >= self.version_number("191"):
            verbose_append("write_hdl -exclude_ilm > {}".format(self.mapped_hier_v_path))
        if self.version() >= self.version_number("221"):
            verbose_append("write_template -full -outfile {}.mapped.scr".format(top))
        else:
            verbose_append("write_script > {}.mapped.scr".format(top))
        corners = self.get_mmmc_corners()
        if corners:
            # First setup corner is default view
            view_name="{cname}.setup_view".format(cname=next(filter(lambda c: c.type is MMMCCornerType.Setup, corners)).name)
        else:
            # TODO: remove hardcoded my_view string
            view_name = "my_view"
        verbose_append("write_sdc -view {view} > {file}".format(view=view_name, file=self.mapped_sdc_path))

        verbose_append("write_sdf > {run_dir}/{top}.mapped.sdf".format(run_dir=self.run_dir, top=top))

        if self.version() >= self.version_number("221"):
            # New write_design is now meant for non-Cadence tools. write_db -common is now for Innovus-compatible databases.
            verbose_append("write_design -gzip_files {top}".format(top=top))
        else:
            # We just get "Cannot trace ILM directory. Data corrupted."
            # -hierarchical needs to be used for non-leaf modules
            is_hier = self.hierarchical_mode != HierarchicalMode.Leaf # self.hierarchical_mode != HierarchicalMode.Flat
            verbose_append("write_design -innovus {hier_flag} -gzip_files {top}".format(
                hier_flag="-hierarchical" if is_hier else "", top=top))

        if self.get_setting("synthesis.genus.phys_flow_effort").lower() != "none":
            verbose_append("write_db -common")
        self.ran_write_outputs = True

        return True
    
    def run_genus(self) -> bool:
        verbose_append = self.verbose_append

        """Close out the synthesis script and run Genus."""
        # Quit Genus.
        verbose_append("quit")

        # Create synthesis script.
        self.syn_tcl_filename = os.path.join(self.run_dir, "syn.tcl")
        self.write_contents_to_path("\n".join(self.output), self.syn_tcl_filename)

        # Build args.
        args = [
            self.get_setting("synthesis.genus.genus_bin"),
            "-f", self.syn_tcl_filename,
            "-no_gui"
        ]

        if bool(self.get_setting("synthesis.genus.generate_only")):
            self.logger.info("Generate-only mode: command-line is " + " ".join(args))
        else:
            # Temporarily disable colours/tag to make run output more readable.
            # TODO: think of a more elegant way to do this?
            HammerVLSILogging.enable_colour = False
            HammerVLSILogging.enable_tag = False
            self.run_executable(args, cwd=self.run_dir) # TODO: check for errors and deal with them
            HammerVLSILogging.enable_colour = True
            HammerVLSILogging.enable_tag = True

        return True

def genus_global_settings(ht: HammerTool) -> bool:
    """Settings that need to be reapplied at every tool invocation"""
    assert isinstance(ht, HammerSynthesisTool)
    assert isinstance(ht, CadenceTool)
    ht.create_enter_script()

    # Python sucks here for verbosity
    verbose_append = ht.verbose_append

    # Generic Settings
    verbose_append("set_db hdl_error_on_blackbox true")
    verbose_append("set_db max_cpus_per_server {}".format(ht.get_setting("vlsi.core.max_threads")))
    verbose_append("set_multi_cpu_usage -local_cpu {}".format(ht.get_setting("vlsi.core.max_threads")))
    verbose_append("set_db super_thread_debug_jobs true")
    verbose_append("set_db super_thread_debug_directory super_thread_debug")

    return True

tool = Genus
