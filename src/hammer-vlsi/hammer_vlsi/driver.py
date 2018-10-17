#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  driver.py
#  HammerDriver and related code.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from functools import reduce
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any

import datetime
import os

from hammer_utils import *

import hammer_config
import hammer_tech
from .hammer_tool import HammerTool
from .hooks import HammerToolHookAction
from .hammer_vlsi_impl import HammerVLSISettings, HammerPlaceAndRouteTool, HammerSynthesisTool, \
    HierarchicalMode, load_tool, PlacementConstraint
from hammer_logging import HammerVLSIFileLogger, HammerVLSILogging, HammerVLSILoggingContext
from .hammer_submit_command import HammerSubmitCommand

__all__ = ['HammerDriverOptions', 'HammerDriver']

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
        builtins_path = os.path.join(HammerVLSISettings.hammer_vlsi_path, "builtins.yml")
        if not os.path.exists(builtins_path):
            raise FileNotFoundError("hammer-vlsi builtin settings not found. Did you call HammerVLSISettings.set_hammer_vlsi_path_from_environment()?")

        self.database.update_builtins([
            hammer_config.load_config_from_file(builtins_path, strict=True),
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

        # Initialize tool hooks. Used to specify resume/pause hooks after custom hooks have been registered.
        self.post_custom_syn_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_par_tool_hooks = []  # type: List[HammerToolHookAction]

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

    def get_hierarchical_settings(self) -> List[Tuple[str, dict]]:
        """
        Read settings from the database, determine leaf/hierarchical modules, an order of execution, and return an
        ordered list (from leaf to top) of modules and associated config snippets needed to run syn+par for that module
        hierarchically.

        :return: List of tuples of (module name, config snippet)
        """
        hier_source_key = "vlsi.inputs.hierarchical.config_source"
        hier_source = str(self.database.get_setting(hier_source_key))
        hier_modules = {}  # type: Dict[str, List[str]]
        hier_placement_constraints = {}  # type: Dict[str, List[PlacementConstraint]]
        if hier_source == "none":
            pass
        elif hier_source == "manual":
            list_of_hier_modules = self.database.get_setting(
                "vlsi.inputs.hierarchical.manual_modules")  # type: List[Dict]
            assert isinstance(list_of_hier_modules, list)
            list_of_placement_constraints = self.database.get_setting(
                "vlsi.inputs.hierarchical.manual_placement_constraints")  # type: List[Dict]
            assert isinstance(list_of_placement_constraints, list)
            hier_modules = reduce(add_dicts, list_of_hier_modules)
            combined_raw_placement_dict = reduce(add_dicts, list_of_placement_constraints)
            hier_placement_constraints = {key: list(map(PlacementConstraint.from_dict, lst))
                                          for key, lst in combined_raw_placement_dict.items()}
        elif hier_source == "from_placement":
            raise NotImplementedError("Generation from placement not implemented yet")
        else:
            raise ValueError("Invalid value for " + hier_source_key)

        assert isinstance(hier_modules, dict)
        if not hier_modules:
            return []

        leaf_modules = set()  # type: Set[str]
        intermediate_modules = set()  # type: Set[str]
        top_module = str(self.database.get_setting("vlsi.inputs.hierarchical.top_module"))

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

            output.append((module, {
                "vlsi.inputs.hierarchical.mode": str(mode),
                "synthesis.inputs.top_module": module,
                "vlsi.inputs.placement_constraints": list(map(PlacementConstraint.to_dict, hier_placement_constraints[module]))
            }))

        return output
