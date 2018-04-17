#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_driver.py
#  HammerDriver and related code.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from functools import reduce
from typing import NamedTuple, List, Optional, Tuple, Dict

import datetime
import os

from utils import *

import hammer_config
import hammer_tech
from hammer_vlsi_impl import HammerVLSISettings, HammerToolHookAction, HammerPlaceAndRouteTool, HammerSynthesisTool, \
    HierarchicalMode, HammerVLSIFileLogger, HammerVLSILogging, load_tool, HammerVLSILoggingContext

# Options for invoking the driver.
HammerDriverOptions = NamedTuple('HammerDriverOptions', [
    # List of environment config files in .json
    ('environment_configs', List[str]),
    # List of project config files in .json
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
            obj_dir=HammerVLSISettings.hammer_vlsi_path
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

        # Store the run dir.
        self.obj_dir = options.obj_dir  # type: str

        # Load in builtins.
        self.database.update_builtins([
            hammer_config.load_config_from_file(os.path.join(HammerVLSISettings.hammer_vlsi_path, "builtins.yml"),
                                                strict=True),
            HammerVLSISettings.get_config()
        ])

        # Read in core defaults.
        self.database.update_core(hammer_config.load_config_from_defaults(HammerVLSISettings.hammer_vlsi_path))

        # Read in the environment config for paths to CAD tools, etc.
        for config in options.environment_configs:
            if not os.path.exists(config):
                self.log.error("Environment config %s does not exist!" % (config))
        self.database.update_environment(hammer_config.load_config_from_paths(options.environment_configs, strict=True))

        # Read in the project config to find the syn, par, and tech.
        project_configs = hammer_config.load_config_from_paths(options.project_configs, strict=True)
        project_configs.append(extra_project_config)
        self.database.update_project(project_configs)
        # Store input config for later.
        self.project_config = hammer_config.combine_configs(project_configs)  # type: dict

        # Get the technology and load technology settings.
        self.tech = None  # type: hammer_tech.HammerTechnology
        self.load_technology()

        # Keep track of what the synthesis and par configs are since
        # update_tools() just takes a whole list.
        self.tool_configs = {}  # type: Dict[str, List[dict]]

        # Initialize tool fields.
        self.syn_tool = None  # type: HammerSynthesisTool
        self.par_tool = None  # type: HammerPlaceAndRouteTool

        # Initialize tool hooks. Used to specify resume/pause hooks after custom hooks have been registered.
        self.post_custom_syn_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_par_tool_hooks = []  # type: List[HammerToolHookAction]

    def load_technology(self, cache_dir: str = "") -> None:
        tech_str = self.database.get_setting("vlsi.core.technology")

        if cache_dir == "":
            cache_dir = os.path.join(self.obj_dir, "tech-%s-cache" % tech_str)

        tech_paths = self.database.get_setting("vlsi.core.technology_path")
        tech_json_path = ""  # type: str
        for path in tech_paths:
            tech_json_path = os.path.join(path, tech_str, "%s.tech.json" % tech_str)
            if os.path.exists(tech_json_path):
                break
        if tech_json_path == "":
            self.log.error("Technology {0} not found or missing .tech.json!".format(tech_str))
            return
        self.log.info("Loading technology '{0}'".format(tech_str))
        self.tech = hammer_tech.HammerTechnology.load_from_dir(tech_str, os.path.dirname(
            tech_json_path))  # type: hammer_tech.HammerTechnology
        self.tech.logger = self.log.context("tech")
        self.tech.set_database(self.database)
        self.tech.cache_dir = cache_dir
        self.tech.extract_technology_files()
        self.database.update_technology(self.tech.get_config())

    def update_tool_configs(self) -> None:
        """
        Calls self.database.update_tools with self.tool_configs as a list.
        """
        tools = reduce(lambda a, b: a + b, list(self.tool_configs.values()))
        self.database.update_tools(tools)

    def load_par_tool(self, run_dir: str = "") -> bool:
        """
        Load the place and route tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
        constructor.
        """
        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "par-rundir")

        par_tool_name = self.database.get_setting("vlsi.core.par_tool")
        par_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.par_tool_path"),
            tool_name=par_tool_name
        )
        assert isinstance(par_tool_get, HammerPlaceAndRouteTool), "Par tool must be a HammerPlaceAndRouteTool"
        par_tool = par_tool_get  # type: HammerPlaceAndRouteTool
        par_tool.name = par_tool_name
        par_tool.logger = self.log.context("par")
        par_tool.technology = self.tech
        par_tool.set_database(self.database)
        par_tool.run_dir = run_dir
        par_tool.hierarchical_mode = HierarchicalMode.from_str(self.database.get_setting("vlsi.inputs.hierarchical_mode"))

        # TODO: automate this based on the definitions
        par_tool.input_files = self.database.get_setting("par.inputs.input_files")
        par_tool.top_module = self.database.get_setting("par.inputs.top_module")
        par_tool.post_synth_sdc = self.database.get_setting("par.inputs.post_synth_sdc", nullvalue="")

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
        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "syn-rundir")

        # Find the synthesis/par tool and read in their configs.
        syn_tool_name = self.database.get_setting("vlsi.core.synthesis_tool")
        syn_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.synthesis_tool_path"),
            tool_name=syn_tool_name
        )
        if not isinstance(syn_tool_get, HammerSynthesisTool):
            self.log.error("Synthesis tool must be a HammerSynthesisTool")
            return False
        # TODO: generate this automatically
        syn_tool = syn_tool_get  # type: HammerSynthesisTool
        syn_tool.name = syn_tool_name
        syn_tool.logger = self.log.context("synthesis")
        syn_tool.technology = self.tech
        syn_tool.set_database(self.database)
        syn_tool.run_dir = run_dir
        syn_tool.hierarchical_mode = HierarchicalMode.from_str(self.database.get_setting("vlsi.inputs.hierarchical_mode"))

        syn_tool.input_files = self.database.get_setting("synthesis.inputs.input_files")
        syn_tool.top_module = self.database.get_setting("synthesis.inputs.top_module", nullvalue="")
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

    def run_synthesis(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> \
            Tuple[bool, dict]:
        """
        Run synthesis based on the given database.
        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_synthesis_hooks.
        Hooks from set_synthesis_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """

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

        # Record output from the syn_tool into the JSON output.
        output_config = deepdict(self.project_config)
        # TODO(edwardw): automate this
        try:
            output_config.update(self.syn_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    @staticmethod
    def generate_par_inputs_from_synthesis(config_in: dict) -> dict:
        """Generate the appropriate inputs for running place-and-route from the outputs of synthesis run."""
        output_dict = deepdict(config_in)
        # Plug in the outputs of synthesis into the par inputs.
        output_dict["par.inputs.input_files"] = output_dict["synthesis.outputs.output_files"]
        output_dict["par.inputs.top_module"] = output_dict["synthesis.inputs.top_module"]
        if "synthesis.outputs.sdc" in output_dict:
            output_dict["par.inputs.post_synth_sdc"] = output_dict["synthesis.outputs.sdc"]
        return output_dict

    def run_par(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> Tuple[
        bool, dict]:
        """
        Run place and route based on the given database.
        """
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

        # Record output from the syn_tool into the JSON output.
        output_config = deepdict(self.project_config)
        # TODO(edwardw): automate this
        try:
            output_config.update(self.par_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config
