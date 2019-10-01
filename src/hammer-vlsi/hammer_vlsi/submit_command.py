#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  submit_command.py
#  Hammer job submit command APIs.
#
#  See LICENSE for licence details.

# pylint: disable=bad-continuation

import re
import os
import atexit
import subprocess
from datetime import datetime
from abc import abstractmethod
from functools import reduce
from typing import Any, Dict, List, NamedTuple, Optional

from hammer_config import HammerDatabase
from hammer_logging import HammerVLSILoggingContext
from hammer_utils import add_dicts, get_or_else

__all__ = ['HammerSubmitResult',
           'HammerSubmitCommand', 'HammerLocalSubmitCommand',
           'HammerLSFSettings', 'HammerLSFSubmitCommand']

#=============================================================================
# SubmitResult
#=============================================================================

class HammerSubmitResult(NamedTuple('SubmitResult', [
    ('success', bool),
    ('code', int),
    ('errors', List[str]),
    ('output', List[str])
])):
    __slots__ = ()

#=============================================================================
# SubmitCommand base class
#=============================================================================

class HammerSubmitCommand:

    @staticmethod
    def get(tool_namespace: str, database: HammerDatabase) -> "HammerSubmitCommand":
        """
        Get a concrete instance of a HammerSubmitCommand for a tool
        :param tool_namespace: The tool namespace to use when querying the
                               HammerDatabase (e.g. "synthesis" or "par").
        :param database: The HammerDatabase object with tool settings
        """
        db                = database
        ns                = "{}.submit".format(tool_namespace)
        mode              = db.get_setting(ns+".command", nullvalue="none")
        settings          = db.get_setting(ns+".settings", nullvalue=[]) 
        max_outputs       = db.get_setting(ns+".max_output_lines")
        max_errors        = db.get_setting(ns+".max_error_lines")
        abort_on_error    = db.get_setting(ns+".abort_on_error")
        error_rgxs        = db.get_setting(ns+".error_rgxs", nullvalue=[])
        error_ignore_rgxs = db.get_setting(ns+".error_ignore_rgxs", nullvalue=[])

        # Settings is a List[Dict[str, Dict[str, Any]]] object. The first Dict
        # key is the submit command name.
        # Its value is a Dict[str, Any] comprising the settings for that command.
        # The top-level list elements are merged from 0 to the last index, with
        # later indices overriding previous entries.
        def combine_settings(settings: List[Dict[str, Dict[str, Any]]], 
                key: str) -> Dict[str, Any]:
            return reduce(add_dicts, map(lambda d: d[key], settings), {})
        settings = combine_settings(settings, mode)

        cmd = None
        if (mode == "none") or (mode == "local"):
            cmd = HammerLocalSubmitCommand()
            cmd.settings = None
        elif mode == "lsf":
            cmd = HammerLSFSubmitCommand()
            cmd.settings = HammerLSFSettings.from_setting(settings)
        else:
            raise NotImplementedError(
                "Submit command key for {0}: {1} is not implemented".format(
                    tool_namespace, submit_command_mode))

        cmd.max_outputs       = int(max_errors) if len(max_errors) else None
        cmd.max_errors        = int(max_errors) if len(max_errors) else None
        cmd.abort_on_error    = abort_on_error
        cmd.error_rgxs        = error_rgxs
        cmd.error_ignore_rgxs = error_ignore_rgxs

        return cmd

    def write_run_script(self, tag:str, args:List[str], cwd:str=None) -> str:
        """
        writes a script that is directly executed. if you run this script
        outside hammer, you should get the same results as when hammer ran
        """
        cwd = cwd if cwd is not None else os.getcwd()
        cmd_script = "{}/{}.sh".format(cwd, tag)
        output = ["#!/bin/bash",
                  "[ -f ./enter ] && source ./enter",
                  "exec {} \\".format(args[0])]
        for arg in args[1:]:
            output += ["  '{}' \\".format(re.sub("'", "\\'", arg))]
        output += [""]
        with open(cmd_script, "w") as f:
            f.write("\n".join(output))
        os.chmod(cmd_script, 0o755)
        return cmd_script

    @abstractmethod
    def get_cmd_array(self, tag:str, args: List[str], env: Dict[str, str],
            logger: HammerVLSILoggingContext, cwd: str = None) -> List[str]:
        raise NotImplementedError()

    def submit(self, args: List[str], env: Dict[str, str],
               logger: HammerVLSILoggingContext, 
               cwd: str = None) -> HammerSubmitResult:
        """
        Submit the job to the job submission system. This function MUST block
        until the command is complete.
        :param args: Command-line to run; each item in the list is one token.
                     The first token should be the command to run.
        :param env: The environment variables to set for the command
        :param logger: The logging context
        :param cwd: Working directory (leave as None to use the current 
                    working directory).
        :return: The command output
        """
        prog_tag = self.get_program_tag(args)

        subprocess_logger = logger.context("Exec " + prog_tag)

        proc = subprocess.Popen(
            self.get_cmd_array("submit_command", args, env, subprocess_logger, cwd),
            shell=False,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE, 
            env=env, 
            cwd=cwd)

        output_lines = []
        log_file = "{}/{}.log".format(cwd, "submit_command")
        output_clipped = False

        with open(log_file, "w") as f:
            def print_to_all(line):
                f.write(line)
                subprocess_logger.debug(line)
                if (self.max_outputs is not None) and \
                        (len(output_lines) <= int(self.max_outputs)):
                    output_lines.append(line)
                else:
                    output_clipped = True

            while True:
                line = proc.stdout.readline().decode("utf-8")
                if line != '':
                    print_to_all(line.rstrip())
                else:
                    break

            if output_clipped:
                print_to_all("[HAMMER]: max output lines exeeded...")

        proc.communicate()
        code = proc.returncode
        success = (code == 0)

        if self.abort_on_error and (code != 0):
            raise ChildProcessError("Failed command: {}, code={}"
                .format(prog_tag, code))

        # check the output_lines for matching error strings
        error_lines = []
        for line in output_lines:
            if (self.max_errors is not None) and \
                    (len(error_lines) > int(self.max_errors)):
                error_lines.append("[HAMMER]: max errors exceeded...")
                break
            if len(list(filter(lambda r: re.match(r, line), error_rgxs))) > 0:
                if len(list(filter(lambda r: re.match(r, line), 
                        error_ignore_rgxs))) == 0:
                    success = False
                    error_lines.append(line)

        if self.abort_on_error and (len(error_lines) > 0):
            raise ChildProcessError("Failed command: {}, error in output={}"
                .format(prog_tag, error_lines[0]))

        return HammerSubmitResult(
            success=success,
            code=code, 
            errors=error_lines,
            output=output_lines)


    @staticmethod
    def get_program_tag(args: List[str], program_name_length: int = 14,
                        arg_display_len: int = 16) -> str:
        """
        Get a short "tag" of the program for easier display in the log.
        :param args: Arguments for subprocess
        :param program_name_length: Capture last 14 (default) characters of
                                    the command name.
        :param arg_display_len: How many characters of args to display after prog_name
        :return: Short tag of the program.
        """
        if len(args[0]) <= program_name_length:
            prog_name = args[0]
        else:
            prog_name = "..." + args[0][len(args[0]) - program_name_length:]

        remaining_args = " ".join(args[1:])
        if len(remaining_args) < arg_display_len:
            prog_args = remaining_args
        else:
            prog_args = remaining_args[0:arg_display_len - 1] + "..."

        return prog_name + " " + prog_args


#=============================================================================
# HammerLocalSubmit
#=============================================================================

class HammerLocalSubmitCommand(HammerSubmitCommand):

    def get_cmd_array(self, tag:str, args: List[str], env: Dict[str, str],
            logger: HammerVLSILoggingContext, cwd: str = None) -> List[str]:

        logger.debug('Executing subprocess: "{}"'.format(' '.join(args)))
        return [self.write_run_script(tag=tag, args=args, cwd=cwd)]

#=============================================================================
# HammerLSFSubmit
#=============================================================================

class HammerLSFSettings(NamedTuple('HammerLSFSettings', [
    ('bsub_binary', str),
    ('num_cpus', Optional[int]),
    ('queue', Optional[str]),
    ('log_file', Optional[str]),
    ('extra_args', List[str])
])):
    __slots__ = ()

    @staticmethod
    def from_setting(settings: Dict[str, Any]) -> 'HammerLSFSettings':
        if not isinstance(settings, dict):
            raise ValueError("Must be a dictionary")
        try:
            bsub_binary = settings["bsub_binary"]
        except KeyError:
            raise ValueError("Missing mandatory key bsub_binary for LSF settings.")
        try:
            num_cpus = settings["num_cpus"]
        except KeyError:
            num_cpus = None
        try:
            queue = settings["queue"]
        except KeyError:
            queue = None
        try:
            log_file = settings["log_file"]
        except KeyError:
            log_file = None

        return HammerLSFSettings(
            bsub_binary=bsub_binary,
            num_cpus=num_cpus,
            queue=queue,
            log_file=log_file,
            extra_args=get_or_else(settings["extra_args"], [])
        )

class HammerLSFSubmitCommand(HammerSubmitCommand):

    def get_cmd_array(self, tag:str, args: List[str], env: Dict[str, str],
            logger: HammerVLSILoggingContext, cwd: str = None) -> List[str]:

        logger.debug('Executing subprocess: {bsub_args} "{args}"'.format(
            bsub_args=' '.join(self.bsub_args()),
            args=' '.join(args)))

        return self.bsub_args() + \
            [self.write_run_script(tag=tag, args=args, cwd=cwd)]

    def bsub_args(self) -> List[str]:
        args = [self.settings.bsub_binary, "-K"]  # always use -K to block
        log_file = self.settings.log_file \
            if self.settings.log_file is not None \
            else datetime.now().strftime("hammer-vlsi-bsub-%Y%m%d-%H%M%S.log")
        args.extend(["-o", log_file])
        if self.settings.queue is not None:
            args.extend(["-q", self.settings.queue])
        if self.settings.num_cpus is not None:
            args.extend(["-n", "%d" % self.settings.num_cpus])
        args.extend(self.settings.extra_args)
        return args



