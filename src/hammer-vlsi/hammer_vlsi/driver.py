#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  driver.py
#  HammerDriver and related code.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from functools import reduce
from typing import NamedTuple, List, Optional, Tuple, Dict, Set

import datetime
import os

from hammer_utils import *

import hammer_config
import hammer_tech
from .hooks import HammerToolHookAction
from .hammer_vlsi_impl import HammerVLSISettings, HammerPlaceAndRouteTool, HammerSynthesisTool, \
    HierarchicalMode, load_tool, PlacementConstraint
from .hammer_vlsi_impl import HammerFormalLECTool, HammerPowerTool
from hammer_logging import HammerVLSIFileLogger, HammerVLSILogging, HammerVLSILoggingContext

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
        self.formal_tool = None  # type: Optional[HammerFormalLECTool]
        self.power_tool = None  # type: Optional[HammerPowerTool]

        # Initialize tool hooks. Used to specify resume/pause hooks after custom hooks have been registered.
        self.post_custom_syn_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_par_tool_hooks = []  # type: List[HammerToolHookAction]
        # Donggyu: do we need this for formal & power tools?
        self.post_custom_formal_tool_hooks = []  # type: List[HammerToolHookAction]
        self.post_custom_power_tool_hooks = []  # type: List[HammerToolHookAction]

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
        tech = hammer_tech.HammerTechnology.load_from_dir(tech_str, os.path.dirname(
            tech_json_path))  # type: hammer_tech.HammerTechnology
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

    def load_formal_tool(self, run_dir: str = "") -> bool:
        """
        Load the formal verification tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        """
        if run_dir == "":
            # Use the synthesis directory for formal tools
            run_dir = os.path.join(self.obj_dir, "syn-rundir")

        formal_tool_name = self.database.get_setting("vlsi.core.formal_tool")
        formal_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.formal_tool_path"),
            tool_name=formal_tool_name
        )
        assert isinstance(formal_tool_get, HammerFormalLECTool), "Formal tool must be a HammerFormalLECTool"
        formal_tool = formal_tool_get  # type: HammerTool
        formal_tool.name = formal_tool_name
        formal_tool.logger = self.log.context("formal")
        formal_tool.set_database(self.database)
        formal_tool.run_dir = run_dir

        formal_tool.input_files = self.database.get_setting("synthesis.inputs.input_files")
        if len(formal_tool.input_files) < 2:
            self.log.error("There must be at least two input files for formal tools: reference and implementation")
            return False

        self.formal_tool = formal_tool

        self.tool_configs["formal"] = formal_tool.get_config()
        self.update_tool_configs()
        return True

    def load_power_tool(self, run_dir: str = "") -> bool:
        """
        Load the power analysis tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        """
        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "pwr-rundir")

        power_tool_name = self.database.get_setting("vlsi.core.power_tool")
        power_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.power_tool_path"),
            tool_name=power_tool_name
        )
        assert isinstance(power_tool_get, HammerPowerTool), "Power tool must be a HammerPowerTool"
        power_tool = power_tool_get  # type: HammerPowerTool
        power_tool.name = power_tool_name
        power_tool.logger = self.log.context("power")
        power_tool.technology = self.tech
        power_tool.set_database(self.database)
        power_tool.run_dir = run_dir

        # TODO: better way to get input files?
        power_tool.top_module = self.database.get_setting("synthesis.inputs.top_module", nullvalue="")
        power_tool.input_files = self.database.get_setting("synthesis.inputs.input_files")
        if len(power_tool.input_files) == 0:
            self.log.error("No verilog files specified for power analysis tools")
            return False
        power_tool.waveform_files = self.database.get_setting("power.inputs.waveform_files")
        if not len(power_tool.waveform_files) == 1:
            self.log.error("There must be only one waveform file for power analysis tools")
            return False

        self.power_tool = power_tool

        self.tool_configs["power"] = power_tool.get_config()
        self.update_tool_configs()
        return True

    def load_par_tool(self, run_dir: str = "") -> bool:
        """
        Load the place and route tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
                        constructor.
        :return: True if successful, false otherwise
        """
        if self.tech is None:
            self.log.error("Must load technology before loading par tool")
            return False

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
        par_tool.hierarchical_mode = HierarchicalMode.from_str(self.database.get_setting("vlsi.inputs.hierarchical.mode"))

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
        if self.tech is None:
            self.log.error("Must load technology before loading synthesis tool")
            return False

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
        syn_tool.hierarchical_mode = HierarchicalMode.from_str(self.database.get_setting("vlsi.inputs.hierarchical.mode"))

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

    def set_post_custom_formal_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the extra list of hooks used for control flow (resume/pause) in run_par.
        They will run after main/hook_actions.

        :param hooks: Hooks to run
        """
        self.post_custom_formal_tool_hooks = list(hooks)

    def run_synthesis(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> \
            Tuple[bool, dict]:
        """
        Run synthesis based on the given database.

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

        # Record output from the syn_tool into the JSON output.
        output_config = deepdict(self.project_config)
        # TODO(edwardw): automate this
        try:
            output_config.update(self.par_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def run_formal(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> \
            Tuple[bool, dict]:
        """
        Run formal check based on the given database.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_formal_hooks.
                             Hooks from set_formal_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """

        # TODO: think about artifact storage?
        self.log.info("Starting formal check with tool '%s'" % (self.formal_tool.name))
        if hook_actions is None:
            hooks_to_use = self.post_custom_formal_tool_hooks
        else:
            if force_override:
                hooks_to_use = hook_actions
            else:
                hooks_to_use = hook_actions + self.post_custom_formal_tool_hooks
        run_succeeded = self.formal_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("Formal check tool %s failed! Please check its output." % self.formal_tool.name)
            # Allow the flow to keep running, just in case.
            # TODO: make this an option

        # Record output from the formal_tool into the JSON output.
        output_config = deepdict(self.project_config)
        # TODO(edwardw): automate this
        try:
            output_config.update(self.formal_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    def run_power(self, hook_actions: Optional[List[HammerToolHookAction]] = None, force_override: bool = False) -> \
            Tuple[bool, dict]:
        """
        Run power check based on the given database.

        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_power_hooks.
                             Hooks from set_power_hooks, if present, will be appended afterwards.
        :param force_override: Set to true to overwrite instead of append.
        :return: Tuple of (success, output config dict)
        """

        # TODO: think about artifact storage?
        self.log.info("Starting power check with tool '%s'" % (self.power_tool.name))
        if hook_actions is None:
            hooks_to_use = self.post_custom_power_tool_hooks
        else:
            if force_override:
                hooks_to_use = hook_actions
            else:
                hooks_to_use = hook_actions + self.post_custom_power_tool_hooks
        run_succeeded = self.power_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("Power analysis tool %s failed! Please check its output." % self.power_tool.name)
            # Allow the flow to keep running, just in case.
            # TODO: make this an option

        # Record output from the power_tool into the JSON output.
        output_config = deepdict(self.project_config)
        # TODO(edwardw): automate this
        try:
            output_config.update(self.power_tool.export_config_outputs())
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
