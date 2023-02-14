#  cli_driver.py
#  CLI driver class for the Hammer VLSI abstraction.
#
#  See LICENSE for licence details.

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import importlib.resources

import ruamel.yaml

import hammer.config
from .hammer_vlsi_impl import HammerTool, HammerVLSISettings
from .hooks import HammerToolHookAction, HammerStartStopStep
from .driver import HammerDriver, HammerDriverOptions
from .hammer_build_systems import BuildSystems

from functools import reduce
from textwrap import dedent
from typing import List, Dict, Tuple, Any, Callable, Optional, Union, cast

from hammer.utils import add_dicts, deeplist, deepdict, get_or_else, check_function_type

from hammer.config import HammerJSONEncoder


KEY_DIR = tempfile.mkdtemp()
KEY_PATH = os.path.join(KEY_DIR, "key-history.json")

def parse_optional_file_list_from_args(args_list: Any, append_error_func: Callable[[str], None]) -> List[str]:
    """Parse a possibly null list of files, validate the existence of each file, and return a list of paths (possibly
    empty)."""
    results = []  # type: List[str]
    if args_list is None:
        # No arguments
        pass
    elif isinstance(args_list, List):
        # Check for file's existence before canonicalization so that we can give the user a sane error message
        for c in args_list:
            if not os.path.exists(c):
                append_error_func("Given path %s does not exist!" % c)
        # Canonicalize the path at this point
        results = list(map(os.path.realpath, args_list))
    else:
        append_error_func("Argument was not a list?")
    return results


def get_nonempty_str(arg: Any) -> Optional[str]:
    """Either get the non-empty string from the given arg or None if it is not a non-empty string."""
    if isinstance(arg, str):
        if len(arg) > 0:
            return str(arg)
    return None


def dump_config_to_json_file(output_path: str, config: dict) -> None:
    """
    Helper function to dump the given config to the given output path while overwriting it if it already exists.
    :param output_path: Output path (e.g. "obj/output.log")
    :param config: Config dictionary to dump
    """
    with open(output_path, "w") as f:
        f.write(json.dumps(config, cls=HammerJSONEncoder, indent=4))

def dump_config_to_yaml_file(output_path: str, config: dict) -> None:
    """
    Helper function to dump the given config in YAML form
    to the given output path while overwriting it if it already exists.
    :param output_path: Output path
    :param config: Config dictionary to dump
    """
    yaml = ruamel.yaml.YAML()
    yaml.indent(offset=2, sequence=4)
    with open(output_path, 'w') as f:
        yaml.dump(config, f)

def add_key_history(config: dict, history: dict) -> Any:
    """
    Generates a YAML file with comments indicating what files modified said keys.
    """
    new = ruamel.yaml.CommentedMap()
    curr_slot = 0
    for k, v in config.items():
        if k in history:
            pretty_hist = ', '.join(history[k])
            new.insert(curr_slot, k, v, comment=f"Modified by: {pretty_hist}")
        else:
            new.insert(curr_slot, k, v)
        curr_slot += 1
    return new

# Type signature of a CLIDriver action that returns a config dictionary.
CLIActionConfigType = Callable[[HammerDriver, Callable[[str], None]], Optional[dict]]

# Type signature of a CLIDriver action that returns a raw string.
CLIActionStringType = Callable[[HammerDriver, Callable[[str], None]], Optional[str]]

# CLIDriver action types.
CLIActionType = Union[CLIActionConfigType, CLIActionStringType]


# We cannot use isinstance() with CLIActionConfigType directly:
# "Parameterized generics cannot be used with class or instance checks"

def is_config_action(func: CLIActionType) -> bool:
    """Return True if the given function is a CLIActionConfigType."""
    return check_function_type(func, [HammerDriver, cast(type, Callable[[str], None])], cast(type, Optional[dict])) is None


def is_string_action(func: CLIActionType) -> bool:
    """Return True if the given function is a CLIActionConfigType."""
    return check_function_type(func, [HammerDriver, cast(type, Callable[[str], None])], cast(type, Optional[str])) is None


def check_CLIActionType_type(func: CLIActionType) -> None:
    """
    Check that the given CLIActionType obeys its function type signature.
    Raises TypeError if the function is of the incorrect type.
    """
    s = [HammerDriver, cast(type, Callable[[str], None])]
    config_check = check_function_type(func, s, cast(type, Optional[dict]))
    if config_check is None:
        return

    string_check = check_function_type(func, s, cast(type, Optional[str]))
    if string_check is None:
        return

    raise TypeError(
        "func does not appear to be a CLIActionType. Check for config returned {config}; check for string returned {string}".format(
            config=config_check, string=string_check))


class CLIDriver:
    """
    Helper class for projects to easily write/customize a CLI driver for hammer without needing to rewrite/copy all the
    argparse and plumbing.
    """

    def __init__(self) -> None:
        # Cache for the synthesis dir and par dir.
        # Defaults to blank (obj_dir + syn-rundir/par-rundir)
        self.syn_rundir = ""  # type: Optional[str]
        self.par_rundir = ""  # type: Optional[str]
        self.drc_rundir = ""  # type: Optional[str]
        self.lvs_rundir = ""  # type: Optional[str]
        self.sram_generator_rundir = ""  # type: Optional[str]
        self.sim_rundir = ""  # type: Optional[str]
        self.power_rundir = "" # type: Optional[str]
        self.formal_rundir = "" # type: Optional[str]
        self.timing_rundir = "" # type: Optional[str]
        self.pcb_rundir = ""  # type: Optional[str]

        # If a subclass has defined these, don't clobber them in init
        # since the subclass still uses this init function.
        if hasattr(self, "sram_generator_action"):
            check_CLIActionType_type(self.sram_generator_action)
        else:
            self.sram_generator_action = self.create_sram_generator_action([])  # type: CLIActionConfigType
        if hasattr(self, "pcb_action"):
            check_CLIActionType_type(self.pcb_action)
        else:
            self.pcb_action = self.create_pcb_action([])  # type: CLIActionConfigType
        if hasattr(self, "synthesis_action"):
            check_CLIActionType_type(self.synthesis_action)
        else:
            self.synthesis_action = self.create_synthesis_action([])  # type: CLIActionConfigType
        if hasattr(self, "par_action"):
            check_CLIActionType_type(self.par_action)
        else:
            self.par_action = self.create_par_action([])  # type: CLIActionConfigType
        if hasattr(self, "drc_action"):
            check_CLIActionType_type(self.drc_action)
        else:
            self.drc_action = self.create_drc_action([])  # type: CLIActionConfigType
        if hasattr(self, "lvs_action"):
            check_CLIActionType_type(self.lvs_action)
        else:
            self.lvs_action = self.create_lvs_action([])  # type: CLIActionConfigType
        if hasattr(self, "synthesis_par_action"):
            check_CLIActionType_type(self.synthesis_par_action)
        else:
            self.synthesis_par_action = self.create_synthesis_par_action(self.synthesis_action,
                                                                         self.par_action)  # type: CLIActionConfigType
        if hasattr(self, "sim_action"):
            check_CLIActionType_type(self.sim_action)
        else:
            self.sim_action = self.create_sim_action([])  # type: CLIActionConfigType
        if hasattr(self, "synthesis_sim_action"):
            check_CLIActionType_type(self.synthesis_sim_action)
        else:
            self.synthesis_sim_action = self.create_synthesis_sim_action(self.synthesis_action, self.sim_action)  # type: CLIActionConfigType
        if hasattr(self, "par_sim_action"):
            check_CLIActionType_type(self.par_sim_action)
        else:
            self.par_sim_action = self.create_par_sim_action(self.par_action, self.sim_action) # type: CLIActionConfigType
        if hasattr(self, "power_action"):
            check_CLIActionType_type(self.power_action)
        else:
            self.power_action = self.create_power_action([]) # type: CLIActionConfigType
        if hasattr(self, "formal_action"):
            check_CLIActionType_type(self.formal_action)
        else:
            self.formal_action = self.create_formal_action([]) # type: CLIActionConfigType
        if hasattr(self, "timing_action"):
            check_CLIActionType_type(self.timing_action)
        else:
            self.timing_action = self.create_timing_action([]) # type: CLIActionConfigType

        # Dictionaries of module-CLIActionConfigType for hierarchical flows.
        # See all_hierarchical_actions() below.
        self.hierarchical_synthesis_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_par_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_synthesis_par_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_drc_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_lvs_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_sim_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_power_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_formal_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_timing_actions = {}  # type: Dict[str, CLIActionConfigType]
        self.hierarchical_auto_action = None  # type: Optional[CLIActionConfigType]

    def action_map(self) -> Dict[str, CLIActionType]:
        """Return the mapping of valid actions -> functions for each action of the command-line driver."""
        return add_dicts({
            "build": self.generate_build_inputs,
            "build-inputs": self.generate_build_inputs,
            "build_inputs": self.generate_build_inputs,
            "dump": self.dump_action,
            "dump-macrosizes": self.dump_macrosizes_action,
            "dump_macrosizes": self.dump_macrosizes_action,
            "info": self.info_action,
            "sram-generator": self.sram_generator_action,
            "sram_generator": self.sram_generator_action,
            "pcb": self.pcb_action,
            "synthesis": self.synthesis_action,
            "syn": self.synthesis_action,
            "par": self.par_action,
            "synthesis_to_par": self.synthesis_to_par_action,
            "synthesis-to-par": self.synthesis_to_par_action,
            "syn_to_par": self.synthesis_to_par_action,
            "syn-to-par": self.synthesis_to_par_action,
            "synthesis_par": self.synthesis_par_action,
            "synthesis-par": self.synthesis_par_action,
            "syn_par": self.synthesis_par_action,
            "syn-par": self.synthesis_par_action,
            "hier_par_to_syn": self.hier_par_to_syn_action,
            "hier-par-to-syn": self.hier_par_to_syn_action,
            "par_to_drc": self.par_to_drc_action,
            "par-to-drc": self.par_to_drc_action,
            "par_to_lvs": self.par_to_lvs_action,
            "par-to-lvs": self.par_to_lvs_action,
            "drc": self.drc_action,
            "lvs": self.lvs_action,
            "sim": self.sim_action,
            "simulation": self.sim_action,
            "synthesis_to_sim": self.synthesis_to_sim_action,
            "synthesis-to-sim": self.synthesis_to_sim_action,
            "syn_to_sim": self.synthesis_to_sim_action,
            "syn-to-sim": self.synthesis_to_sim_action,
            "synthesis_sim": self.synthesis_sim_action,
            "synthesis-sim": self.synthesis_sim_action,
            "syn_sim": self.synthesis_sim_action,
            "syn-sim": self.synthesis_sim_action,
            "par_to_sim": self.par_to_sim_action,
            "par-to-sim": self.par_to_sim_action,
            "par_sim": self.par_sim_action,
            "par-sim": self.par_sim_action,
            "power": self.power_action,
            "syn-to-power": self.syn_to_power_action,
            "syn_to_power": self.syn_to_power_action,
            "par-to-power": self.par_to_power_action,
            "par_to_power": self.par_to_power_action,
            "sim-to-power": self.sim_to_power_action,
            "sim_to_power": self.sim_to_power_action,
            "formal": self.formal_action,
            "synthesis_to_formal": self.synthesis_to_formal_action,
            "synthesis-to-formal": self.synthesis_to_formal_action,
            "syn_to_formal": self.synthesis_to_formal_action,
            "syn-to-formal": self.synthesis_to_formal_action,
            "par_to_formal": self.par_to_formal_action,
            "par-to-formal": self.par_to_formal_action,
            "timing": self.timing_action,
            "synthesis_to_timing": self.synthesis_to_timing_action,
            "synthesis-to-timing": self.synthesis_to_timing_action,
            "syn_to_timing": self.synthesis_to_timing_action,
            "syn-to-timing": self.synthesis_to_timing_action,
            "par_to_timing": self.par_to_timing_action,
            "par-to-timing": self.par_to_timing_action
        }, self.all_hierarchical_actions)

    @staticmethod
    def dump_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """
        Just dump the parsed project configuration as the output.
        """
        return driver.project_config

    @staticmethod
    def info_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """
        Return the descripion of any key.
        """
        defaults_txt = importlib.resources.files("hammer.config").joinpath("defaults.yml").read_text()
        yaml = ruamel.yaml.YAML()
        data = yaml.load(defaults_txt)
        with open(KEY_PATH, 'r', encoding="utf-8") as f:
            yaml = ruamel.yaml.YAML()
            history = yaml.load(f)
        while True:
            curr_level = data
            overall_key = []
            while isinstance(curr_level, ruamel.yaml.CommentedMap):
                print()
                for k in curr_level.keys():
                    if "_meta" not in k:
                        print(k)
                while True:
                    try:
                        key = input("Select from the current level of keys: ")
                        next_level = curr_level[key]
                        break
                    except KeyError:
                        driver.log.error(f"Key {key} could not be found at the current level, try again.")
                overall_key.append(key)
                if not isinstance(next_level, ruamel.yaml.CommentedMap):
                    flat_key = '.'.join(overall_key)
                    if not driver.database.has_setting(flat_key):
                        val = curr_level.get(key)
                        driver.log.warning(f"{flat_key} is not in the project configuration, the default value is displayed.")
                    else:
                        val = driver.database.get_setting(flat_key)
                    if key in curr_level.ca.items:
                        comment = curr_level.ca.items[key][2].value.strip().replace('\n', ' ')  # NOTE: only takes in comment immediately after the key-value pair
                    else:
                        comment = "no comment provided"
                    key_hist = history[flat_key] if flat_key in history else "no history provided"
                    print(dedent(f"""
                    ----------------------------------------
                    Key: {flat_key}
                    Value: {val}
                    Description: {comment}
                    History: {key_hist}
                    ----------------------------------------
                    """))
                    while True:
                        continue_input = input("Continue querying keys? [y/n]: ")
                        if continue_input.lower() == 'y':
                            break
                        if continue_input.lower() == 'n':
                            return driver.project_config
                        driver.log.error("Please input either [y]es or [n]o.")
                    break
                curr_level = next_level

    @staticmethod
    def dump_macrosizes_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[str]:
        """
        Dump macro size information.
        """
        assert driver.tech is not None, "must have a technology"
        macro_json = list(map(lambda m: m.to_setting(), driver.tech.get_macro_sizes()))
        return json.dumps(macro_json, cls=HammerJSONEncoder, indent=4)

    def get_extra_synthesis_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra synthesis hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_par_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra place and route hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_drc_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra design-rule-check hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_lvs_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra layout-vs-schematic hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_sram_generator_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra SRAM generation hooks in this project.
        To be overriden by subclasses.
        """
        return list()

    def get_extra_sim_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra simulation hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_power_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra power hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_formal_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra formal hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_timing_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra timing hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def get_extra_pcb_hooks(self) -> List[HammerToolHookAction]:
        """
        Return a list of extra PCB deliverable hooks in this project.
        To be overridden by subclasses.
        """
        return list()

    def create_synthesis_action(self, custom_hooks: List[HammerToolHookAction],
                                pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                                post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                                post_run_func: Optional[Callable[[HammerDriver], None]] = None
                                ) -> CLIActionConfigType:
        hooks = self.get_extra_synthesis_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("synthesis", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_par_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_par_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("par", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    @staticmethod
    def get_full_config(driver: HammerDriver, output: dict) -> dict:
        """
        Get the full configuration by combining the project config from the
        driver with the given output dict (i.e. it contains only
        "synthesis.output.blah") that we want to combine with the project
        config.
        :param driver: HammerDriver that has the full project config.
        :param output: Output dict containing specific settings we want to add
                       to the full project config.
        :return: Full project config combined with the output dict
        """
        if "vlsi.builtins.is_complete" in output:
            if bool(output["vlsi.builtins.is_complete"]):
                raise ValueError("Output-only config claims it is complete")
        else:
            raise ValueError("Output-only config does not appear to be output only")

        output_full = deepdict(driver.project_config)
        output_full.update(deepdict(output))
        # Merged configs are always complete
        if "vlsi.builtins.is_complete" in output_full:
            del output_full["vlsi.builtins.is_complete"]
        return output_full

    def create_drc_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_drc_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("drc", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_lvs_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_lvs_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("lvs", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_sim_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_sim_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("sim", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_power_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_power_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("power", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_formal_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_formal_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("formal", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_timing_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_timing_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("timing", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_sram_generator_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_sram_generator_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("sram_generator", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_pcb_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        hooks = self.get_extra_pcb_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("pcb", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_action(self, action_type: str,
                      extra_hooks: Optional[List[HammerToolHookAction]],
                      pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                      post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                      post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionConfigType:
        """
        Create an action function for the action_map.

        :param action_type: Either "syn"/"synthesis" or "par"
        :param extra_hooks: List of hooks to pass to the run function.
        :param pre_action_func: Optional function to call before doing anything.
        :param post_load_func: Optional function to call after loading the tool.
        :param post_run_func: Optional function to call after running the tool.
        :return: Action function.
        """

        def post_load_func_checked(driver: HammerDriver) -> None:
            """Check that post_load_func isn't null before calling it."""
            if post_load_func is not None:
                post_load_func(driver)

        def post_run_func_checked(driver: HammerDriver) -> None:
            """Check that post_run_func isn't null before calling it."""
            if post_run_func is not None:
                post_run_func(driver)

        def action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
            if pre_action_func is not None:
                pre_action_func(driver)

            # If the driver didn't successfully load, return None.
            # Note the step/hook priority is (in order of lowest to highest):
            # 1. Tool-supplied core steps
            # 2. Tool-supplied hooks (usually for persistence)
            # 3. Tech-supplied hooks
            # 4. User-supplied hooks
            assert driver.tech is not None, "must have a technology"
            with open(KEY_PATH, 'r') as f:
                key_history = json.load(f)
            if action_type == "synthesis" or action_type == "syn":
                if not driver.load_synthesis_tool(get_or_else(self.syn_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.syn_tool is not None, "load_synthesis_tool was unsuccessful"
                success, output = driver.run_synthesis(
                        driver.syn_tool.get_tool_hooks() + \
                        driver.tech.get_tech_syn_hooks(driver.syn_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("Synthesis tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.syn_tool.run_dir, "syn-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.syn_tool.run_dir, "syn-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.syn_tool.run_dir, "syn-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "par":
                if not driver.load_par_tool(get_or_else(self.par_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.par_tool is not None, "load_par_tool was unsuccessful"
                success, output = driver.run_par(
                        driver.par_tool.get_tool_hooks() + \
                        driver.tech.get_tech_par_hooks(driver.par_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("Place-and-route tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.par_tool.run_dir, "par-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.par_tool.run_dir, "par-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.par_tool.run_dir, "par-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "drc":
                if not driver.load_drc_tool(get_or_else(self.drc_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.drc_tool is not None, "load_drc_tool was unsuccessful"
                success, output = driver.run_drc(
                        driver.drc_tool.get_tool_hooks() + \
                        driver.tech.get_tech_drc_hooks(driver.drc_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("DRC tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.drc_tool.run_dir, "drc-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.drc_tool.run_dir, "drc-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.drc_tool.run_dir, "drc-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "lvs":
                if not driver.load_lvs_tool(get_or_else(self.lvs_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.lvs_tool is not None, "load_lvs_tool was unsuccessful"
                success, output = driver.run_lvs(
                        driver.lvs_tool.get_tool_hooks() + \
                        driver.tech.get_tech_lvs_hooks(driver.lvs_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("LVS tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.lvs_tool.run_dir, "lvs-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.lvs_tool.run_dir, "lvs-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.lvs_tool.run_dir, "lvs-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "sram_generator":
                if not driver.load_sram_generator_tool(get_or_else(self.sram_generator_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.sram_generator_tool is not None, "load_sram_generator_tool was unsuccessful"
                success, output = driver.run_sram_generator(
                        driver.sram_generator_tool.get_tool_hooks() + \
                        driver.tech.get_tech_sram_generator_hooks(driver.sram_generator_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("SRAM generator tool did not succeed")
                    return None
                post_run_func_checked(driver)
            elif action_type == "sim":
                if not driver.load_sim_tool(get_or_else(self.sim_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.sim_tool is not None, "load_sim_tool was unsuccessful"
                success, output = driver.run_sim(
                        driver.sim_tool.get_tool_hooks() + \
                        driver.tech.get_tech_sim_hooks(driver.sim_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("Sim tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.sim_tool.run_dir, "sim-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.sim_tool.run_dir, "sim-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.sim_tool.run_dir, "sim-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "power":
                if not driver.load_power_tool(get_or_else(self.power_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.power_tool is not None, "load_power_tool was unsuccessful"
                success, output = driver.run_power(extra_hooks)
                if not success:
                    driver.log.error("Power tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.power_tool.run_dir, "power-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.power_tool.run_dir, "power-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.power_tool.run_dir, "power-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "formal":
                if not driver.load_formal_tool(get_or_else(self.formal_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.formal_tool is not None, "load_formal_tool was unsuccessful"
                success, output = driver.run_formal(
                        driver.formal_tool.get_tool_hooks() + \
                        driver.tech.get_tech_formal_hooks(driver.formal_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("Formal tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.formal_tool.run_dir, "formal-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.formal_tool.run_dir, "formal-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.formal_tool.run_dir, "formal-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            elif action_type == "timing":
                if not driver.load_timing_tool(get_or_else(self.timing_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.timing_tool is not None, "load_timing_tool was unsuccessful"
                success, output = driver.run_timing(
                        driver.timing_tool.get_tool_hooks() + \
                        driver.tech.get_tech_timing_hooks(driver.timing_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("Timing tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.timing_tool.run_dir, "timing-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.timing_tool.run_dir, "timing-output-full.json"),
                                         self.get_full_config(driver, output))
                post_run_func_checked(driver)
            elif action_type == "pcb":
                if not driver.load_pcb_tool(get_or_else(self.pcb_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                assert driver.pcb_tool is not None, "load_pcb_tool was unsuccessful"
                success, output = driver.run_pcb(
                        driver.pcb_tool.get_tool_hooks() + \
                        driver.tech.get_tech_pcb_hooks(driver.pcb_tool.name) + \
                        list(extra_hooks or []))
                if not success:
                    driver.log.error("PCB deliverable tool did not succeed")
                    return None
                dump_config_to_json_file(os.path.join(driver.pcb_tool.run_dir, "pcb-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.pcb_tool.run_dir, "pcb-output-full.json"),
                                         self.get_full_config(driver, output))
                if driver.dump_history:
                    dump_config_to_yaml_file(os.path.join(driver.pcb_tool.run_dir, "pcb-output-history.yml"),
                                            add_key_history(self.get_full_config(driver, output), key_history))
                post_run_func_checked(driver)
            else:
                raise ValueError("Invalid action_type = " + str(action_type))
            # TODO: detect errors
            return output

        return action

    def synthesis_to_par_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        par_input_only = HammerDriver.synthesis_output_to_par_input(driver.project_config)
        if par_input_only is None:
            driver.log.error("Input config does not appear to contain valid synthesis outputs")
            return None
        else:
            return self.get_full_config(driver, par_input_only)

    def synthesis_to_sim_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        sim_input_only = HammerDriver.synthesis_output_to_sim_input(driver.project_config)
        if sim_input_only is None:
            driver.log.error("Input config does not appear to contain valid synthesis outputs")
            return None
        else:
            return self.get_full_config(driver, sim_input_only)

    def par_to_sim_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        sim_input_only = HammerDriver.par_output_to_sim_input(driver.project_config)
        if sim_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, sim_input_only)

    def hier_par_to_syn_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """ Create a full config to run the output. """
        syn_input_only = HammerDriver.par_output_to_syn_input(driver.project_config)
        if syn_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, syn_input_only)

    def par_to_drc_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """ Create a full config to run the output. """
        drc_input_only = HammerDriver.par_output_to_drc_input(driver.project_config)
        if drc_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, drc_input_only)

    def par_to_lvs_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """ Create a full config to run the output. """
        lvs_input_only = HammerDriver.par_output_to_lvs_input(driver.project_config)
        if lvs_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, lvs_input_only)

    def syn_to_power_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        power_input_only = HammerDriver.synthesis_output_to_power_input(driver.project_config)
        if power_input_only is None:
            driver.log.error("Input config does not appear to contain valid syn outputs")
            return None
        else:
            return self.get_full_config(driver, power_input_only)

    def par_to_power_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        power_input_only = HammerDriver.par_output_to_power_input(driver.project_config)
        if power_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, power_input_only)

    def sim_to_power_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        power_input_only = HammerDriver.sim_output_to_power_input(driver.project_config)
        if power_input_only is None:
            driver.log.error("Input config does not appear to contain valid sim outputs")
            return None
        else:
            return self.get_full_config(driver, power_input_only)

    def synthesis_to_formal_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        formal_input_only = HammerDriver.synthesis_output_to_formal_input(driver.project_config)
        if formal_input_only is None:
            driver.log.error("Input config does not appear to contain valid synthesis outputs")
            return None
        else:
            return self.get_full_config(driver, formal_input_only)

    def par_to_formal_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        formal_input_only = HammerDriver.par_output_to_formal_input(driver.project_config)
        if formal_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, formal_input_only)

    def synthesis_to_timing_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        timing_input_only = HammerDriver.synthesis_output_to_timing_input(driver.project_config)
        if timing_input_only is None:
            driver.log.error("Input config does not appear to contain valid synthesis outputs")
            return None
        else:
            return self.get_full_config(driver, timing_input_only)

    def par_to_timing_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a full config to run the output."""
        timing_input_only = HammerDriver.par_output_to_timing_input(driver.project_config)
        if timing_input_only is None:
            driver.log.error("Input config does not appear to contain valid par outputs")
            return None
        else:
            return self.get_full_config(driver, timing_input_only)


    def create_synthesis_par_action(self, synthesis_action: CLIActionConfigType, par_action: CLIActionConfigType) -> CLIActionConfigType:
        """
        Create a parameterizable synthesis_par action for the CLIDriver.

        :param synthesis_action: synthesis action
        :param par_action: par action
        :return: Custom synthesis_par action
        """

        def syn_par_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
            # Synthesis output.
            syn_output = synthesis_action(driver, append_error_func)
            if syn_output is None:
                append_error_func("Synthesis action in syn_par failed")
                return None
            else:
                # Generate place-and-route input from the synthesis output.
                syn_output_converted = HammerDriver.synthesis_output_to_par_input(syn_output)
                assert syn_output_converted is not None, "syn_output must be generated by CLIDriver"
                par_input = self.get_full_config(driver, syn_output_converted)  # type: dict

                # Dump both synthesis output and par input for debugging/resuming.
                # TODO(edwardw): make these output filenames configurable?
                assert driver.syn_tool is not None, "Syn tool must exist since we ran synthesis_action successfully"
                dump_config_to_json_file(os.path.join(driver.syn_tool.run_dir, "par-input.json"), par_input)

                # Use new par input and run place-and-route.
                driver.update_project_configs([par_input])
                par_output = par_action(driver, append_error_func)
                return par_output

        return syn_par_action

    def create_synthesis_sim_action(self, synthesis_action: CLIActionConfigType, sim_action: CLIActionConfigType) -> CLIActionConfigType:
        """
        Create a parameterizable synthesis_sim action for the CLIDriver.

        :param synthesis_action: synthesis action
        :param sim_action: sim action
        :return: Custom synthesis_sim action
        """

        def syn_sim_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
            # Synthesis output.
            syn_output = synthesis_action(driver, append_error_func)
            if syn_output is None:
                append_error_func("Synthesis action in syn_sim failed")
                return None
            else:
                # Generate sim input from the synthesis output.
                syn_output_converted = HammerDriver.synthesis_output_to_sim_input(syn_output)
                assert syn_output_converted is not None, "syn_output must be generated by CLIDriver"
                sim_input = self.get_full_config(driver, syn_output_converted)  # type: dict

                # Dump both synthesis output and sim input for debugging/resuming.
                assert driver.syn_tool is not None, "Syn tool must exist since we ran synthesis_action successfully"
                dump_config_to_json_file(os.path.join(driver.syn_tool.run_dir, "sim-input.json"), sim_input)

                # Use new sim input and run simulation.
                driver.update_project_configs([sim_input])
                sim_output = sim_action(driver, append_error_func)
                return sim_output

        return syn_sim_action

    def create_par_sim_action(self, par_action: CLIActionConfigType, sim_action: CLIActionConfigType) -> CLIActionConfigType:
        """
        Create a parameterizable par_sim action for the CLIDriver.

        :param par_action: par action
        :param sim_action: sim action
        :return: Custom par_sim action
        """

        def par_sim_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
            # Synthesis output.
            par_output = par_action(driver, append_error_func)
            if par_output is None:
                append_error_func("PAR action in syn_sim failed")
                return None
            else:
                # Generate sim input from the par output.
                par_output_converted = HammerDriver.par_output_to_sim_input(par_output)
                assert par_output_converted is not None, "par_output must be generated by CLIDriver"
                sim_input = self.get_full_config(driver, par_output_converted)  # type: dict

                # Dump both par output and sim input for debugging/resuming.
                assert driver.par_tool is not None, "PAR tool must exist since we ran par_action successfully"
                dump_config_to_json_file(os.path.join(driver.par_tool.run_dir, "sim-input.json"), sim_input)

                # Use new sim input and run simulation.
                driver.update_project_configs([sim_input])
                sim_output = sim_action(driver, append_error_func)
                return sim_output

        return par_sim_action

    ### Hierarchical stuff ###
    @property
    def all_hierarchical_actions(self) -> Dict[str, CLIActionConfigType]:
        """
        Return a list of hierarchical actions if the given project configuration is a hierarchical design.
        Set when the driver is first created in args_to_driver.
        Create syn/synthesis-[block], par-[block], and /syn_par-[block].

        :return: Dictionary of actions to use (could be empty).
        """
        actions = {}  # type: Dict[str, CLIActionConfigType]
        if self.hierarchical_auto_action is not None:
            actions.update({"auto": self.hierarchical_auto_action})

        def add_variants(templates: List[str], block: str, action: CLIActionConfigType) -> None:
            """Just add the given action using the name templates."""
            for template in templates:
                name = template.format(block=block)
                actions.update({name: action})

        for module, action in self.hierarchical_synthesis_actions.items():
            add_variants([
                "syn-{block}",
                "synthesis-{block}",
                "syn_{block}",
                "synthesis_{block}"
            ], module, action)

        for module, action in self.hierarchical_par_actions.items():
            add_variants([
                "par-{block}",
                "par_{block}"
            ], module, action)

        for module, action in self.hierarchical_synthesis_par_actions.items():
            add_variants([
                "syn-par-{block}",
                "syn_par-{block}",
                "syn-par_{block}",
                "syn_par_{block}"
            ], module, action)

        for module, action in self.hierarchical_drc_actions.items():
            add_variants([
                "drc-{block}",
                "drc_{block}"
            ], module, action)

        for module, action in self.hierarchical_lvs_actions.items():
            add_variants([
                "lvs-{block}",
                "lvs_{block}"
            ], module, action)

        for module, action in self.hierarchical_sim_actions.items():
            add_variants([
                "sim-{block}",
                "sim_{block}"
            ], module, action)

        for module, action in self.hierarchical_power_actions.items():
            add_variants([
                "power-{block}",
                "power_{block}"
            ], module, action)

        for module, action in self.hierarchical_formal_actions.items():
            add_variants([
                "formal-{block}",
                "formal_{block}"
            ], module, action)

        for module, action in self.hierarchical_timing_actions.items():
            add_variants([
                "timing-{block}",
                "timing_{block}"
            ], module, action)

        return actions

    def get_extra_hierarchical_synthesis_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical synthesis hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_par_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical place and route hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_drc_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical DRC hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_lvs_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical LVS hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_sim_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical sim hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_power_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical power hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_formal_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical formal hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_timing_hooks(self, driver: HammerDriver) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical timing hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    # The following functions are present for further user customizability.

    def get_hierarchical_synthesis_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical synthesis for the given module (in hierarchical flows).
        """
        return self.hierarchical_synthesis_actions[module]

    def set_hierarchical_synthesis_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical synthesis for the given module (in hierarchical flows).
        """
        self.hierarchical_synthesis_actions[module] = action

    def get_hierarchical_par_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical par for the given module (in hierarchical flows).
        """
        return self.hierarchical_par_actions[module]

    def set_hierarchical_par_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical par for the given module (in hierarchical flows).
        """
        self.hierarchical_par_actions[module] = action

    def set_hierarchical_drc_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical drc for the given module (in hierarchical flows).
        """
        self.hierarchical_drc_actions[module] = action

    def get_hierarchical_drc_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical drc for the given module (in hierarchical flows).
        """
        return self.hierarchical_drc_actions[module]

    def set_hierarchical_lvs_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical lvs for the given module (in hierarchical flows).
        """
        self.hierarchical_lvs_actions[module] = action

    def get_hierarchical_lvs_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical lvs for the given module (in hierarchical flows).
        """
        return self.hierarchical_lvs_actions[module]

    def get_hierarchical_synthesis_par_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical syn_par for the given module (in hierarchical flows).
        """
        return self.hierarchical_synthesis_par_actions[module]

    def set_hierarchical_synthesis_par_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical syn_par for the given module (in hierarchical flows).
        """
        self.hierarchical_synthesis_par_actions[module] = action

    def set_hierarchical_sim_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical sim for the given module (in hierarchical flows).
        """
        self.hierarchical_sim_actions[module] = action

    def get_hierarchical_sim_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical sim for the given module (in hierarchical flows).
        """
        return self.hierarchical_sim_actions[module]

    def set_hierarchical_power_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical power for the given module (in hierarchical flows).
        """
        self.hierarchical_power_actions[module] = action

    def get_hierarchical_power_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical power for the given module (in hierarchical flows).
        """
        return self.hierarchical_power_actions[module]

    def set_hierarchical_formal_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical formal for the given module (in hierarchical flows).
        """
        self.hierarchical_formal_actions[module] = action

    def get_hierarchical_formal_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical formal for the given module (in hierarchical flows).
        """
        return self.hierarchical_formal_actions[module]

    def set_hierarchical_timing_action(self, module: str, action: CLIActionConfigType) -> None:
        """
        Set the action associated with hierarchical timing for the given module (in hierarchical flows).
        """
        self.hierarchical_timing_actions[module] = action

    def get_hierarchical_timing_action(self, module: str) -> CLIActionConfigType:
        """
        Get the action associated with hierarchical timing for the given module (in hierarchical flows).
        """
        return self.hierarchical_timing_actions[module]

    def valid_actions(self) -> List[str]:
        """Get the list of valid actions for the command-line driver."""
        return list(self.action_map().keys())

    def args_to_driver(self, args: dict,
                       default_options: Optional[HammerDriverOptions] = None) -> \
            Tuple[HammerDriver, List[str]]:
        """Parse command line arguments and environment variables for the command line front-end to hammer-vlsi.

        :return: HammerDriver and a list of errors."""

        # TODO: rewrite this less tediously?

        # Resolve default_options.
        # Can't call HammerDriver.get_default_driver_options in the
        # parameters as it will be called when args_to_driver is defined
        default_options_resolved = HammerDriver.get_default_driver_options()  # type: HammerDriverOptions
        if default_options is not None:
            default_options_resolved = default_options

        # Driver options.
        options = default_options_resolved  # type: HammerDriverOptions

        # Extra config (flattened JSON).
        config = {}  # type: Dict[str, Any]

        # Create a list of errors for the user.
        errors = []  # type: List[str]

        # Load environment configs.
        env_configs = parse_optional_file_list_from_args(args['environment_config'],
                                                         append_error_func=errors.append)  # type: List[str]
        # Also load any environment configs from the environment.
        split_env_var_s = os.environ.get("HAMMER_ENVIRONMENT_CONFIGS", default="").split(os.pathsep)  # type: List[str]
        # "".split(':') returns [''], so we need to catch this case and return an empty list as intended.
        split_env_var = [] if split_env_var_s == [''] else split_env_var_s  # type: List[str]
        env_config_environment_var = parse_optional_file_list_from_args(split_env_var,
                                                                        append_error_func=errors.append)  # type: List[str]
        for extra_path in env_config_environment_var:
            env_configs.append(extra_path)
        options = options._replace(environment_configs=list(env_configs))

        # Load project configs.
        project_configs = parse_optional_file_list_from_args(args['configs'], append_error_func=errors.append)
        options = options._replace(project_configs=list(project_configs))

        # Log file.
        log = args["log"]
        if log is not None:
            if isinstance(log, str):
                options = options._replace(log_file=log)
            else:
                errors.append("Log file 'log' is not a string")

        # Verilog inputs.
        # (optional, since it can also be specified from JSON)
        verilogs = args['verilog']
        if isinstance(verilogs, List) and len(verilogs) > 0:
            config.update({'synthesis.inputs.input_files': list(verilogs)})

        # Top module.
        # (optional, since it can also be specified from JSON)
        top_module = get_nonempty_str(args['top'])
        if top_module is not None:
            config['synthesis.inputs.top_module'] = top_module

        # Object dir.
        # (optional)
        obj_dir = get_nonempty_str(args['obj_dir'])
        if obj_dir is None:
            # Try getting object dir from environment variable.
            obj_dir = get_nonempty_str(os.environ.get("HAMMER_DRIVER_OBJ_DIR", ""))
        if obj_dir is not None:
            options = options._replace(obj_dir=os.path.realpath(obj_dir))
        # Syn/par rundir (optional)
        self.syn_rundir = get_nonempty_str(args['syn_rundir'])
        self.par_rundir = get_nonempty_str(args['par_rundir'])
        self.drc_rundir = get_nonempty_str(args['drc_rundir'])
        self.lvs_rundir = get_nonempty_str(args['lvs_rundir'])
        self.sim_rundir = get_nonempty_str(args['sim_rundir'])
        self.power_rundir = get_nonempty_str(args['power_rundir'])
        self.formal_rundir = get_nonempty_str(args['formal_rundir'])
        self.timing_rundir = get_nonempty_str(args['timing_rundir'])

        # Intercept keys for determining key origin
        project_configs_yaml: List[dict] = []
        for conf_file in project_configs:
            config_str = Path(conf_file).read_text()
            project_configs_yaml.append(hammer.config.load_config_from_string(config_str, is_yaml=True, path=str(Path(conf_file).resolve().parent)))
        project_configs_yaml_keys = [set(i.keys()) for i in project_configs_yaml]
        key_history: Dict[str, List[str]] = {i: [] for i in reduce(lambda x, y: x.union(y), project_configs_yaml_keys)}
        for cfg_file, cfg in zip(project_configs, project_configs_yaml_keys):
            for key in cfg:
                key_history[key].append(cfg_file)
        with open(KEY_PATH, 'w') as f:
            json.dump(key_history, f)

        # Stage control: from/to
        from_step = get_nonempty_str(args['from_step'])
        after_step = get_nonempty_str(args['after_step'])
        to_step = get_nonempty_str(args['to_step'])
        until_step = get_nonempty_str(args['until_step'])
        only_step = get_nonempty_str(args['only_step'])

        if from_step is not None and after_step is not None:
            errors.append("Specified both start_before_step and start_after_step. start_before_step will take precedence.")
        if to_step is not None and until_step is not None:
            errors.append("Specified both stop_after_step and stop_before_step. stop_after_step will take precedence.")
        if only_step is not None and any(s is not None for s in [from_step, after_step, to_step, until_step]):
            errors.append("Specified {start|stop}_{before_after}_step with only_step. only_step will take precedence.")
        if (from_step is not None and until_step is not None and from_step == until_step) or \
           (after_step is not None and to_step is not None and after_step == to_step) or \
           (after_step is not None and until_step is not None and after_step == until_step):
            errors.append("Caution: start_before_step == stop_before_step, start_after_step == stop_after_step, or start_after_step == stop_before_step will result in nothing being run")

        driver = HammerDriver(options, config)

        start_step = only_step or from_step or after_step or None
        start_incl = (only_step or from_step) is not None
        stop_step = only_step or to_step or until_step or None
        stop_incl = (only_step or to_step) is not None
        if (start_step or stop_step) is not None:
            driver.set_post_custom_syn_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_par_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_drc_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_lvs_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_sim_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_power_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_formal_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))
            driver.set_post_custom_timing_tool_hooks(HammerTool.make_start_stop_hooks(
                HammerStartStopStep(step=start_step, inclusive=start_incl),
                HammerStartStopStep(step=stop_step, inclusive=stop_incl)))

        # Hierarchical support.
        # Generate synthesis and par actions for each module above.
        hierarchical_settings = driver.get_hierarchical_settings()

        for module_iter, config_iter in hierarchical_settings:
            def create_actions(module: str, config: dict) -> None:
                # Create a new context (this def) per module, otherwise when these higher-order funcs run they'll all
                # use the last iteration of the loop.

                # TODO(edwardw): this is a bit of a hack.
                # Should really add an API to allow a run to have a bit of temporary project config
                base_project_config = [[]]  # type: List[List[dict]]

                def syn_pre_func(d: HammerDriver) -> None:
                    self.syn_rundir = os.path.join(d.obj_dir, "syn-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def par_pre_func(d: HammerDriver) -> None:
                    self.par_rundir = os.path.join(d.obj_dir, "par-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def drc_pre_func(d: HammerDriver) -> None:
                    self.drc_rundir = os.path.join(d.obj_dir, "drc-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def lvs_pre_func(d: HammerDriver) -> None:
                    self.lvs_rundir = os.path.join(d.obj_dir, "lvs-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def sim_pre_func(d: HammerDriver) -> None:
                    self.lvs_rundir = os.path.join(d.obj_dir, "sim-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def power_pre_func(d: HammerDriver) -> None:
                    self.lvs_rundir = os.path.join(d.obj_dir, "power-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def formal_pre_func(d: HammerDriver) -> None:
                    self.lvs_rundir = os.path.join(d.obj_dir, "formal-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def timing_pre_func(d: HammerDriver) -> None:
                    self.lvs_rundir = os.path.join(d.obj_dir, "timing-{module}".format(
                        module=module))  # TODO(edwardw): fix this ugly os.path.join; it doesn't belong here.
                    # TODO(edwardw): remove ugly hack to store stuff in parent context
                    base_project_config[0] = deeplist(driver.project_configs)
                    d.update_project_configs(deeplist(base_project_config[0]) + [config])

                def post_run(d: HammerDriver, rundir: str) -> None:
                    # Write out the configs used/generated for logging/debugging.
                    with open(os.path.join(rundir, "full_config.json"), "w") as f:
                        new_output_json = json.dumps(d.project_config, cls=HammerJSONEncoder, indent=4)
                        f.write(new_output_json)
                    with open(os.path.join(rundir, "module_config.json"), "w") as f:
                        new_output_json = json.dumps(config, cls=HammerJSONEncoder, indent=4)
                        f.write(new_output_json)

                    d.update_project_configs(deeplist(base_project_config[0]))

                def syn_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.syn_rundir, ""))

                def par_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.par_rundir, ""))

                def drc_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.drc_rundir, ""))

                def lvs_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.lvs_rundir, ""))

                def sim_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.sim_rundir, ""))

                def power_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.power_rundir, ""))

                def formal_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.formal_rundir, ""))

                def timing_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.timing_rundir, ""))

                syn_action = self.create_synthesis_action(self.get_extra_hierarchical_synthesis_hooks(driver).get(module, []),
                                                          pre_action_func=syn_pre_func, post_load_func=None,
                                                          post_run_func=syn_post_run)
                self.set_hierarchical_synthesis_action(module, syn_action)
                par_action = self.create_par_action(self.get_extra_hierarchical_par_hooks(driver).get(module, []),
                                                    pre_action_func=par_pre_func, post_load_func=None,
                                                    post_run_func=par_post_run)
                self.set_hierarchical_par_action(module, par_action)
                syn_par_action = self.create_synthesis_par_action(synthesis_action=syn_action, par_action=par_action)
                self.set_hierarchical_synthesis_par_action(module, syn_par_action)
                drc_action = self.create_drc_action(self.get_extra_hierarchical_drc_hooks(driver).get(module, []),
                                                    pre_action_func=drc_pre_func, post_load_func=None,
                                                    post_run_func=drc_post_run)
                self.set_hierarchical_drc_action(module, drc_action)
                lvs_action = self.create_lvs_action(self.get_extra_hierarchical_lvs_hooks(driver).get(module, []),
                                                    pre_action_func=lvs_pre_func, post_load_func=None,
                                                    post_run_func=lvs_post_run)
                self.set_hierarchical_lvs_action(module, lvs_action)
                sim_action = self.create_sim_action(self.get_extra_hierarchical_sim_hooks(driver).get(module, []),
                                                    pre_action_func=sim_pre_func, post_load_func=None,
                                                    post_run_func=sim_post_run)
                self.set_hierarchical_sim_action(module, sim_action)
                power_action = self.create_power_action(self.get_extra_hierarchical_power_hooks(driver).get(module, []),
                                                    pre_action_func=power_pre_func, post_load_func=None,
                                                    post_run_func=power_post_run)
                self.set_hierarchical_power_action(module, power_action)
                formal_action = self.create_formal_action(self.get_extra_hierarchical_formal_hooks(driver).get(module, []),
                                                    pre_action_func=formal_pre_func, post_load_func=None,
                                                    post_run_func=formal_post_run)
                self.set_hierarchical_formal_action(module, formal_action)
                timing_action = self.create_timing_action(self.get_extra_hierarchical_timing_hooks(driver).get(module, []),
                                                    pre_action_func=timing_pre_func, post_load_func=None,
                                                    post_run_func=timing_post_run)
                self.set_hierarchical_timing_action(module, timing_action)

            create_actions(module_iter, config_iter)

        # If we are in hierarchical mode, also generate an auto that can run the whole flow.
        if len(hierarchical_settings) > 0:
            def auto_action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
                log = driver.log.context("CLIDriver_auto")
                output = {}  # type: dict

                # Run syn_par for every module.
                for module, _ in hierarchical_settings:
                    syn_par_action = self.get_hierarchical_synthesis_par_action(module)
                    new_output = syn_par_action(driver, append_error_func)

                    if new_output is None:
                        log.error("Hierarchical syn-par run for module {module} failed".format(module=module))
                        return None
                    else:
                        log.info("Hierarchical syn-par run for module {module} finished".format(module=module))

                    b, ext = os.path.splitext(args["output"])
                    new_output_filename = "{base}-{module}{ext}".format(base=b, module=module, ext=ext)
                    with open(new_output_filename, "w") as f:
                        new_output_json = json.dumps(new_output, cls=HammerJSONEncoder, indent=4)
                        f.write(new_output_json)
                    log.info("Output JSON: " + str(new_output))

                    new_ilm = {
                        "vlsi.inputs.ilms": new_output["par.outputs.output_ilms"],
                        "vlsi.inputs.ilms_meta": "append"
                    }
                    new_ilm_filename = "{base}-{module}_ilm{ext}".format(base=b, module=module, ext=ext)
                    with open(new_ilm_filename, "w") as f:
                        json_content = json.dumps(new_ilm, cls=HammerJSONEncoder, indent=4)
                        f.write(json_content)
                    log.info("New input ILM JSON written to " + new_ilm_filename)
                    driver.update_project_configs(driver.project_configs + [new_ilm])
                return output

            self.hierarchical_auto_action = auto_action

        driver.dump_history = args["dump_history"]

        return driver, errors

    @staticmethod
    def generate_build_inputs(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """
        Generate the build tool artifacts for this flow, specified by the "vlsi.core.build_system" key.
        The flow is the set of steps configured by the current HammerIR input.

        :param driver: The HammerDriver object which has parsed the configs specified by -p
        :param append_error_func: The function to use to append an error
        :return: The diplomacy graph
        """
        build_system = str(driver.database.get_setting("vlsi.core.build_system", "none"))
        if build_system in BuildSystems:
            return BuildSystems[build_system](driver, append_error_func)
        else:
            raise ValueError("Unsupported build system: {}".format(build_system))

    def run_main_parsed(self, args: dict) -> int:
        """
        Given a parsed dictionary of arguments, find and run the given action.

        :return: Return code (0 for success)
        """
        if args['firrtl'] is not None and len(args['firrtl']) > 0:
            print("firrtl convenience argument not yet implemented", file=sys.stderr)
            return 1

        driver, errors = self.args_to_driver(args)

        # Check for action after creating the driver (e.g. for custom actions like hierarchical actions).
        action = str(args['action'])  # type: str
        if action not in self.valid_actions():
            print("Invalid action {action}".format(action=action), file=sys.stderr)
            print("Valid actions are: {actions}".format(actions=", ".join(self.valid_actions())), file=sys.stderr)
            return 1

        action_func = self.action_map()[action]
        output_str = None  # type: Optional[str]
        if is_config_action(action_func):
            action_func = cast(CLIActionConfigType, action_func)
            output_config = action_func(driver, errors.append)  # type: Optional[dict]
            if output_config is not None:
                output_str = json.dumps(output_config, cls=HammerJSONEncoder, indent=4)
        elif is_string_action(action_func):
            action_func = cast(CLIActionStringType, action_func)
            output_str = action_func(driver, errors.append)
        else:
            raise NotImplementedError("Invalid action function")
        if output_str is None:
            print("Action {action} failed with errors".format(action=action), file=sys.stderr)
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        else:
            with open(args["output"], "w") as f:
                f.write(output_str)
            print("Action {action} config output written to {file}".format(action=action, file=args["output"]))
            return 0


    def main(self, args: Optional[List[str]] = None) -> None:
        """
        Main function to call from your entry point script.
        Parses command line arguments.
        :param args: Custom command-line arguments.  If not given, sys.argv[1:] will be used.
        Example:
        >>> if __name__ == '__main__':
        >>>   CLIDriver().main()
        """
        parser = argparse.ArgumentParser()

        parser.add_argument('action', metavar='ACTION', type=str,  # choices=self.valid_actions() <- sadly incompatible w/custom actions
                            help='Action to perform with the command-line driver.')
        # Required arguments for (Python) hammer driver.
        parser.add_argument("-e", "--environment_config", action='append', required=False,
                            help="Environment config files (.yml or .json) - .json will take precendence over any .yml. These config files will not be re-emitted in the output json. Can also be specified as a colon-separated list in the environment variable HAMMER_ENVIRONMENT_CONFIGS.")
        parser.add_argument("-p", "--project_config", action='append', dest="configs", type=str,
                            help='Project config files (.yml or .json).')
        parser.add_argument("-l", "--log", required=False,
                            help='Log file. Leave blank to automatically create one.')
        parser.add_argument("--obj_dir", required=False,
                            help='Folder for storing results of CAD tool runs. If not specified, this will be the hammer-vlsi folder by default. Can also be specified via the environment variable HAMMER_DRIVER_OBJ_DIR.')
        parser.add_argument("--syn_rundir", required=False, default="",
                            help='(optional) Directory to store syn results in')
        parser.add_argument("--par_rundir", required=False, default="",
                            help='(optional) Directory to store par results in')
        parser.add_argument("--drc_rundir", required=False, default="",
                            help='(optional) Directory to store DRC results in')
        parser.add_argument("--lvs_rundir", required=False, default="",
                            help='(optional) Directory to store LVS results in')
        parser.add_argument("--sim_rundir", required=False, default="",
                            help='(optional) Directory to store simulation results in')
        parser.add_argument("--power_rundir", required=False, default="",
                            help='(optional) Directory to store power results in')
        parser.add_argument("--formal_rundir", required=False, default="",
                            help='(optional) Directory to store formal results in')
        parser.add_argument("--timing_rundir", required=False, default="",
                            help='(optional) Directory to store timing results in')
        # Optional arguments for step control.
        parser.add_argument("--start_before_step", "--from_step", dest="from_step", required=False,
                            help="Run the given action from before the given step (inclusive). Not compatible with --start_after_step.")
        parser.add_argument("--start_after_step", "--after_step", dest="after_step", required=False,
                            help="Run the given action from after the given step (exclusive). Not compatible with --start_before_step.")
        parser.add_argument("--stop_after_step", "--to_step", dest="to_step", required=False,
                            help="Run the given action to the given step (inclusive). Not compatible with --stop_before_step.")
        parser.add_argument("--stop_before_step", "--until_step", dest="until_step", required=False,
                            help="Run the given action until the given step (exclusive). Not compatible with --stop_after_step.")
        parser.add_argument("--only_step", dest="only_step", required=False,
                            help="Run only the given step. Not compatible with --{start|stop}_{before|after}_step.")
        # Required arguments for CLI hammer driver.
        parser.add_argument("-o", "--output", default="output.json", required=False,
                            help='Output JSON file for results and modular use of hammer-vlsi. Default: output.json.')
        # Optional arguments (depending on context)
        parser.add_argument("-v", "--verilog", required=False, action='append',
                            help='Input set of Verilog files.')
        parser.add_argument("-f", "--firrtl", action='append', required=False,
                            help='Input set of firrtl files. Provided for convenience; hammer-vlsi will transform it to Verilog.')
        parser.add_argument("-t", "--top", required=False,
                            help='Top module. If not specified, hammer-vlsi will take it from synthesis.inputs.top_module.')
        parser.add_argument("--cad-files", action='append', required=False,
                            help="CAD files.")
        parser.add_argument("--dump-history", default=False, action=argparse.BooleanOptionalAction,
                            help='Option to dump the key history of all the project configurations.')

        try:
            output = subprocess.check_output(["hammer-shell-test"]).decode().strip()
        except FileNotFoundError:
            output = "File not found"
        except PermissionError as e:
            output = str(e.args[0]) + " " + e.args[1]
        if output != "hammer-shell appears to be on the path":
            print("hammer-shell does not appear to be on the path (hammer-shell-test failed to run: %s)" % (output),
                  file=sys.stderr)
            sys.exit(1)

        sys.exit(self.run_main_parsed(vars(parser.parse_args(args))))
