#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  driver.py
#  HammerDriver and related code.
#
#  See LICENSE for licence details.

from functools import reduce, partial
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

import datetime
import os

from hammer_utils import *

import hammer_config
import hammer_tech
from hammer_tech import MacroSize
from .hammer_tool import HammerTool
from .hooks import HammerToolHookAction
from .hammer_vlsi_impl import HammerVLSISettings, HammerPlaceAndRouteTool, HammerSynthesisTool, \
    HammerSignoffTool, HammerDRCTool, HammerLVSTool, HammerSRAMGeneratorTool, HammerPCBDeliverableTool, HammerSimTool, \
    HierarchicalMode, load_tool, PlacementConstraint, SRAMParameters, ILMStruct
from hammer_logging import HammerVLSIFileLogger, HammerVLSILogging, HammerVLSILoggingContext
from .submit_command import HammerSubmitCommand

__all__ = ['HammerDriverOptions', 'HammerDriver']

# Options for invoking the driver.
HammerDriverOptions = NamedTuple('HammerDriverOptions', [
    # List of environment config files in .json
    ('environment_configs', List[str]),
    # List of project config files in .json or .yml
    ('project_configs', List[str]),
    # Log file location.
    ('log_file', str),
    # Folder for storing runtime files / CAD junk.
    ('obj_dir', str)
])


class HammerDriver:
    @staticmethod
    def get_default_driver_options() -> HammerDriverOptions:
        """Get default driver options."""
        return HammerDriverOptions(
            environment_configs=[],
            project_configs=[],
            log_file=datetime.datetime.now().strftime("hammer-vlsi-%Y%m%d-%H%M%S.log"),
            obj_dir=os.path.realpath(HammerVLSISettings.hammer_vlsi_path)
        )

    def __init__(self, options: HammerDriverOptions, extra_project_config: dict = {}) -> None:
        """
        Create a hammer-vlsi driver, which is a higher level convenience function
        for quickly using hammer-vlsi. It imports and uses the hammer-vlsi blocks.

        Set up logging, databases, context, etc.

        :param options: Driver options.
        :param extra_project_config: An extra flattened config for the project. Optional.
        """

        # Create global logging context.
        file_logger = HammerVLSIFileLogger(options.log_file)
        HammerVLSILogging.add_callback(file_logger.callback)
        self.log = HammerVLSILogging.context()  # type: HammerVLSILoggingContext

        # Create a new hammer database.
        self.database = hammer_config.HammerDatabase()  # type: hammer_config.HammerDatabase

        self.log.info("Loading hammer-vlsi libraries and reading settings")

        # Store the run dir (this should already be canonicalized by the CLI driver).
        self.obj_dir = options.obj_dir  # type: str

        # Also store the options
        self.options = options

        # Load builtins and core into the database.
        HammerVLSISettings.load_builtins_and_core(self.database)

        # Read in the environment config for paths to CAD tools, etc.
        for config in options.environment_configs:
            if not os.path.exists(config):
                self.log.error("Environment config %s does not exist!" % (config))
        self.database.update_environment(hammer_config.load_config_from_paths(options.environment_configs, strict=True))

        # Read in the project config to find the syn, par, and tech.
        project_configs = hammer_config.load_config_from_paths(options.project_configs, strict=True)
        project_configs.append(extra_project_config)
        self.project_configs = []  # type: List[dict]
        self.update_project_configs(project_configs)

        # Get the technology and load technology settings.
        self.tech = None  # type: Optional[hammer_tech.HammerTechnology]
        self.load_technology()

        # Keep track of what the synthesis and par configs are since
        # update_tools() just takes a whole list.
        self.tool_configs = {}  # type: Dict[str, List[dict]]

        # Initialize tool fields.
        self.syn_tool = None  # type: Optional[HammerSynthesisTool]
        self.par_tool = None  # type: Optional[HammerPlaceAndRouteTool]
        self.drc_tool = None  # type: Optional[HammerDRCTool]
        self.lvs_tool = None  # type: Optional[HammerLVSTool]
        self.sram_generator_tool = None  # type: Optional[HammerSRAMGeneratorTool]
        self.sim_tool = None  # type: Optional[HammerSimTool]

        # Initialize tool hooks. Used to specify resume/pause hooks after custom hooks have been registered.
        self.post_custom_syn_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_par_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_drc_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_lvs_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_sram_generator_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_sim_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_pcb_tool_hooks = []  # type: List[HammerToolHookAction]

    @property
    def project_config(self) -> dict:
        return hammer_config.combine_configs(self.project_configs)

    def update_project_configs(self, project_configs: List[dict]) -> None:
        """
        Update the project configs in the driver and database.
        """
        self.project_configs = project_configs
        self.database.update_project(self.project_configs)

    def load_technology(self, cache_dir: str = "") -> None:
        tech_str = self.database.get_setting("vlsi.core.technology")  # type: str

        if cache_dir == "":
            cache_dir = os.path.join(self.obj_dir, "tech-%s-cache" % tech_str)

        tech_paths = list(self.database.get_setting("vlsi.core.technology_path"))  # type: List[str]

        self.log.info("Loading technology '{0}'".format(tech_str))
        tech_opt = None  # type: Optional[hammer_tech.HammerTechnology]
        for base_path in tech_paths:
            sys.path.append(base_path)
            path = os.path.join(base_path, tech_str)
            tech_opt = hammer_tech.HammerTechnology.load_from_dir(tech_str, path)
            if tech_opt is not None:
                break
        if tech_opt is None:
            self.log.fatal("Technology {0} not found or missing .tech.[json/yml]!".format(tech_str))
            return
        else:
            tech = tech_opt  # type: hammer_tech.HammerTechnology
        # Update database as soon as possible since e.g. extract_technology_files could use those settings
        self.database.update_technology(tech.get_config())
        tech.logger = self.log.context("tech")
        tech.set_database(self.database)
        tech.cache_dir = cache_dir
        tech.extract_technology_files()

        self.tech = tech

    def update_tool_configs(self) -> None:
        """
        Calls self.database.update_tools with self.tool_configs as a list.
        """
        tools = reduce(lambda a, b: a + b, list(self.tool_configs.values()))
        self.database.update_tools(tools)

    def instantiate_tool_from_config(self, tool_type: str,
                                     required_type: Optional[type] = None) -> Optional[Tuple[HammerTool, str]]:
        """
        Create a new instance of the given tool using information from the config.
        :param tool_type: Tool type. e.g. if "par", then this will look in
                          vlsi.core.par_tool/vlsi.core.par_tool_path.
        :param required_type: (optional) Check that the instantiated tool is the given type.
        :return: Tuple of (tool instance, tool name) or
                 None if an error occurred.
        """
        # Find the tool and read in their configs.
        tool_name = self.database.get_setting("vlsi.core.{tool_type}_tool".format(tool_type=tool_type))
        tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.{tool_type}_tool_path".format(tool_type=tool_type)),
            tool_name=tool_name
        )
        if required_type is not None:
            if not isinstance(tool_get, required_type):
                self.log.error("{tool_type} tool's type is incorrect: got {got}".format(tool_type=tool_type,
                                                                                        got=str(type(tool_get))))
                return None
        return tool_get, tool_name

    def set_up_synthesis_tool(self, syn_tool: HammerSynthesisTool,
                              name: str, run_dir: str = "") -> bool:
        """
        Set up and store the given synthesis tool instance for use in this
        driver.
        :param syn_tool: Tool instance.
        :param name: Short name (e.g. "yosys") of the tool instance. Typically
                     obtained from the database.
        :param run_dir: Directory to use for the tool run_dir. Defaults to the
                        run_dir passed in the HammerDriver constructor.
        :return: True if setup was successful.
        """
        if self.tech is None:
            self.log.error("Must load technology before loading synthesis tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "syn-rundir")

        # TODO: generate this automatically
        syn_tool.name = name
        syn_tool.logger = self.log.context("synthesis")
        syn_tool.technology = self.tech
        syn_tool.set_database(self.database)
        syn_tool.run_dir = run_dir
        syn_tool.hierarchical_mode = HierarchicalMode.from_str(
            self.database.get_setting("vlsi.inputs.hierarchical.mode"))
        syn_tool.input_files = self.database.get_setting("synthesis.inputs.input_files")
        syn_tool.top_module = self.database.get_setting("synthesis.inputs.top_module", nullvalue="")
        syn_tool.submit_command = HammerSubmitCommand.get("synthesis", self.database)
        syn_tool.output_all_regs = []
        syn_tool.output_seq_cells = []

        # TODO: automate this based on the definitions
        missing_inputs = False
        if syn_tool.top_module == "":
            self.log.error("Top module not specified for synthesis")
            missing_inputs = True
        if len(syn_tool.input_files) == 0:
            self.log.error("No input files specified for synthesis")
            missing_inputs = True
        if missing_inputs:
            return False

        self.syn_tool = syn_tool
        self.tool_configs["synthesis"] = syn_tool.get_config()
        self.update_tool_configs()
        return True

    def set_up_par_tool(self, par_tool: HammerPlaceAndRouteTool,
                        name: str, run_dir: str = "") -> bool:
        """
        Set up and store the given place-and-route tool instance for use in this
        driver.
        :param par_tool: Tool instance.
        :param name: Short name (e.g. "yosys") of the tool instance. Typically
                     obtained from the database.
        :param run_dir: Directory to use for the tool run_dir. Defaults to the
                        run_dir passed in the HammerDriver constructor.
        :return: True if setup was successful.
        """
        if self.tech is None:
            self.log.error("Must load technology before loading par tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "par-rundir")

        par_tool.name = name
        par_tool.logger = self.log.context("par")
        par_tool.technology = self.tech
        par_tool.set_database(self.database)
        par_tool.run_dir = run_dir
        par_tool.hierarchical_mode = HierarchicalMode.from_str(
            self.database.get_setting("vlsi.inputs.hierarchical.mode"))
        par_tool.submit_command = HammerSubmitCommand.get("par", self.database)

        missing_inputs = False

        # TODO: automate this based on the definitions
        par_tool.input_files = list(self.database.get_setting("par.inputs.input_files"))
        par_tool.top_module = self.database.get_setting("par.inputs.top_module", nullvalue="")
        par_tool.post_synth_sdc = self.database.get_setting("par.inputs.post_synth_sdc", nullvalue="")
        par_tool.output_all_regs = []
        par_tool.output_seq_cells = []


        if len(par_tool.input_files) == 0:
            self.log.error("No input files specified for par")
            missing_inputs = True
        if par_tool.top_module == "":
            self.log.error("No top module specified for par")
            missing_inputs = True
        if missing_inputs:
            return False

        self.par_tool = par_tool
        self.tool_configs["par"] = par_tool.get_config()
        self.update_tool_configs()
        return True

    def load_synthesis_tool(self, run_dir: str = "") -> bool:
        """
        Load the synthesis tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if synthesis tool loading was successful, False otherwise.
        """
        config_result = self.instantiate_tool_from_config("synthesis", HammerSynthesisTool)
        if config_result is None:
            return False
        else:
            (syn_tool, name) = config_result
            assert isinstance(syn_tool, HammerSynthesisTool)
            return self.set_up_synthesis_tool(syn_tool, name, run_dir)

    def load_par_tool(self, run_dir: str = "") -> bool:
        """
        Load the place and route tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if successful, false otherwise
        """
        config_result = self.instantiate_tool_from_config("par", HammerPlaceAndRouteTool)
        if config_result is None:
            return False
        else:
            (par_tool, name) = config_result
            assert isinstance(par_tool, HammerPlaceAndRouteTool)
            return self.set_up_par_tool(par_tool, name, run_dir)

    def load_drc_tool(self, run_dir: str = "") -> bool:
        """
        Loads a DRC tool on a given database

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if DRC tool loading was successful, False otherwise.
        """
        if self.tech is None:
            self.log.error("Must load technology before loading DRC tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "drc-rundir")

        drc_tool_name = self.database.get_setting("vlsi.core.drc_tool")
        drc_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.drc_tool_path"),
            tool_name=drc_tool_name
        )
        assert isinstance(drc_tool_get, HammerDRCTool), "DRC tool must be a HammerDRCTool"
        drc_tool = drc_tool_get  # type: HammerDRCTool
        drc_tool.name = drc_tool_name
        drc_tool.logger = self.log.context("drc")
        drc_tool.technology = self.tech
        drc_tool.set_database(self.database)
        drc_tool.submit_command = HammerSubmitCommand.get("drc", self.database)
        drc_tool.run_dir = run_dir
        # TODO hierarchical

        drc_tool.top_module = self.database.get_setting("drc.inputs.top_module", nullvalue="")
        drc_tool.layout_file = self.database.get_setting("drc.inputs.layout_file", nullvalue="")
        missing_inputs = False
        if drc_tool.top_module == "":
            self.log.error("Top module not specified for DRC")
            missing_inputs = True
        if drc_tool.layout_file is None:
            self.log.error("No layout file specified for DRC")
            missing_inputs = True
        if missing_inputs:
            return False

        self.drc_tool = drc_tool

        self.tool_configs["drc"] = drc_tool.get_config()
        self.update_tool_configs()
        return True

    def load_lvs_tool(self, run_dir: str = "") -> bool:
        """
        Loads an LVS tool on a given database

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if LVS tool loading was successful, False otherwise.
        """
        if self.tech is None:
            self.log.error("Must load technology before loading LVS tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "lvs-rundir")

        lvs_tool_name = self.database.get_setting("vlsi.core.lvs_tool")
        lvs_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.lvs_tool_path"),
            tool_name=lvs_tool_name
        )
        assert isinstance(lvs_tool_get, HammerLVSTool), "LVS tool must be a HammerLVSTool"
        lvs_tool = lvs_tool_get  # type: HammerLVSTool
        lvs_tool.name = lvs_tool_name
        lvs_tool.logger = self.log.context("lvs")
        lvs_tool.technology = self.tech
        lvs_tool.set_database(self.database)
        lvs_tool.submit_command = HammerSubmitCommand.get("lvs", self.database)
        lvs_tool.run_dir = run_dir

        lvs_tool.schematic_files = self.database.get_setting("lvs.inputs.schematic_files", nullvalue=[])
        lvs_tool.layout_file = self.database.get_setting("lvs.inputs.layout_file", nullvalue="")
        lvs_tool.top_module = self.database.get_setting("lvs.inputs.top_module", nullvalue="")
        lvs_tool.hcells_list = self.database.get_setting("lvs.inputs.hcells_list", nullvalue=[])
        lvs_tool.ilms = list(map(lambda x: ILMStruct.from_setting(x), self.database.get_setting("lvs.inputs.ilms", nullvalue=[])))
        missing_inputs = False
        if lvs_tool.top_module == "":
            self.log.error("Top module not specified for LVS")
            missing_inputs = True
        if lvs_tool.layout_file is None:
            self.log.error("No layout file specified for LVS")
            missing_inputs = True
        if len(lvs_tool.schematic_files) == 0:
            self.log.error("No schematic files specified for LVS")
            missing_inputs = True
        if missing_inputs:
            return False

        self.lvs_tool = lvs_tool

        self.tool_configs["lvs"] = lvs_tool.get_config()
        self.update_tool_configs()
        return True

    def load_sram_generator_tool(self, run_dir: str = "") -> bool:
        """
        Loads an SRAM Generator tool on a given database

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if SRAM Generator tool loading was successful, False otherwise.
        """
        if self.tech is None:
            self.log.error("Must load technology before loading SRAM Generator tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "sram_generator-rundir")

        sram_generator_tool_name = self.database.get_setting("vlsi.core.sram_generator_tool")
        sram_generator_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.sram_generator_tool_path"),
            tool_name=sram_generator_tool_name
        )
        assert isinstance(sram_generator_tool_get, HammerSRAMGeneratorTool), "SRAM Generator tool must be a HammerSRAMGeneratorTool"
        sram_generator_tool = sram_generator_tool_get  # type: HammerSRAMGeneratorTool
        sram_generator_tool.name = sram_generator_tool_name
        sram_generator_tool.logger = self.log.context("sram_generator")
        sram_generator_tool.technology = self.tech
        sram_generator_tool.set_database(self.database)
        sram_generator_tool.submit_command = HammerSubmitCommand.get("sram_generator", self.database)
        sram_generator_tool.run_dir = run_dir
        raw_params = self.database.get_setting("vlsi.inputs.sram_parameters",nullvalue=[])
        sram_params = list(map(lambda p: SRAMParameters.from_setting(p), raw_params))
        sram_generator_tool.input_parameters = sram_params
        # TODO: support hierarchical?

        if len(sram_generator_tool.input_parameters) == 0:
            self.log.warning("No SRAM parameters specified, no SRAMs will be generated.")

        self.sram_generator_tool = sram_generator_tool

        self.tool_configs["sram_generator"] = sram_generator_tool.get_config()
        self.update_tool_configs()
        return True

    def set_up_sim_tool(self, sim_tool: HammerSimTool,
                              name: str, run_dir: str = "") -> bool:
        """
        Set up and store the given simulation tool instance for use in this
        driver.
        :param sim_tool: Tool instance.
        :param name: Short name (e.g. "vcs") of the tool instance. Typically
                     obtained from the database.
        :param run_dir: Directory to use for the tool run_dir. Defaults to the
                        run_dir passed in the HammerDriver constructor.
        :return: True if setup was successful.
        """

        if self.tech is None:
            self.log.error("Must load technology before loading sim tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "sim-rundir")

        sim_tool.name = name
        sim_tool.logger = self.log.context("sim")
        sim_tool.set_database(self.database)
        sim_tool.run_dir = run_dir
        sim_tool.technology = self.tech
        sim_tool.input_files = self.database.get_setting("sim.inputs.input_files")
        sim_tool.top_module = self.database.get_setting("sim.inputs.top_module", nullvalue="")
        sim_tool.submit_command = HammerSubmitCommand.get("sim", self.database)
        sim_tool.all_regs = self.database.get_setting("sim.inputs.all_regs")
        sim_tool.seq_cells = self.database.get_setting("sim.inputs.seq_cells")
        sim_tool.sdf_file = self.database.get_setting("sim.inputs.sdf_file")

        missing_inputs = False
        if sim_tool.top_module == "":
            self.log.error("Top module not specified for simulation")
            missing_inputs = True
        if len(sim_tool.input_files) == 0:
            self.log.error("No input files specified for simulation")
            missing_inputs = True
        if missing_inputs:
            return False

        self.sim_tool = sim_tool
        self.tool_configs["simulation"] = sim_tool.get_config()
        self.update_tool_configs()
        return True

    def load_sim_tool(self, run_dir: str = "") -> bool:
        """
        Load the simulation tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if simulation tool loading was successful, False otherwise.
        """
        config_result = self.instantiate_tool_from_config("sim", HammerSimTool)
        if config_result is None:
            return False
        else:
            (sim_tool, name) = config_result
            assert isinstance(sim_tool, HammerSimTool)
            return self.set_up_sim_tool(sim_tool, name, run_dir)

    def load_pcb_tool(self, run_dir: str = "") -> bool:
        """
        Load the PCB deliverable tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if successful, false otherwise
        """
        if self.tech is None:
            self.log.error("Must load technology before loading PCB deliverable tool")
            return False

        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "pcb-rundir")

        pcb_tool_name = self.database.get_setting("vlsi.core.pcb_tool")
        pcb_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.pcb_tool_path"),
            tool_name=pcb_tool_name
        )
        assert isinstance(pcb_tool_get, HammerPCBDeliverableTool), "PCB deliverable tool must be a HammerPCBDeliverableTool"
        pcb_tool = pcb_tool_get  # type: HammerPCBDeliverableTool
        pcb_tool.name = pcb_tool_name
        pcb_tool.logger = self.log.context("pcb")
        pcb_tool.technology = self.tech
        pcb_tool.set_database(self.database)
        pcb_tool.top_module = self.database.get_setting("pcb.inputs.top_module", nullvalue="")
        if pcb_tool.top_module == "":
            self.log.error("Top module not specified for PCB")
            return False
        pcb_tool.submit_command = HammerSubmitCommand.get("pcb", self.database)
        pcb_tool.run_dir = run_dir

        self.pcb_tool = pcb_tool

        self.tool_configs["pcb"] = pcb_tool.get_config()
        self.update_tool_configs()
        return True

    def set_post_custom_syn_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the extra list of hooks used for control flow (resume/pause) in run_synthesis.
        They will run after main/hook_actions.

        :param hooks: Hooks to run
        """
        self.post_custom_syn_tool_hooks = list(hooks)

    def set_post_custom_par_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the extra list of hooks used for control flow (resume/pause) in run_par.
        They will run after main/hook_actions.

        :param hooks: Hooks to run
        """
        self.post_custom_par_tool_hooks = list(hooks)

    def set_post_custom_drc_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the extra list of hooks used for control flow (resume/pause) in run_drc.
        They will run after main/hook_actions.

        :param hooks: Hooks to run
        """
        self.post_custom_drc_tool_hooks = list(hooks)

    def set_post_custom_lvs_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the extra list of hooks used for control flow (resume/pause) in run_lvs.
        They will run after main/hook_actions.

        :param hooks: Hooks to run
        """
        self.post_custom_lvs_tool_hooks = list(hooks)

    def set_post_custom_sim_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the extra list of hooks used for control flow (resume/pause) in run_sim.
        They will run after main/hook_actions.

        :param hooks: Hooks to run
        """
        self.post_custom_sim_tool_hooks = list(hooks)

    def run_synthesis(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> \
            Tuple[bool, dict]:
        """
        Run synthesis based on the given database.
        The output config dict returned does NOT have a copy of the input config settings.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_synthesis_hooks.
                             Hooks from set_synthesis_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """
        if self.syn_tool is None:
            self.log.error("Must load synthesis tool before calling run_synthesis")
            return False, {}

        # TODO: think about artifact storage?
        self.log.info("Starting synthesis with tool '%s'" % (self.syn_tool.name))
        if hook_actions is None:
            hooks_to_use = self.post_custom_syn_tool_hooks
        else:
            if force_override:
                hooks_to_use = hook_actions
            else:
                hooks_to_use = hook_actions + self.post_custom_syn_tool_hooks
        run_succeeded = self.syn_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("Synthesis tool %s failed! Please check its output." % self.syn_tool.name)
            # Allow the flow to keep running, just in case.
            # TODO: make this an option

        # Record output from the tool into the JSON output.
        # Note: the output config dict is NOT complete
        output_config = {}  # type: Dict[str, Any]
        # TODO(edwardw): automate this
        try:
            output_config = deepdict(self.syn_tool.export_config_outputs())
            if output_config.get("vlsi.builtins.is_complete", True):
                self.log.error(
                    "The synthesis plugin is mis-written; "
                    "it did not mark its output dictionary as output-only "
                    "or did not call super().export_config_outputs(). "
                    "Subsequent commands might not behave correctly.")
                output_config["vlsi.builtins.is_complete"] = False
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    @staticmethod
    def synthesis_output_to_par_input(output_dict: dict) -> Optional[dict]:
        """
        Generate the appropriate inputs for running place-and-route from the
        outputs of synthesis run.
        Does not merge the results with any project dictionaries.
        :param output_dict: Dict containing synthesis.outputs.*
        :return: par.inputs.* settings generated from output_dict,
                 or None if output_dict was invalid
        """
        try:
            output_files = deeplist(output_dict["synthesis.outputs.output_files"])
            result = {
                "par.inputs.input_files": output_files,
                "par.inputs.top_module": output_dict["synthesis.inputs.top_module"],
                "vlsi.builtins.is_complete": False
            }  # type: Dict[str, Any]
            if "synthesis.outputs.sdc" in output_dict:
                result["par.inputs.post_synth_sdc"] = output_dict["synthesis.outputs.sdc"]
            return result
        except KeyError:
            # KeyError means that the given dictionary is missing output keys.
            return None

    @staticmethod
    def synthesis_output_to_sim_input(output_dict: dict) -> Optional[dict]:
        """
        Generate the appropriate inputs for running gate level simulations from the
        outputs of synthesis run.
        Does not merge the results with any project dictionaries.
        :param output_dict: Dict containing synthesis.outputs.*
        :return: sim.inputs.* settings generated from output_dict,
                 or None if output_dict was invalid
        """
        try:
            output_files = deeplist(output_dict["synthesis.outputs.output_files"])
            all_regs = deeplist(output_dict["synthesis.outputs.all_regs"])
            result = {
                "sim.inputs.input_files": output_files,
                "sim.inputs.input_files_meta": "append",
                "sim.inputs.top_module": output_dict["synthesis.inputs.top_module"],
                "sim.inputs.all_regs": all_regs,
                "sim.inputs.seq_cells": output_dict["synthesis.outputs.seq_cells"],
                "sim.inputs.sdf_file": output_dict["synthesis.outputs.sdf_file"],
                "vlsi.builtins.is_complete": False
            }  # type: Dict[str, Any]
            return result
        except KeyError:
            # KeyError means that the given dictionary is missing output keys.
            return None

    @staticmethod
    def par_output_to_sim_input(output_dict: dict) -> Optional[dict]:
        """
        Generate the appropriate inputs for running gate level simulations from the
        outputs of par run.
        Does not merge the results with any project dictionaries.
        :param output_dict: Dict containing par.outputs.*
        :return: sim.inputs.* settings generated from output_dict,
                 or None if output_dict was invalid
        """
        try:
            all_regs = deeplist(output_dict["par.outputs.all_regs"])
            sim_input_files = deeplist([output_dict["par.outputs.output_sim_netlist"]])
            result = {
                "sim.inputs.input_files": sim_input_files,
                "sim.inputs.input_files_meta": "append",
                "sim.inputs.top_module": output_dict["par.inputs.top_module"],
                "sim.inputs.all_regs": all_regs,
                "sim.inputs.seq_cells": output_dict["par.outputs.seq_cells"],
                "sim.inputs.sdf_file": output_dict["par.outputs.sdf_file"],
                "vlsi.builtins.is_complete": False
            }  # type: Dict[str, Any]
            return result
        except KeyError:
            # KeyError means that the given dictionary is missing output keys.
            return None

    def run_par(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> Tuple[
        bool, dict]:
        """
        Run place and route based on the given database.
        The output config dict returned does NOT have a copy of the input config settings.
        """
        if self.par_tool is None:
            self.log.error("Must load par tool before calling run_par")
            return False, {}

        # TODO: update API to match run_synthesis and deduplicate logic
        self.log.info("Starting place and route with tool '%s'" % (self.par_tool.name))
        if hook_actions is None:
            hooks_to_use = self.post_custom_par_tool_hooks
        else:
            if force_override:
                hooks_to_use = hook_actions
            else:
                hooks_to_use = hook_actions + self.post_custom_par_tool_hooks
        # TODO: get place and route working
        run_succeeded = self.par_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("Place and route tool %s failed! Please check its output." % self.par_tool.name)
            # Allow the flow to keep running, just in case.
            # TODO: make this an option

        # Record output from the tool into the JSON output.
        # Note: the output config dict is NOT complete
        output_config = {}  # type: Dict[str, Any]
        # TODO(edwardw): automate this
        try:
            output_config = deepdict(self.par_tool.export_config_outputs())
            if output_config.get("vlsi.builtins.is_complete", True):
                self.log.error(
                    "The place-and-route plugin is mis-written; "
                    "it did not mark its output dictionary as output-only "
                    "or did not call super().export_config_outputs(). "
                    "Subsequent commands might not behave correctly.")
                output_config["vlsi.builtins.is_complete"] = False
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    @staticmethod
    def par_output_to_syn_input(output_dict: dict) -> Optional[dict]:
        """
        Generate the appropriate inputs for running the next level of synthesis from the
        outputs of par run in a hierarchical flow.
        Does not merge the results with any project dictionaries.
        :param output_dict: Dict containing par.outputs.*
        :return: vlsi.inputs.* settings generated from output_dict,
                 or None if output_dict was invalid
        """
        try:
            result = {
                "vlsi.inputs.ilms": output_dict["par.outputs.output_ilms"],
                "vlsi.builtins.is_complete": False
            }  # type: Dict[str, Any]
            return result
        except KeyError:
            # KeyError means that the given dictionary is missing output keys.
            return None

    @staticmethod
    def par_output_to_drc_input(output_dict: dict) -> Optional[dict]:
        """
        Generate the appropriate inputs for running DRC from the
        outputs of par run.
        Does not merge the results with any project dictionaries.
        :param output_dict: Dict containing par.outputs.*
        :return: drc.inputs.* settings generated from output_dict,
                 or None if output_dict was invalid
        """
        try:
            result = {
                "drc.inputs.top_module": output_dict["par.inputs.top_module"],
                "drc.inputs.layout_file": output_dict["par.outputs.output_gds"],
                "vlsi.builtins.is_complete": False
            }  # type: Dict[str, Any]
            return result
        except KeyError:
            # KeyError means that the given dictionary is missing output keys.
            return None

    @staticmethod
    def par_output_to_lvs_input(output_dict: dict) -> Optional[dict]:
        """
        Generate the appropriate inputs for running LVS from the
        outputs of par run.
        Does not merge the results with any project dictionaries.
        :param output_dict: Dict containing par.outputs.*
        :return: lvs.inputs.* settings generated from output_dict,
                 or None if output_dict was invalid
        """
        try:
            result = {
                "lvs.inputs.top_module": output_dict["par.inputs.top_module"],
                "lvs.inputs.layout_file": output_dict["par.outputs.output_gds"],
                "lvs.inputs.schematic_files": [output_dict["par.outputs.output_netlist"]],
                "lvs.inputs.ilms": output_dict["par.outputs.output_ilms"],
                "lvs.inputs.hcells_list": output_dict["par.outputs.hcells_list"],
                "vlsi.builtins.is_complete": False
            }  # type: Dict[str, Any]
            return result
        except KeyError:
            # KeyError means that the given dictionary is missing output keys.
            return None

    def run_drc(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> Tuple[
        bool, dict]:
        """
        Run DRC on a given database.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_drc_hooks.
                             Hooks from set_drc_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """
        if self.drc_tool is None:
            self.log.error("Must load DRC tool before calling run_drc")
            return False, {}

        self.log.info("Starting DRC check with tool '%s'" % (self.drc_tool.name))

        if hook_actions is None:
            hooks_to_use = self.post_custom_drc_tool_hooks
        elif force_override:
            hooks_to_use = hook_actions
        else:
            hooks_to_use = hook_actions + self.post_custom_drc_tool_hooks

        run_succeeded = self.drc_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("DRC tool %s failed! Please check its output." % self.drc_tool.name)
            # Allow the flow to keep running, just in case

        # Record output from the drc_tool into the JSON output
        output_config = {}  # type: Dict[str, Any]
        try:
            output_config.update(self.drc_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def run_lvs(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> Tuple[
        bool, dict]:
        """
        Run LVS on a given database.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_lvs_hooks.
                             Hooks from set_lvs_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """
        if self.lvs_tool is None:
            self.log.error("Must load LVS tool before calling run_lvs")
            return False, {}

        self.log.info("Starting LVS check with tool '%s'" % (self.lvs_tool.name))

        if hook_actions is None:
            hooks_to_use = self.post_custom_lvs_tool_hooks
        elif force_override:
            hooks_to_use = hook_actions
        else:
            hooks_to_use = hook_actions + self.post_custom_lvs_tool_hooks

        run_succeeded = self.lvs_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("LVS tool %s failed! Please check its output." % self.lvs_tool.name)
            # Allow the flow to keep running, just in case

        # Record output from the lvs_tool into the JSON output
        output_config = {}  # type: Dict[str, Any]
        try:
            output_config.update(self.lvs_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def run_sram_generator(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> Tuple[
        bool, dict]:
        """
        Run SRAM Generator on a given database.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_sram_generator_hooks.
                             Hooks from set_sram_generator_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """
        if self.sram_generator_tool is None:
            self.log.error("Must load SRAM Generator tool before calling run_sram_generator")
            return False, {}

        self.log.info("Starting SRAM Generator with tool '%s'" % (self.sram_generator_tool.name))

        if hook_actions is None:
            hooks_to_use = self.post_custom_sram_generator_tool_hooks
        elif force_override:
            hooks_to_use = hook_actions
        else:
            hooks_to_use = hook_actions + self.post_custom_sram_generator_tool_hooks

        run_succeeded = self.sram_generator_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("SRAM Generator tool %s failed! Please check its output." % self.sram_generator_tool.name)
            # Allow the flow to keep running, just in case

        # Record output from the sram_generator_tool into the JSON output
        output_config = {}  # type: Dict[str, Any]
        try:
            output_config.update(self.sram_generator_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def run_sim(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> \
            Tuple[bool, dict]:
        """
        Run simulation based on the given database.
        The output config dict returned does NOT have a copy of the input config settings.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_simulation_hooks.
                             Hooks from set_simulation_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """
        if self.sim_tool is None:
            self.log.error("Must load simulation tool before calling run_sim")
            return False, {}

        # TODO: think about artifact storage?
        self.log.info("Starting simulation with tool '%s'" % (self.sim_tool.name))
        if hook_actions is None:
            hooks_to_use = self.post_custom_sim_tool_hooks
        else:
            if force_override:
                hooks_to_use = hook_actions
            else:
                hooks_to_use = hook_actions + self.post_custom_sim_tool_hooks

        run_succeeded = self.sim_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("Simulation tool %s failed! Please check its output." % self.sim_tool.name)
            # Allow the flow to keep running, just in case.
            # TODO: make this an option

        # Record output from the tool into the JSON output.
        # Note: the output config dict is NOT complete
        output_config = {}  # type: Dict[str, Any]
        try:
            output_config = deepdict(self.sim_tool.export_config_outputs())
            if output_config.get("vlsi.builtins.is_complete", True):
                self.log.error(
                    "The simulation plugin is mis-written; "
                    "it did not mark its output dictionary as output-only "
                    "or did not call super().export_config_outputs(). "
                    "Subsequent commands might not behave correctly.")
                output_config["vlsi.builtins.is_complete"] = False
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def run_pcb(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> Tuple[
        bool, dict]:
        """
        Run the PCB deliverable generation tool

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_pcb_hooks.
                             Hooks from set_pcb_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """
        if self.pcb_tool is None:
            self.log.error("Must load PCB deliverable tool before calling run_pcb")
            return False, {}

        self.log.info("Starting PCB deliverable generation with tool '%s'" % (self.pcb_tool.name))

        if hook_actions is None:
            hooks_to_use = self.post_custom_pcb_tool_hooks
        elif force_override:
            hooks_to_use = hook_actions
        else:
            hooks_to_use = hook_actions + self.post_custom_pcb_tool_hooks

        run_succeeded = self.pcb_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("PCB deliverable tool %s failed! Please check its output." % self.pcb_tool.name)
            # Allow the flow to keep running, just in case

        # Record output from the pcb_tool into the JSON output
        output_config = {}  # type: Dict[str, Any]
        try:
            output_config.update(self.pcb_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def get_hierarchical_dependency_graph(self) -> Dict[str, Tuple[List[str], List[str]]]:
        """
        Return the dependency graph for this flow if it is hierarchical, or an empty dict if it is flat.
        The flow is the set of setps configured by the current input Hammer IR.

        :return: The dependency graph.
        """
        return self._hierarchical_helper()[1]

    def get_hierarchical_settings(self) -> List[Tuple[str, dict]]:
        """
        Read settings from the database, determine leaf/hierarchical modules, an order of execution, and return an
        ordered list (from leaf to top) of modules and associated config snippets needed to run syn+par for that module
        hierarchically.

        :return: List of tuples of (module name, config snippet)
        """
        return self._hierarchical_helper()[0]

    def _hierarchical_helper(self) -> Tuple[List[Tuple[str, dict]], Dict[str, Tuple[List[str], List[str]]]]:
        """
        Read settings from the database, determine leaf/hierarchical modules, an order of execution, and return an
        ordered list (from leaf to top) of modules and associated config snippets needed to run syn+par for that module
        hierarchically and the dependency graph. Do not call this method directly- use get_hierarchical_settings or
        get_hierarchial_dependency_graph instead.

        :return: Tuple of (List of tuples of (module name, config snippet), the dependency graph)
        """
        hier_source_key = "vlsi.inputs.hierarchical.config_source"
        hier_source = str(self.database.get_setting(hier_source_key))
        hier_modules = {}  # type: Dict[str, List[str]]
        hier_placement_constraints = {}  # type: Dict[str, List[PlacementConstraint]]
        hier_constraints = {}  # type: Dict[str, List[Dict]]

        # This is retrieving the list of hard macro sizes to be used when creating PlacementConstraint tuples later
        list_of_hard_macros = self.database.get_setting("vlsi.technology.extra_macro_sizes")  # type: List[Dict]
        hard_macros = list(map(MacroSize.from_setting, list_of_hard_macros))

        if hier_source == "none":
            pass
        elif hier_source == "manual":
            list_of_hier_modules = self.database.get_setting(
                "vlsi.inputs.hierarchical.manual_modules")  # type: List[Dict]
            assert isinstance(list_of_hier_modules, list)
            if len(list_of_hier_modules) == 0:
                raise ValueError("No hierarchical modules defined manually in manual hierarchical mode")
            hier_modules = reduce(add_dicts, list_of_hier_modules)

            list_of_placement_constraints = self.database.get_setting(
                "vlsi.inputs.hierarchical.manual_placement_constraints")  # type: List[Dict]
            assert isinstance(list_of_placement_constraints, list)
            combined_raw_placement_dict = reduce(add_dicts, list_of_placement_constraints, {})  # type: Dict[str, List[Dict[str, Any]]]

            # This helper function filters only the dict containing the toplevel placement constraint, if any, from the provided list of dicts.
            # If the list does not contain a toplevel constraint, it returns None.
            def get_toplevel(d: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
                results = list(filter(lambda x: x["type"] == "toplevel", d))
                if len(results) == 0:
                    return None
                else:
                    return results[-1]

            # Use the above helper method to filter down the combined raw placement dict into a dict:
            # - keys are hierarchical module name
            # - values are dicts containing toplevel constraints or None
            toplevels_opt = {k: get_toplevel(v) for k, v in combined_raw_placement_dict.items()}  # type: Dict[str, Optional[Dict[str, Any]]]
            # This filters out all of the Nones to get only hierarchical modules with toplevel placement constraints
            toplevels = {k: v for k, v in toplevels_opt.items() if v is not None}  # type: Dict[str, Dict[str, Any]]
            # This converts each dict entry into a MacroSize tuple, which should now represent all hierarchical modules
            hier_macros = [MacroSize(library="", name=x[0], width=x[1]["width"], height=x[1]["height"]) for x in toplevels.items()]
            masters = hard_macros + hier_macros

            hier_placement_constraints = {key: list(map(partial(PlacementConstraint.from_masters_and_dict, masters), lst))
                                          for key, lst in combined_raw_placement_dict.items()}
            list_of_hier_constraints = self.database.get_setting(
                    "vlsi.inputs.hierarchical.constraints") # type: List[Dict]
            hier_constraints = reduce(add_dicts, list_of_hier_constraints, {})
        elif hier_source == "from_placement":
            raise NotImplementedError("Generation from placement not implemented yet")
        else:
            raise ValueError("Invalid value for " + hier_source_key)

        assert isinstance(hier_modules, dict)
        if not hier_modules:
            return ([], {})

        leaf_modules = set()  # type: Set[str]
        intermediate_modules = set()  # type: Set[str]
        top_module = str(self.database.get_setting("vlsi.inputs.hierarchical.top_module"))
        if top_module == "" or top_module is None:
            raise ValueError("Cannot have a hierarchical flow if the top module is not set")

        # Node + outgoing edges (nodes that depend on us) + incoming edges (nodes we depend on)
        dependency_graph = {}  # type: Dict[str, Tuple[List[str], List[str]]]

        # If there is a hierarchy, find the leaf and intermediate modules.
        def visit_module(mod: str) -> None:
            if mod not in hier_modules:
                if mod == top_module:
                    raise ValueError("Cannot have a hierarchical flow with top as leaf")
                leaf_modules.add(mod)
                return
            elif len(hier_modules[mod]) == 0:
                if mod == top_module:
                    raise ValueError("Cannot have a hierarchical flow with top as leaf")
                leaf_modules.add(mod)
                return
            else:
                if mod != top_module:
                    intermediate_modules.add(mod)
                for m in hier_modules[mod]:
                    # m depends on us
                    dependency_graph.setdefault(m, ([], []))[0].append(mod)
                    # We depend on m
                    dependency_graph.setdefault(mod, ([], []))[1].append(m)
                    visit_module(m)
        visit_module(top_module)

        # Create an order for the modules to be run in.
        order = topological_sort(dependency_graph, list(leaf_modules))

        output = []  # type: List[Tuple[str, dict]]

        for module in order:
            mode = HierarchicalMode.Hierarchical
            if module == top_module:
                mode = HierarchicalMode.Top
            elif module in leaf_modules:
                mode = HierarchicalMode.Leaf
            elif module in intermediate_modules:
                mode = HierarchicalMode.Hierarchical
            else:
                assert "Should not get here"

            constraint_dict = {
                "vlsi.inputs.hierarchical.mode": str(mode),
                "synthesis.inputs.top_module": module,
                "vlsi.inputs.placement_constraints": list(
                    map(PlacementConstraint.to_dict, hier_placement_constraints.get(module, [])))
            }
            constraint_dict = reduce(add_dicts, hier_constraints.get(module, []), constraint_dict)
            output.append((module, constraint_dict))

        return (output, dependency_graph)
