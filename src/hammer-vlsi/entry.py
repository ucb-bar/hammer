#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  entry.py
#  
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
#
#  Entry point to the hammer VLSI abstraction.

import argparse
import importlib
import json
import os
import subprocess
import sys

import hammer_config
import hammer_vlsi
import hammer_tech

from typing import List, Dict, Tuple, Any

def parse_args(args: dict, defaultOptions: hammer_vlsi.HammerDriverOptions = hammer_vlsi.HammerDriver.get_default_driver_options()) -> Tuple[hammer_vlsi.HammerDriverOptions, dict, List[str]]:
    """Parse command line arguments for the command line front-end to hammer-vlsi.
    
    :return: DriverOptions, a parsed config for certain options, and a list of errors."""

    # TODO: rewrite this less tediously?

    # Driver options.
    options = defaultOptions # type: hammer_vlsi.HammerDriverOptions

    # Extra config (flattened JSON).
    config = {} # type: Dict[str, Any]

    # Create a list of errors for the user.
    errors = [] # type: List[str]

    # Load environment configs.
    env_configs = args['environment_config']
    if isinstance(env_configs, List):
        for c in env_configs:
            if not os.path.exists(c):
                errors.append("Environment config %s does not exist!" % (c))
        options = options._replace(environment_configs=list(env_configs))
    else:
        errors.append("environment_config was not a list?")

    # Load project configs.
    project_configs = args['configs']
    if isinstance(env_configs, List):
        for c in project_configs:
            if not os.path.exists(c):
                errors.append("Project config %s does not exist!" % (c))
        options = options._replace(project_configs=list(project_configs))
    else:
        errors.append("configs was not a list?")

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
    top_module = args['top']
    if isinstance(top_module, str) and len(top_module) > 0:
        config['synthesis.inputs.top_module'] = top_module

    return options, config, errors

def main(args: dict) -> int:
    if args['firrtl'] is not None and len(args['firrtl']) > 0:
        print("firrtl convenience argument not yet implemented", file=sys.stderr)
        return 1

    options, config, errors = parse_args(args)
    driver = hammer_vlsi.HammerDriver(options, config)
    driver.load_synthesis_tool()

    syn_output = driver.run_synthesis()
    # Dump output config for modular composition of hammer-vlsi runs.
    output_json = json.dumps(syn_output, indent=4)
    with open(args["output"], "w") as f:
        f.write(output_json)
    print(output_json)

    #~ hammer_vlsi.HammerDriver.par_run_from_synthesis()
    #~ driver.run_par()
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verilog", required=True, action='append',
                        help='Input set of Verilog files.')
    parser.add_argument("-f", "--firrtl", action='append', required=False,
                        help='Input set of firrtl files. Provided for convenience; hammer-vlsi will transform it to Verilog.')
    parser.add_argument("-o", "--output", default="output.json", required=False,
                        help='Output JSON file for results and modular use of hammer-vlsi. Default: output.json.')
    parser.add_argument("-l", "--log", required=False,
                        help='Log file. Leave blank to automatically create one.')
    parser.add_argument("-t", "--top", required=False,
                        help='Top module. If not specified, hammer-vlsi will take it from synthesis.inputs.top_module.')
    parser.add_argument("--cad-files", action='append', required=False,
                        help="CAD files.")
    parser.add_argument("--environment_config", action='append', required=False,
                        help="Environment config files (.yml or .json) - .json will take precendence over any .yml. These config files will not be re-emitted in the output json.")
    parser.add_argument('configs', metavar='CONFIGS', type=str, nargs='+',
                        help='Project config files (.yml or .json) - .json will take precedence over any .yml.')

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
        print("hammer-shell does not appear to be on the path (hammer-shell-test failed to run: %s)" % (output), file=sys.stderr)
        sys.exit(1)

    sys.exit(main(vars(parser.parse_args())))
