#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  entry.py
#  
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
#
#  Entry point to the hammer VLSI abstraction.

import argparse
import datetime
import importlib
import json
import os
import subprocess
import sys

import hammer_config
import hammer_vlsi
import hammer_tech

# TODO: move most of this into the hammer-vlsi library itself so that applications can more easily utilize this without duplicating all this code.
def main(args: dict) -> int:
    # Create global logging context.
    if args["log"] is None:
        log_file = datetime.datetime.now().strftime("hammer-vlsi-%Y%m%d-%H%M%S.log")
    else:
        log_file = args["log"]
    file_logger = hammer_vlsi.HammerVLSIFileLogger(log_file)
    hammer_vlsi.HammerVLSILogging.add_callback(file_logger.callback)
    log = hammer_vlsi.HammerVLSILogging.context()

    # Create a new hammer database.
    database = hammer_config.HammerDatabase() # type: hammer_config.HammerDatabase

    log.info("Loading hammer-vlsi libraries and reading settings")

    # Load in builtins.
    database.update_builtins([
        hammer_config.load_config_from_file("builtins.yml", strict=True),
        hammer_vlsi.HammerVLSISettings.get_config()
    ])

    # Read in core defaults.
    database.update_core(hammer_config.load_config_from_defaults(os.getcwd()))

    # Read in the environment config for paths to CAD tools, etc.
    for config in args['environment_config']:
        if not os.path.exists(config):
            log.error("Environment config %s does not exist!" % (config))
    database.update_environment(hammer_config.load_config_from_paths(args['environment_config'], strict=True))

    # Read in the project config to find the syn, par, and tech.
    project_configs = hammer_config.load_config_from_paths(args['configs'], strict=True)
    database.update_project(project_configs)
    project_config = hammer_config.combine_configs(project_configs) # type: dict

    # Get the technology and load technology settings.
    tech_str = database.get_setting("vlsi.core.technology")
    tech_paths = database.get_setting("vlsi.core.technology_path")
    for path in tech_paths:
        tech_json_path = os.path.join(path, tech_str, "%s.tech.json" % (tech_str))
        if os.path.exists(tech_json_path):
            break
    log.info("Loading technology '{0}'".format(tech_str))
    tech = hammer_tech.HammerTechnology.load_from_dir(tech_str, os.path.dirname(tech_json_path))
    tech.logger = log.context("tech")
    tech.set_database(database)
    tech.cache_dir = "%s/tech-%s-cache" % (hammer_vlsi.HammerVLSISettings.hammer_vlsi_path, tech_str) # TODO: don't hardcode this
    database.update_technology(tech.get_config())

    tech.extract_tarballs() # TODO: move this back into tech itself

    # Find the synthesis/par tool and read in their configs.
    syn_tool_name = database.get_setting("vlsi.core.synthesis_tool")
    syn_tool_get = hammer_vlsi.load_tool(path=database.get_setting("vlsi.core.synthesis_tool_path"), tool_name=syn_tool_name)
    assert isinstance(syn_tool_get, hammer_vlsi.HammerSynthesisTool), "Synthesis tool must be a HammerSynthesisTool"
    syn_tool = syn_tool_get # type: hammer_vlsi.HammerSynthesisTool
    syn_tool.logger = log.context("synthesis")
    syn_tool.set_database(database)
    syn_tool.run_dir = hammer_vlsi.HammerVLSISettings.hammer_vlsi_path + "/syn-rundir" # TODO: don't hardcode this
    syn_tool.input_files = args['verilog']
    syn_tool.technology = tech
    if database.get_setting("synthesis.inputs.top_module") != 'null':
        syn_tool.top_module = database.get_setting("synthesis.inputs.top_module")
    else:
        syn_tool.top_module = args['top']

    par_tool_name = database.get_setting("vlsi.core.par_tool")
    par_tool_get = hammer_vlsi.load_tool(path=database.get_setting("vlsi.core.par_tool_path"), tool_name=par_tool_name)
    assert isinstance(par_tool_get, hammer_vlsi.HammerPlaceAndRouteTool), "Synthesis tool must be a HammerPlaceAndRouteTool"
    par_tool = par_tool_get # type: hammer_vlsi.HammerPlaceAndRouteTool
    par_tool.logger = log.context("par")
    par_tool.set_database(database)
    par_tool.run_dir = hammer_vlsi.HammerVLSISettings.hammer_vlsi_path + "/par-rundir" # TODO: don't hardcode this

    database.update_tools(syn_tool.get_config() + par_tool.get_config())

    # TODO: think about artifact storage?
    log.info("Starting synthesis with tool '%s'" % (syn_tool_name))
    syn_tool.run()
    # TODO: check and handle failure!!!

    # Record output from the syn_tool into the JSON output.
    # TODO(edwardw): automate this
    try:
        project_config["synthesis.outputs.output_files"] = syn_tool.output_files
        project_config["synthesis.inputs.input_files"] = syn_tool.input_files
        project_config["synthesis.inputs.top_module"] = syn_tool.top_module
    except ValueError as e:
        log.fatal(e.args[0])
        return 1

    log.info("Starting place and route with tool '%s'" % (par_tool_name))
    # TODO: get place and route working
    par_tool.run()

    # Dump output config for modular composition of hammer-vlsi runs.
    output_json = json.dumps(project_config, indent=4)
    with open(args["output"], "w") as f:
        f.write(output_json)
    print(output_json)

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
