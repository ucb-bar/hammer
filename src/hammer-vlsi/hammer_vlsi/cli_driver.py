#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  cli_driver.py
#  
#  Copyright 2017-2018 Edward Wang <edward.c.wang@compdigitec.com>
#
#  CLI driver class for the Hammer VLSI abstraction.

import argparse
import json
import os
import subprocess
import sys

from .hammer_vlsi_impl import HammerTool, HammerVLSISettings
from .hooks import HammerToolHookAction
from .driver import HammerDriver, HammerDriverOptions

from typing import List, Dict, Tuple, Any, Callable, Optional

from hammer_utils import add_dicts, deeplist, deepdict, get_or_else, check_function_type


def parse_optional_file_list_from_args(args_list: Any, append_error_func: Callable[[str], None]) -> List[str]:
    """Parse a possibly null list of files, validate the existence of each file, and return a list of paths (possibly
    empty)."""
    results = []  # type: List[str]
    if args_list is None:
        # No arguments
        pass
    elif isinstance(args_list, List):
        for c in args_list:
            if not os.path.exists(c):
                append_error_func("Given path %s does not exist!" % c)
        results = list(args_list)
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
        f.write(json.dumps(config, indent=4))


# Type signature of a CLIDriver action.
CLIActionType = Callable[[HammerDriver, Callable[[str], None]], Optional[dict]]


def check_CLIActionType_type(func: CLIActionType) -> None:
    """
    Check that the given CLIActionType obeys its function type signature.
    Raises TypeError if the function is of the incorrect type.
    """
    check_function_type(func, [HammerDriver, Callable[[str], None]], Optional[dict])


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

        # If a subclass has defined these, don't clobber them in init
        # since the subclass still uses this init function.
        if hasattr(self, "synthesis_action"):
            check_CLIActionType_type(self.synthesis_action)  # type: ignore
        else:
            self.synthesis_action = self.create_synthesis_action([])  # type: CLIActionType
        if hasattr(self, "par_action"):
            check_CLIActionType_type(self.par_action)  # type: ignore
        else:
            self.par_action = self.create_par_action([])  # type: CLIActionType
        if hasattr(self, "synthesis_par_action"):
            check_CLIActionType_type(self.synthesis_par_action)  # type: ignore
        else:
            self.synthesis_par_action = self.create_synthesis_par_action(self.synthesis_action, self.par_action)  # type: CLIActionType

        # Dictionaries of module-CLIActionType for hierarchical flows.
        # See all_hierarchical_actions() below.
        self.hierarchical_synthesis_actions = {}  # type: Dict[str, CLIActionType]
        self.hierarchical_par_actions = {}  # type: Dict[str, CLIActionType]
        self.hierarchical_synthesis_par_actions = {}  # type: Dict[str, CLIActionType]
        self.hierarchical_auto_action = None  # type: Optional[CLIActionType]

    def action_map(self) -> Dict[str, CLIActionType]:
        """Return the mapping of valid actions -> functions for each action of the command-line driver."""
        return add_dicts({
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
            "syn-par": self.synthesis_par_action
        }, self.all_hierarchical_actions)

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

    def create_synthesis_action(self, custom_hooks: List[HammerToolHookAction],
                                pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                                post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                                post_run_func: Optional[Callable[[HammerDriver], None]] = None
                                ) -> CLIActionType:
        hooks = self.get_extra_synthesis_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("synthesis", hooks if len(hooks) > 0 else None,
                                  pre_action_func, post_load_func, post_run_func)

    def create_par_action(self, custom_hooks: List[HammerToolHookAction],
                          pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                          post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionType:
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

    def create_action(self, action_type: str,
                      extra_hooks: Optional[List[HammerToolHookAction]],
                      pre_action_func: Optional[Callable[[HammerDriver], None]] = None,
                      post_load_func: Optional[Callable[[HammerDriver], None]] = None,
                      post_run_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionType:
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
            if action_type == "synthesis" or action_type == "syn":
                if not driver.load_synthesis_tool(get_or_else(self.syn_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                success, output = driver.run_synthesis(extra_hooks)
                dump_config_to_json_file(os.path.join(driver.syn_tool.run_dir, "syn-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.syn_tool.run_dir, "syn-output-full.json"),
                                         self.get_full_config(driver, output))
                post_run_func_checked(driver)
            elif action_type == "par":
                if not driver.load_par_tool(get_or_else(self.par_rundir, "")):
                    return None
                else:
                    post_load_func_checked(driver)
                success, output = driver.run_par(extra_hooks)
                dump_config_to_json_file(os.path.join(driver.par_tool.run_dir, "par-output.json"), output)
                dump_config_to_json_file(os.path.join(driver.par_tool.run_dir, "par-output-full.json"),
                                         self.get_full_config(driver, output))
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

    def create_synthesis_par_action(self, synthesis_action: CLIActionType, par_action: CLIActionType) -> CLIActionType:
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
                assert syn_output_converted is not None, "syn_output was generated by CLIDriver"
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

    ### Hierarchical stuff ###
    @property
    def all_hierarchical_actions(self) -> Dict[str, CLIActionType]:
        """
        Return a list of hierarchical actions if the given project configuration is a hierarchical design.
        Set when the driver is first created in args_to_driver.
        Create syn/synthesis-[block], par-[block], and /syn_par-[block].

        :return: Dictionary of actions to use (could be empty).
        """
        actions = {}  # type: Dict[str, CLIActionType]
        if self.hierarchical_auto_action is not None:
            actions.update({"auto": self.hierarchical_auto_action})

        def add_variants(templates: List[str], block: str, action: CLIActionType) -> None:
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

        return actions

    def get_extra_hierarchical_synthesis_hooks(self) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical synthesis hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    def get_extra_hierarchical_par_hooks(self) -> Dict[str, List[HammerToolHookAction]]:
        """
        Return a list of extra hierarchical place and route hooks in this project.
        To be overridden by subclasses.

        :return: Dictionary of (module name, list of hooks)
        """
        return dict()

    # The following functions are present for further user customizability.

    def get_hierarchical_synthesis_action(self, module: str) -> CLIActionType:
        """
        Get the action associated with hierarchical synthesis for the given module (in hierarchical flows).
        """
        return self.hierarchical_synthesis_actions[module]

    def set_hierarchical_synthesis_action(self, module: str, action: CLIActionType) -> None:
        """
        Set the action associated with hierarchical synthesis for the given module (in hierarchical flows).
        """
        self.hierarchical_synthesis_actions[module] = action

    def get_hierarchical_par_action(self, module: str) -> CLIActionType:
        """
        Get the action associated with hierarchical par for the given module (in hierarchical flows).
        """
        return self.hierarchical_par_actions[module]

    def set_hierarchical_par_action(self, module: str, action: CLIActionType) -> None:
        """
        Set the action associated with hierarchical par for the given module (in hierarchical flows).
        """
        self.hierarchical_par_actions[module] = action

    def get_hierarchical_synthesis_par_action(self, module: str) -> CLIActionType:
        """
        Get the action associated with hierarchical syn_par for the given module (in hierarchical flows).
        """
        return self.hierarchical_synthesis_par_actions[module]

    def set_hierarchical_synthesis_par_action(self, module: str, action: CLIActionType) -> None:
        """
        Set the action associated with hierarchical syn_par for the given module (in hierarchical flows).
        """
        self.hierarchical_synthesis_par_actions[module] = action

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
        # parameters as it will be called when args_to_driver is defined, and
        # hammer_vlsi_path will not be defined yet.
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
            options = options._replace(obj_dir=obj_dir)
        # Syn/par rundir (optional)
        self.syn_rundir = get_nonempty_str(args['syn_rundir'])
        self.par_rundir = get_nonempty_str(args['par_rundir'])

        # Stage control: from/to
        from_step = get_nonempty_str(args['from_step'])
        to_step = get_nonempty_str(args['to_step'])
        only_step = get_nonempty_str(args['only_step'])

        driver = HammerDriver(options, config)
        if from_step is not None or to_step is not None:
            driver.set_post_custom_syn_tool_hooks(HammerTool.make_from_to_hooks(from_step, to_step))
            driver.set_post_custom_par_tool_hooks(HammerTool.make_from_to_hooks(from_step, to_step))
            if only_step is not None:
                errors.append("Cannot specify from_step/to_step and only_step")
        else:
            if only_step is not None:
                driver.set_post_custom_syn_tool_hooks(HammerTool.make_from_to_hooks(only_step, only_step))
                driver.set_post_custom_par_tool_hooks(HammerTool.make_from_to_hooks(only_step, only_step))

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

                def post_run(d: HammerDriver, rundir: str) -> None:
                    # Write out the configs used/generated for logging/debugging.
                    with open(os.path.join(rundir, "full_config.json"), "w") as f:
                        new_output_json = json.dumps(d.project_config, indent=4)
                        f.write(new_output_json)
                    with open(os.path.join(rundir, "module_config.json"), "w") as f:
                        new_output_json = json.dumps(config, indent=4)
                        f.write(new_output_json)

                    d.update_project_configs(deeplist(base_project_config[0]))

                def syn_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.syn_rundir, ""))

                def par_post_run(d: HammerDriver) -> None:
                    post_run(d, get_or_else(self.par_rundir, ""))

                syn_action = self.create_synthesis_action(self.get_extra_hierarchical_synthesis_hooks().get(module, []),
                                                          pre_action_func=syn_pre_func, post_load_func=None,
                                                          post_run_func=syn_post_run)
                self.set_hierarchical_synthesis_action(module, syn_action)
                par_action = self.create_par_action(self.get_extra_hierarchical_par_hooks().get(module, []),
                                                    pre_action_func=par_pre_func, post_load_func=None,
                                                    post_run_func=par_post_run)
                self.set_hierarchical_par_action(module, par_action)
                syn_par_action = self.create_synthesis_par_action(synthesis_action=syn_action, par_action=par_action)
                self.set_hierarchical_synthesis_par_action(module, syn_par_action)

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
                        new_output_json = json.dumps(new_output, indent=4)
                        f.write(new_output_json)
                    log.info("Output JSON: " + str(new_output))

                    new_ilm = {
                        "vlsi.inputs.ilms": new_output["par.outputs.output_ilms"],
                        "vlsi.inputs.ilms_meta": "append"
                    }
                    new_ilm_filename = "{base}-{module}_ilm{ext}".format(base=b, module=module, ext=ext)
                    with open(new_ilm_filename, "w") as f:
                        json_content = json.dumps(new_ilm, indent=4)
                        f.write(json_content)
                    log.info("New input ILM JSON written to " + new_ilm_filename)
                    driver.update_project_configs(driver.project_configs + [new_ilm])
                return output

            self.hierarchical_auto_action = auto_action

        return driver, errors

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

        output_config = self.action_map()[action](driver, errors.append)
        if output_config is None:
            print("Action {action} failed with errors".format(action=action), file=sys.stderr)
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        else:
            # Dump output config for modular composition of hammer-vlsi runs.
            output_json = json.dumps(output_config, indent=4)
            with open(args["output"], "w") as f:
                f.write(output_json)
            print(output_json)
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
                            help='Project config files (.yml or .json) - .json will take precedence over any .yml.')
        parser.add_argument("-l", "--log", required=False,
                            help='Log file. Leave blank to automatically create one.')
        parser.add_argument("--obj_dir", required=False,
                            help='Folder for storing results of CAD tool runs. If not specified, this will be the hammer-vlsi folder by default. Can also be specified via the environment variable HAMMER_DRIVER_OBJ_DIR.')
        parser.add_argument("--syn_rundir", required=False, default="",
                            help='(optional) Directory to store syn results in')
        parser.add_argument("--par_rundir", required=False, default="",
                            help='(optional) Directory to store par results in')
        # Optional arguments for step control.
        parser.add_argument("--from_step", dest="from_step", required=False,
                            help="Run the given action from the given step (inclusive).")
        parser.add_argument("--to_step", dest="to_step", required=False,
                            help="Run the given action to the given step (inclusive).")
        parser.add_argument("--only_step", dest="only_step", required=False,
                            help="Run only the given step. Not compatible with --from_step or --to_step.")
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

        if HammerVLSISettings.set_hammer_vlsi_path_from_environment() is False:
            print("You must set HAMMER_VLSI to the hammer-vlsi directory", file=sys.stderr)
            sys.exit(1)

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
