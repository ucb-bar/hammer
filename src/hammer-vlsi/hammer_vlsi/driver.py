#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  driver.py
#  HammerDriver and related code.
#
#  See LICENSE for licence details.

from functools import reduce, partial
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any
from datetime import datetime
import os

from hammer_utils import *
import hammer_config
import hammer_tech
from hammer_tech import MacroSize
from .hammer_tool import HammerTool
from .hammer_vlsi_impl import HammerVLSISettings, HammerPlaceAndRouteTool, \
                              HammerSynthesisTool, HammerDRCTool, \
                              HammerLVSTool, HammerSRAMGeneratorTool, \
                              HammerPCBDeliverableTool, HammerSimTool, \
                              SRAMParameters, ILMStruct
from hammer_logging import HammerVLSIFileLogger, HammerVLSILogging, \
                           HammerVLSILoggingContext
from .submit_command import HammerSubmitCommand

__all__ = ['HammerDriverOptions', 'HammerDriver']

class StageInfo(NamedTuple("StageInfo", [
    (tool_name, str),
    (depends_on, List[str])
])):
    __slots__ = []

# Options for invoking the driver.
HammerDriverOptions = NamedTuple('HammerDriverOptions', [
    # List of environment config files in .json
    ('environment_configs', List[str]),
    # List of project config files in .json
    ('project_configs', List[str]),
    # Log file location.
    ('log_file', Optional[str]),
    # Folder for storing runtime files
    ('run_dir', Optional[str])
    # Folder for storing releases
    ('release_dir', Optional[str])
])

class HammerDriver:
    @staticmethod
    def get_default_driver_options() -> HammerDriverOptions:
        """Get default driver options."""
        return HammerDriverOptions(
            environment_configs=[],
            project_configs=[],
            log_file=None,
            run_dir=None,
            release_dir=None
        )


    def __init__(self, options: HammerDriverOptions) -> None:
        """
        set up logging, db (builtins->core->env->project->tech), run_dir,
        release_dir, designs, and stages
        :param options: Driver options.
        :param extra_project_config: An optional flattened config for the project. 
        """
        # Create global logging context (only write to file if user wants)
        if options.log_file is not None:
            file_logger = HammerVLSIFileLogger(options.log_file)
            HammerVLSILogging.add_callback(file_logger.callback)
        self.log = HammerVLSILogging.context()

        # Create a new hammer database.
        # type: hammer_config.HammerDatabase
        self.db = hammer_config.HammerDatabase() 

        self.log.info("Loading hammer-vlsi libraries and reading settings")

        # Load builtins and core into the database.
        HammerVLSISettings.load_builtins_and_core(self.db)

        # Read in the environment configs
        for config in options.environment_configs:
            if not os.path.exists(config):
                self.log.error("Env config %s does not exist!" % (config))
        self.db.update_environment(
            hammer_config.load_config_from_paths(
                options.environment_configs, strict=True))

        # read project configs (overwrites environment configs keys conflict)
        project_configs = hammer_config.load_config_from_paths(
            options.project_configs, strict=True)
        project_configs.append(extra_project_config)
        self.db.update_project(project_configs)

        # Get the technology and load technology settings.
        # tech is not optional
        self.tech = self._load_technology()

        # run_dir (chdir to rundir!)
        self.run_dir = self.db.get_setting("vlsi.core.run_dir")
        if options.run_dir is None:
            self.run_dir = options.run_dir
        assert os.path.isdir(self.run_dir), "failed to set up run_dir"
        self.run_dir = os.path.abspath(self.run_dir)
        if not os.path.isdir(self.run_dir)
            os.mkdir(self.run_dir)
        os.chdir(self.run_dir)

        # release_dir
        self.release_dir = self.db.get_setting("vlsi.core.release_dir")
        if options.release_dir is None:
            self.release_dir = options.release_dir
        assert os.path.isdir(self.release_dir), "failed to set up release_dir"
        self.release_dir = os.path.abspath(self.release_dir)

        # each design now has a personalized tech/database!
        # no more need for hierarchical-configs
        self.designs = self._load_designs()

        # stage abstraction allows multiple explicit configurations for a tool
        self.stages = {
            "sram_gen": StageInfo("sram_gen", []),
            "sim_rtl":  StageInfo("sim",      [])
            "syn":      StageInfo("syn",      [])
            "sim_syn":  StageInfo("sim_syn",  ["syn"])
            "par":      StageInfo("par",      ["syn"])
            "sim_pnr":  StageInfo("sim_pnr",  ["pnr"])
            "drc":      StageInfo("drc",      ["pnr"])
            "lvs":      StageInfo("lvs",      ["pnr"])
        }

    #-------------------------------------------------------------------------
    def get_designs(self) -> List[HammerDeisgn]:
        return self.designs.values()

    def get_design(self, name:str) -> HammerDeisgn:
        if name is not in self.designs:
            raise Exception("{} is not a valid design".format(name))
        return self.designs[name]

    def get_top_design(self) -> HammerDesign:
        top_designs = list(filter(lambda x: x.is_top(), 
            driver.get_designs()))
        if len(top_designs) != 1:
            raise Exception("{} top deisigns found. check your project.yml"
                .format(len(top_designs)))
        return top_designs[0]

    #-------------------------------------------------------------------------
    def get_supported_stages(self) -> List[str]:
        return self.stages.keys()

    def stage_name_to_tool_name(self, stage_name: str) -> str:
        stage_info = self.stages[stage]
        if stage_info is None:
            raise Exception("invalid design stage {}".format(stage_name))
        return stage_info.tool_name

    #-------------------------------------------------------------------------
    def _load_technology(self, cache_dir: str = "") -> HammerTechnology:
        tech_str = self.db.get_setting("vlsi.core.technology")

        if cache_dir == "":
            cache_dir = os.path.join(self.run_dir, "tech-%s-cache" % tech_str)

        tech_paths = list(self.db.get_setting("vlsi.core.technology_path"))

        self.log.info("Loading technology '{0}'".format(tech_str))
        tech_opt = None  # type: Optional[hammer_tech.HammerTechnology]
        for base_path in tech_paths:
            path = os.path.join(base_path, tech_str)
            tech_opt = hammer_tech.HammerTechnology.load_from_dir(tech_str, path)
            if tech_opt is not None:
                break
        if tech_opt is None:
            raise Exception("Technology {0} not found or missing .tech.[json/yml]!"
                .format(tech_str))

        # type: hammer_tech.HammerTechnology
        tech = tech_opt  
        # Update database as soon as possible since e.g. 
        # extract_technology_files could use those settings
        self.db.update_technology(tech.get_config())
        tech.logger = self.log.context("tech")
        tech.set_database(self.db)
        tech.cache_dir = cache_dir
        tech.extract_technology_files()
        return tech

    #-------------------------------------------------------------------------
    def _load_designs(self) -> Dict[str, HammerDesign]:
        """
        This should be called by the constructor of HammerDriver, so that all
        user references are to the HammerDriver that is fully setup/loaded
        """
        names = self.db.get_setting_subkeys("designs")
        designs = {}
        if len(names) == 0: 
            raise Exception("no designs found at designs.<design-name>")
        # create a temp hash with the new hammer databases
        for name in names:
            db = self.db.clone()
            db.update_project(db.project + \
                [db.get_unprefixed_settings("designs.{}".format(name))])
            db.set_setting("design.name", name)
            tech = self.tech.clone(db=db)
            db.update_technology(tech.get_config())
            designs[name] = HammerDesign(name=name, db=db, tech=tech)

        # populate the parent/child settings for each design
        for name,design in designs.items():
            for sub_name in design.db.get_setting("design.children"):
                if sub_name in designs:
                    sub_design = designs[sub_name]
                    design.add_child(sub_design)
                else:
                    raise Exception("design {} has invalid sub-design {}".format(
                        name, sub_name)

        return designs

    #-------------------------------------------------------------------------
    def has_valid_release(self, tool:HammerTool) -> bool:
        """true if the tool has dropped a 'valid' file in release dir"""
        return os.path.isfile("{}/valid".format(self.release_dir))

    #-------------------------------------------------------------------------
    def has_stale_release(self, tool:HammerTool, other: HammerTool) -> bool:
        """
        only returns false if both releases exist, and other release is older
        than tool release.
        """
        tool_valid_file = "{}/valid".format(tool.release_dir)
        other_valid_file = "{}/valid".format(other.release_dir)
        with open(tool_valid_file, "r") as f:
            try:
                tool_ts = strptime(f.readline(), "%Y-m-d %H:%m:%S.%f")
            except:
                tool_ts = None

        with open(other_valid_file, "r") as f:
            try:
                other_ts = strptime(f.readline(), "%Y-m-d %H:%m:%S.%f")
            except:
                other_ts = None

        if (tool_ts is None) or (other_ts is None) or (tool_ts < other_ts):
            return True
        return False

    #-------------------------------------------------------------------------
    def setup_tool_for_stage(self, stage:str, design:HammerDesign) -> HammerTool:
        """sets up the new tool for the given design stage. """
        tool_name = self.stage_name_to_tool_name(stage)
        if tool_name is None:
            raise Exception("invalid design stage {}".format(stage))

        design = design.clone()
        db = design.db
        tech = design.tech
        # now the design.tool and design.name have booth been set.
        db.set_setting("design.stage", stage)
        db.set_setting("design.tool", tool_name)

        #--------------------------------------------------------------------
        tool_name = db.get_setting("vlsi.core.{}_tool".format(tool_name))
        tool_path = db.get_setting("vlsi.core.{}_tool_path".format(tool_name))
        tool_get = load_tool(path=path, tool_name=tool_name)

        sys.path.insert(0, tool_path)
        try:
            if tool_name in sys.modules:
                del sys.modules[tool_name]
            mod = importlib.import_module(tool_name)
        except ImportError:
            raise ValueError("No such tool " + tool_name)
        sys.path.pop(0)
        try:
            tool_class = getattr(mod, "tool")
        except AttributeError:
            raise ValueError("No such tool " + tool_name + \
                ", or tool does not follow the hammer-vlsi tool library format")

        if not issubclass(tool_class, HammerTool):
            raise ValueError("Tool must be a HammerTool")

        tool = tool_class()

        tool.name           = tool_name
        tool.stage          = stage
        tool.top_module     = tool.design.name  # for legacy code. TODO: remove
        tool.db             = design.db
        tool.tech           = design.tech
        tool.tool_dir       = os.path.dirname(os.path.abspath(mod.__file__))
        tool.run_dir        = db.get_setting("design.run_dir")
        tool.release_dir    = db.get_setting("design.release_dir")
        tool.logger         = self.log.context(tool_name)
        tool.submit_command = HammerSubmitCommand.get(tool_name, db)

        # tool-specific configuration
        getattr(self, "_finish_{}_setup".format(stage))(tool)

        # finally, update the tool's db with the tool configs
        tool.db.update_tools(tool.get_config())

        # save the loaded to into the design
        design.set_tool(stage, tool)
        return tool

    #------------------------------------------------------------------------
    def _finish_sram_gen_setup(self, tool: HammerSRAMGeneratorTool) -> None:
        # TODO: make stale-ness dependent on an 'rtl-prep' step or gen_sram
        # setup stale/released flags
        tool.has_stale_release = False
        tool.has_valid_release = self.has_valid_release(tool)

        tool.input_parameters = \
            list(map(lambda p: SRAMParameters.from_setting(p),
                tool.db.get_setting("vlsi.inputs.sram_parameters",nullvalue=[])
        # TODO: add rest of sram_gen.* settings from db

        if len(tool.input_files) == 0:
            tool.error("no input files")

    #------------------------------------------------------------------------
    def _finish_syn_setup(self, tool:HammerSynthesisTool) -> None:
        # TODO: make stale-ness dependent on an 'rtl-prep' step or gen_sram
        # setup stale/released flags
        tool.has_stale_release = False
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.input_files  = tool.db.get_setting("syn.inputs.input_files")
        tool.rtl_filelist = tool.db.get_setting("syn.inputs.rtl_filelist")
        tool.is_physical  = tool.db.get_setting("syn.physical")
        # TODO: add rest of syn.* settings from db

        if (len(tool.input_files) == 0) and (len(tool.rtl_filelist) == 0):
            tool.error("no input files")

    #------------------------------------------------------------------------
    def _finish_pnr_setup(self, tool:HammerPlaceAndRouteTool) -> None:
        # get dependency outputs
        syn_tool        = self.get_tool("syn")
        syn_outputs     = syn_tool.get_release_files()
        syn_netlist     = syn_outputs["netlist"]
        syn_output_sdc  = syn_outputs["sdc"]

        # setup stale/released flags
        tool.has_stale_release = self.has_stale_release(tool, syn_tool)
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.input_files = syn_netlist
        tool.post_synth_sdc = syn_sdc
        # TODO: add rest of pnr.* settings from db

        if len(tool.input_files) == 0:
            tool.error("no input files")

    #------------------------------------------------------------------------
    def _finish_drc_setup(self, tool: HammerDRCTool) -> None:
        # get dependency outputs
        pnr_tool    = self.get_tool("pnr")
        pnr_outputs = pnr_tool.get_release_files()
        pnr_gds     = pnr_outputs["gds"]

        # setup stale/released flags
        tool.has_stale_release = self.has_stale_release(tool, pnr_tool)
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.layout_file = pnr_gds
        # TODO: add rest of drc.* settings from db

        if len(tool.layout_file) == 0:
            tool.error("no layout file")

    #------------------------------------------------------------------------
    def _finish_lvs_setup(self, tool: HammerLVSTool) -> None:
        # get dependency outputs
        pnr_tool    = self.get_tool("pnr")
        pnr_outputs = pnr_tool.get_release_files()
        pnr_gds     = pnr_outputs["gds"]
        pnr_netlist = pnr_outputs["netlist"]
        pnr_hcells  = pnr_outputs["hcells_list"]
        pnr_ilms    = pnr_outputs["ilms"]

        # setup stale/released flags
        tool.has_stale_release = self.has_stale_release(tool, pnr_tool)
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.layout_file        = pnr_gds
        tool.schematic_files    = [pnr_netlist]
        tool.hcells_list        = pnr_hcells
        tool.ilms               = list(map(lambda x: ILMStruct.from_setting(x), 
                                    pnr_ilms))
        # TODO: add rest of lvs.* settings from db

        if len(tool.layout_file) == 0:
            tool.error("no layout file")
        if len(tool.schematic_files) == 0:
            tool.error("no schematic file")

    #------------------------------------------------------------------------
    def _finish_sim_setup(self, tool: HammerSimTool) -> None:
        # TODO: make stale-ness dependent on an 'rtl-prep' step or gen_sram
        # setup stale/released flags
        tool.has_stale_release = False
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.input_files = tool.db.get_setting("sim.inputs.design_files") +\
                           tool.db.get_setting("sim.inputs.sim_files")
        # TODO: add rest of sim.* settings from db

        if len(tool.input_files) == 0:
            tool.error("no input files")

    #------------------------------------------------------------------------
    def _finish_sim_syn_setup(self, tool: HammerSimTool) -> None:
        """sim_syn-specific configuration. throws error on exception"""
        # get dependency outputs
        syn_tool        = self.get_tool("syn")
        syn_release     = syn_tool.get_release_files()
        syn_netlist     = syn_release["netlist"]
        syn_sdf         = syn_release["sdf"]
        syn_regs_json   = tool.read_regs_json(syn_release["regs_json"])
        syn_all_regs    = syn_regs_json["all_regs"]
        syn_seq_cells   = syn_regs_json["seq_cells"]

        # setup stale/released flags
        tool.has_stale_release = self.has_stale_release(tool, syn_tool)
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.input_files    = [syn_netlist] +\
                              tool.db.get_setting("sim.inputs.sim_files")
        tool.sdf_file       = syn_sdf
        tool.all_regs       = syn_all_regs
        tool.seq_cells      = syn_seq_cells
        # TODO: add rest of sim.* settings from db

        if len(tool.input_files) == 0:
            tool.error("no input files")

    #------------------------------------------------------------------------
    def _finish_sim_pnr_setup(self, tool: HammerSimTool) -> None:
        """sim_pnr-specific configuration. throws error on exception"""
        # get dependency outputs
        pnr_tool        = self.get_tool("pnr")
        pnr_release     = pnr_tool.get_release_files()
        pnr_netlist     = pnr_release["netlist"]
        pnr_sdf         = pnr_release["sdf"]
        pnr_regs_json   = tool.read_regs_json(pnr_release["regs_json"])
        pnr_all_regs    = pnr_regs_json["all_regs"]
        pnr_seq_cells   = pnr_regs_json["seq_cells"]

        # setup stale/released flags
        tool.has_stale_release = self.has_stale_release(tool, pnr_tool)
        tool.has_valid_release = self.has_valid_release(tool)

        # setup inputs
        tool.input_files    = [pnr_netlist] +\
                              tool.db.get_setting("sim.inputs.sim_files")
        tool.sdf_file       = pnr_sdf
        tool.all_regs       = pnr_all_regs
        tool.seq_cells      = pnr_seq_cells
        # TODO: add rest of sim.* settings from db

        if len(tool.input_files) == 0:
            tool.error("no input files")

    #------------------------------------------------------------------------
    def _finish_pcb_setup(self, tool: HammerPCBDeliverableTool) -> None:
        """pcb-specific configuration. throws error on exception"""
        # TODO: make stale-ness dependent on an 'rtl-prep' step or gen_sram
        # setup stale/released flags
        tool.has_stale_release = False
        tool.has_valid_release = self.has_valid_release(tool)

