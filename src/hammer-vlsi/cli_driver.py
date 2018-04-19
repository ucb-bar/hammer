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

from hammer_vlsi_impl import HammerToolHookAction, HammerTool, HammerVLSISettings
from hammer_driver import HammerDriver, HammerDriverOptions

from typing import List, Dict, Tuple, Any, Iterable, Callable, Optional


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


# Type signature of a CLIDriver action.
CLIActionType = Callable[[HammerDriver, Callable[[str], None]], Optional[dict]]


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

        self.synthesis_action = self.create_synthesis_action([])
        self.par_action = self.create_par_action([])

    def action_map(self) -> Dict[str, CLIActionType]:
        """Return the mapping of valid actions -> functions for each action of the command-line driver."""
        return {
            "synthesis": self.synthesis_action,
            "syn": self.synthesis_action,
            "par": self.par_action,
            "synthesis_to_par": self.synthesis_to_par_action,
            "synthesis-to-par": self.synthesis_to_par_action,
            "syn_to_par": self.synthesis_to_par_action,
            "syn-to-par": self.synthesis_to_par_action,
            "synthesis_par": self.synthesis_par_action,
            "syn_par": self.synthesis_par_action
        }

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
                                post_load_func: Optional[
                                    Callable[[HammerDriver], None]] = None) -> CLIActionType:
        hooks = self.get_extra_synthesis_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("synthesis", hooks if len(hooks) > 0 else None, post_load_func)

    def create_par_action(self, custom_hooks: List[HammerToolHookAction],
                          post_load_func: Optional[Callable[[HammerDriver], None]] = None) -> CLIActionType:
        hooks = self.get_extra_par_hooks() + custom_hooks  # type: List[HammerToolHookAction]
        return self.create_action("par", hooks if len(hooks) > 0 else None, post_load_func)

    def create_action(self, action_type: str,
                      extra_hooks: Optional[List[HammerToolHookAction]],
                      post_load_func: Optional[Callable[[HammerDriver], None]]) -> CLIActionType:
        """
        Create an action function for the action_map.
        :param action_type: Either "syn"/"synthesis" or "par"
        :param extra_hooks: List of hooks to pass to the run function.
        :param post_load_func: Optional function to call after loading the tool.
        :return: Action function.
        """

        def post_load_func_checked(driver: HammerDriver) -> None:
            """Check that post_load_func isn't null before calling it."""
            if post_load_func is not None:
                post_load_func(driver)

        def action(driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
            # If the driver didn't successfully load, return None.
            if action_type == "synthesis" or action_type == "syn":
                if not driver.load_synthesis_tool(self.syn_rundir if self.syn_rundir is not None else ""):
                    return None
                else:
                    post_load_func_checked(driver)
                success, output = driver.run_synthesis(extra_hooks)
            elif action_type == "par":
                if not driver.load_par_tool(self.par_rundir if self.par_rundir is not None else ""):
                    return None
                else:
                    post_load_func_checked(driver)
                success, output = driver.run_par(extra_hooks)
            else:
                raise ValueError("Invalid action_type = " + str(action_type))
            # TODO: detect errors
            return output

        return action

    def synthesis_to_par_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        """Create a config to run the output."""
        return HammerDriver.generate_par_inputs_from_synthesis(driver.project_config)

    def synthesis_par_action(self, driver: HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
        syn_output = self.synthesis_action(driver, append_error_func)
        par_config = HammerDriver.generate_par_inputs_from_synthesis(syn_output)
        # TODO: Make this a function
        driver.project_config = par_config
        driver.database.update_project([driver.project_config])
        par_output = self.par_action(driver, append_error_func)
        return par_output


    def valid_actions(self) -> Iterable[str]:
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

        return driver, errors

    def run_main_parsed(self, args: dict) -> int:
        """
        Given a parsed dictionary of arguments, find and run the given action.
        :return: Return code (0 for success)
        """
        action = str(args['action'])  # type: str
        if action not in self.valid_actions():
            print("Invalid action %s" % action, file=sys.stderr)
            return 1

        if args['firrtl'] is not None and len(args['firrtl']) > 0:
            print("firrtl convenience argument not yet implemented", file=sys.stderr)
            return 1

        driver, errors = self.args_to_driver(args)

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

    def main(self) -> None:
        """
        Main function to call from your entry point script.
        Parses command line arguments.
        Example:
        >>> if __name__ == '__main__':
        >>>   CLIDriver().main()
        """
        parser = argparse.ArgumentParser()

        parser.add_argument('action', metavar='ACTION', type=str, choices=self.valid_actions(),
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

        sys.exit(self.run_main_parsed(vars(parser.parse_args())))
