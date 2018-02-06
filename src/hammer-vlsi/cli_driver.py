#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  cli_driver.py
#  
#  Copyright 2017-2018 Edward Wang <edward.c.wang@compdigitec.com>
#
#  Entry point to the hammer VLSI abstraction.

import argparse
import json
import os
import subprocess
import sys

import hammer_config
import hammer_vlsi
import hammer_tech

from typing import List, Dict, Tuple, Any, Iterable, Callable, Optional


def action_map() -> Dict[str, Callable[[hammer_vlsi.HammerDriver, Callable[[str], None]], Optional[dict]]]:
    """Return the mapping of valid actions -> functions for each action of the command-line driver."""
    return {
        "synthesis": synthesis_action,
        "syn": synthesis_action,
        "par": par_action,
        "synthesis_to_par": synthesis_to_par_action,
        "synthesis-to-par": synthesis_to_par_action,
        "syn_to_par": synthesis_to_par_action,
        "syn-to-par": synthesis_to_par_action,
        "synthesis_par": None
    }


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


def args_to_driver(args: dict,
                   default_options: Optional[hammer_vlsi.HammerDriverOptions] = None) -> \
        Tuple[hammer_vlsi.HammerDriverOptions, dict, List[str]]:
    """Parse command line arguments and environment variables for the command line front-end to hammer-vlsi.

    :return: DriverOptions, a parsed config for certain options, and a list of errors."""

    # TODO: rewrite this less tediously?

    # Resolve default_options.
    # Can't call hammer_vlsi.HammerDriver.get_default_driver_options in the
    # parameters as it will be called when args_to_driver is defined, and
    # hammer_vlsi_path will not be defined yet.
    default_options_resolved = hammer_vlsi.HammerDriver.get_default_driver_options()  # type: hammer_vlsi.HammerDriverOptions
    if default_options is not None:
        default_options_resolved = default_options

    # Driver options.
    options = default_options_resolved  # type: hammer_vlsi.HammerDriverOptions

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

    return options, config, errors


def get_nonempty_str(arg: Any) -> Optional[str]:
    """Either get the non-empty string from the given arg or None if it is not a non-empty string."""
    if isinstance(arg, str):
        if len(arg) > 0:
            return str(arg)
    return None


def valid_actions() -> Iterable[str]:
    """Get the list of valid actions for the command-line driver."""
    return list(action_map().keys())


def synthesis_action(driver: hammer_vlsi.HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
    """Run the command-line synthesis action."""
    if not driver.load_synthesis_tool():
        # If the driver didn't successfully load, return None.
        return None
    syn_output = driver.run_synthesis()
    # TODO: detect errors
    return syn_output


def par_action(driver: hammer_vlsi.HammerDriver, append_error_func: Callable[[str], None]) -> Optional[dict]:
    """Run the command-line par action."""
    if not driver.load_par_tool():
        # If the driver didn't successfully load, return None.
        return None
    par_output = driver.run_par()
    # TODO: detect errors
    return par_output


def synthesis_to_par_action(driver: hammer_vlsi.HammerDriver, append_error_func: Callable[[str], None]) -> Optional[
    dict]:
    """Create a config to run the output."""
    print("driver.project_config = " + str(driver.project_config))
    return hammer_vlsi.HammerDriver.generate_par_inputs_from_synthesis(driver.project_config)


def main(args: dict) -> int:
    action = str(args['action'])  # type: str
    if action not in valid_actions():
        print("Invalid action %s" % action, file=sys.stderr)
        return 1

    if args['firrtl'] is not None and len(args['firrtl']) > 0:
        print("firrtl convenience argument not yet implemented", file=sys.stderr)
        return 1

    options, config, errors = args_to_driver(args)
    driver = hammer_vlsi.HammerDriver(options, config)

    output_config = action_map()[action](driver, errors.append)
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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('action', metavar='ACTION', type=str, choices=valid_actions(),
                        help='Action to perform with the command-line driver.')
    # Required options for (Python) hammer driver.
    parser.add_argument("-e", "--environment_config", action='append', required=False,
                        help="Environment config files (.yml or .json) - .json will take precendence over any .yml. These config files will not be re-emitted in the output json. Can also be specified as a colon-separated list in the environment variable HAMMER_ENVIRONMENT_CONFIGS.")
    parser.add_argument("-p", "--project_config", action='append', dest="configs", type=str,
                        help='Project config files (.yml or .json) - .json will take precedence over any .yml.')
    parser.add_argument("-l", "--log", required=False,
                        help='Log file. Leave blank to automatically create one.')
    parser.add_argument("--obj_dir", required=False,
                        help='Folder for storing results of CAD tool runs. If not specified, this will be the hammer-vlsi folder by default. Can also be specified via the environment variable HAMMER_DRIVER_OBJ_DIR.')
    # Required options for CLI hammer driver.
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

    if "HAMMER_VLSI" in os.environ:
        hammer_vlsi.HammerVLSISettings.hammer_vlsi_path = os.environ["HAMMER_VLSI"]
    else:
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

    sys.exit(main(vars(parser.parse_args())))
