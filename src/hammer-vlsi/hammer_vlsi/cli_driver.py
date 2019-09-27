#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  cli_driver.py
#  CLI driver class for the Hammer VLSI abstraction.
#
#  See LICENSE for licence details.

import argparse
import glob
import json
import subprocess
import os
import sys

from .hammer_vlsi_impl import HammerTool, HammerVLSISettings
from .hooks import HammerToolHookAction
from .driver import HammerDriver, HammerDriverOptions
from .design import HammerDesign

from typing import List, Dict, Tuple, Any, Callable, Optional

from hammer_config import HammerJSONEncoder

#----------------------------------------------------------------------------
class CLIDriver:
    """
    Helper class for projects to easily write/customize a CLI driver for 
    hammer without needing to rewrite/copy all the argparse and plumbing.
    """

    def configure_and_run(self, args: dict) -> None:
        """
        parse command line options, create driver, create actions, and run
        Parse command line arguments and environment variables for the 
        command line front-end to hammer-vlsi.
        :return: HammerDriver and a list of errors.
        """
        #--------------------------------------------------------------------
        # create hammer-driver object
        #--------------------------------------------------------------------
        config_dir = os.path.abspath("configs")
        if args["config_dir"] is not None:
            config_dir = os.path.abspath(args["config_dir"])
        env_dir = os.path.join(config_dir, "env")
        proj_dir = os.path.join(config_dir, "project")
        if not os.path.isdir(env_dir):
            raise Exception("env-configs dir doesnt exist: {}".format(env_dir))
        if not os.path.isdir(proj_dir):
            raise Exception("proj-configs dir doesnt exist: {}".format(proj_dir))

        env_files = glob.glob("{}/*.yml".format(env_dir)) + \
                    glob.glob("{}/*.json".format(env_dir))
        proj_files = glob.glob("{}/*.yml".format(proj_dir)) + \
                     glob.glob("{}/*.json".format(proj_dir))

        options = HammerDriver.get_default_driver_options() 
        options.environment_configs = env_files
        options.project_configs = proj_files
        options.log_file = args["log_file"]
        options.run_file = args["run_dir"]
        options.release_file = args["release_dir"]

        driver = HammerDriver(options)

        #--------------------------------------------------------------------
        # build all the actions dynamically
        #--------------------------------------------------------------------
        def _get_nonempty_str(arg: Any) -> Optional[str]:
            if isinstance(arg, str) and (len(arg) > 0):
                return str(arg)
            return None

        from_step = _get_nonempty_strargs['from_step'])
        to_step   = _get_nonempty_str(args['to_step'])
        only_step = _get_nonempty_str(args['only_step'])

        actions = {}
        for tool_name in driver.get_supported_tool_types():
            for design in driver.get_designs():
                tool = design.get_tool(tool_name)
                # tool actions
                def make_func(tool, design) -> bool:
                    action_name = "{}-{}".format(tool.name, design.name)
                    def func():
                        hooks = []
                        attrname = "get_extra_{}_hooks".format(tool.name)
                        if hasattr(self, attrname):
                            hooks = getattr(self, attrname)()
                            if not isinstance(hooks, list):
                                raise Exception(attrname+"didn't return a list")
                            for hook in hooks:
                                if not isinstance(hook, HammerToolHookAction:
                                    raise Exception(attrname+"returned non-hook")
                        tool.run(hooks=hooks, from=from_step, to=to_step)
                    return func

                tools[action_name] = make_func(driver.setup_tool(tool, design))

    #-------------------------------------------------------------------------
    def get_top_design(self, driver:HammerDriver, 
                       design_name:Optional[str]) -> HammerDesign
        if design_name is not None:
            return driver.get_design(design_name)
        else:
            return driver.get_top_design()

    #-------------------------------------------------------------------------
    def _print_macro_sizes(self, driver: HammerDriver) -> None:
        """Dump macro size information (for convenience)"""
        return json.dumps(
            list(map(lambda m: m.to_setting(), driver.tech.get_macro_sizes())),
            cls=HammerJSONEncoder, 
            indent=4)

    #-------------------------------------------------------------------------
    def print_steps(self, driver: HammerDriver, 
            design_name: Optional[str]) -> None:
        top_design = self.get_top_design(design_name)
        print("Stages and steps for {}:".format(top_design.name))
        for stage in top_design.get_stages():
            print("stage: {}".format(stage.name))
            for step in stage.steps():
                print("  {}".format(step.name))
        print("")

    #-------------------------------------------------------------------------
    def print_status(self, driver: HammerDriver, design_name: Optional[str], 
                    stage_name: Optional[str]) -> None:
        top_design = self.get_top_design(design_name)
        stages = top_design.get_stages()

        text_table = []
        col_widths = []
        def build_status_table(design: HammerDesign, lpad: str) -> None:
            line = ["{}{}".format(lpad, design.name)]
            for stage in stages:
                if design.has_stage(stage.name):
                    dstage = design.get_stage(stage.name)
                    if dstage.has_stale_release():
                        line.append("STALE")
                    if dstage.has_valid_release():
                        line.append("OK")
                    else:
                        line.append("MISSING")
                else:
                    line.append("N/A")
            text_table.append(line)
            for idx in range(len(line)):
                if col_widths[idx] is None or col_widths[idx] < len(line[idx]):
                    col_widths[idx] = len(line[idx])
            for child in design.get_children():
                build_status_table(child, lpad+"  ")

        build_status_table(top_design)

        fmt_strings   = list(map(lambda x: "{:^"+(x+2)+"s}", col_widths))
        line2_strings = list(map(lambda x: "-"*(x+2), col_widths))

        for idx in range(len(col_widths)):
            sys.stdout.write(fmt_strings[idx].format(text_table[0][idx]))
        sys.stdout.write("\n")
        for item in line2_strings:
            sys.stdout.write(item)
        sys.stdout.write("\n")
        for oidx in range(1, len(text_table)):
            for idx in range(len(col_widths)):
                sys.stdout.write(fmt_strings[idx].format(text_table[oidx][idx]))
            sys.stdout.write("\n")
        sys.stdout.write("\n")

    #-------------------------------------------------------------------------
    def configure_and_run(self, args: dict) -> None:
        """loads and configures driver, and then runs some action"""
        config_dir = os.path.abspath("configs")
        if args["config_dir"] is not None:
            config_dir = os.path.abspath(args["config_dir"])
        env_dir = os.path.join(config_dir, "env")
        proj_dir = os.path.join(config_dir, "project")
        if not os.path.isdir(env_dir):
            raise Exception("env-configs dir doesnt exist: {}".format(env_dir))
        if not os.path.isdir(proj_dir):
            raise Exception("proj-configs dir doesnt exist: {}".format(proj_dir))

        env_files = glob.glob("{}/*.yml".format(env_dir)) + \
                    glob.glob("{}/*.json".format(env_dir))
        proj_files = glob.glob("{}/*.yml".format(proj_dir)) + \
                     glob.glob("{}/*.json".format(proj_dir))

        driver = HammerDriver(
            project_ymls=proj_files, 
            env_ymls=env_files
            extra_hooks=self.get_extra_hooks())

        if args["macro_sizes"] is not None:
            self.print_macro_sizes(driver, args["design"])
            return

        if args["list_steps"] is not None:
            self.print_steps(driver)
            return

        if args["status"] is not None:
            self.print_status(driver, args["design"], args["stage"])
            return

        stage = driver.get_design(args["design"]).get_stage(args["stage"])

        if args["release"] is not None:
            stage.make_release()
            return

        def _get_nonempty_str(arg: Any) -> Optional[str]:
            if isinstance(arg, str) && len(arg) > 0:
                return str(arg)
            return None

        from_step = _get_nonempty_str(args['from_step'])
        to_step   = _get_nonempty_str(args['to_step'])
        only_step = _get_nonempty_str(args['only_step'])
        if only_step is not None:
            if (from_step is not None) or (to_step is not None):
                raise Exception("cant specify --only_step with --to/from_step")
            from_step = only_step
            to_step = only_step

        stage.run(stage, from_step=from_step, to_step=to_step)


    def main(self) -> None:
        """
        main entry point to cli-driver. sub-class this class to add any hooks
        and addint stage-specifc hook-list getters of the form 
        'get_extra_<stage>_hooks() -> List[HammerToolHookAction]'
        """
        parser = argparse.ArgumentParser(description=textwrap.dedent("""
        Designs:
        --------
        This is a command-line front-end for HAMMER. A chip is composed of 1 or
        more designs: there is a top design and 0 or more designs below it.
        A design will be separately implemented and integrated into its parent
        designs. A design can show up under multiple different parents. A 
        design can have more than 1 sub-designs at varying depths. A design
        is synonymous with a 'module' in verilog.

        Stages:
        -------
        Each design has some stages associated with it (such as syn, pnr, drc).
        Stages can depend on other stages. For example blockA/pnr
        might depend on blockA/syn to release data. Also, a stage
        can depend on outputs from parent or child stages (for example, a 
        partition pnr WILL depend on the pnr stages of each child block).

        Stages are associated N:1 with tools. For example, sim_syn, and sim_pnr
        both use the sim tool, but with different stage configurations (meaning,
        sim will get inputs from different places depending on what stage 
        invoked it). A tool is a generic wrapper around a real vendor tool 
        (e.g.: the "sim" tool can be instantiated by the "vcs" vendor tool
        You run the stages by running "hammer-vlsi <design> <stages>"

        Stages:
        -------
        The chip has a global release directory. Stages will release their
        final collateral to this release directory. If you are satisfied with
        the results, release the collateral by running
        "hammer-vlsi <design> <stages> --release". You cannot release collateral
        in the same tool invocation that you run a stage's steps. However,
        if you run a stage that invokes multiple dependency stages, those 
        dependencies will be released (under the hood, in hammer) before the 
        target stage is run.

        To view the implementation status of all designs across all stages,
        run "hammer-vlsi --status" to get a hierarchical 2-D chart.

        Steps:
        ------
        Each stage has 1 or more steps. A step is a discrete chunk of 
        code that can be run in the tool, without running the other steps. For
        example, synthesis has a "syn_generic" and a "syn_map" step, among
        others. You can specify which subset of steps to run with the
        "--from_step", "--to_step", and "--only_step" arguments. To get a list
        of all steps for all stages, run "hammer-vlsi --list-steps"
        
        Configs:
        --------
        Configs are YAML/JSON files. hammer-vlsi is opinionated about input
        configs: your environment configs must live in ./configs/env, and
        your project configs must live in ./configs/project. All *.yml/*.json
        files are sourced from these directories. Project configs
        override environment configs with the same key-path. You can override
        the configs base-dir by running "hammer-vlsi --config_dir=<dir>".
        """)

        # main args
        parser.add_argument('design', type=str, required=False,
            help="the name of the design to run the stages on")
        parser.add_argument('stages', type=str, required=False,
            help="which stages to run (comma-separated)")

        # stage control
        parser.add_argument('--status', type=str, required=False,
            help="show the status of all designs, or the specified design")
        parser.add_argument("--release", dest="release", required=False,
            help="Run the design release only. this will ONLY run release."
        parser.add_argument("--no_deps", dest="no_deps", required=False,
            help="do not run out-of-date dependency stages")

        # step control
        parser.add_argument("--list_steps", dest="list_steps", required=False,
            help="List steps for all stages and exit")
        parser.add_argument("--from_step", dest="from_step", required=False,
            help="Run the given action from the given step (inclusive).")
        parser.add_argument("--to_step", dest="to_step", required=False,
            help="Run the given action to the given step (inclusive).")
        parser.add_argument("--only_step", dest="only_step", required=False,
            help="Run only the given step. Not compatible with --from/to_step")

        # miscellaneous
        parser.add_argument('--config_dir', type=str, required=False,
            help="directory where env/project configs are stored")
        parser.add_argument('--run_dir', type=str, required=False,
            help="alternate run_dir")
        parser.add_argument('--release_dir', type=str, required=False,
            help="alternate release_dir")
        parser.add_argument("--dump_db", dest="dump_db", required=False,
            help="Dump the flattened config database to stdout then exit")
        parser.add_argument("--macro_sizes", dest="macro_sizes", required=False,
            help="Print macro-sizes (for convenience) then exit")
        parser.add_argument('--log_file', type=str, required=False,
            help="also pipe hammer stdout/stderr to this file")

        if os.environ["HAMMER_VLSI"] is None:
            raise Exception("env HAMMER_VLSI isnt set. source the sourceme.sh")

        self.configure_and_run(vars(parser.parse_args(args)))
        sys.exit(0)



