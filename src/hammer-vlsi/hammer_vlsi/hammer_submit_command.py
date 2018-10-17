#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# hammer_submit_command.py
#

from abc import ABCMeta, abstractmethod
import atexit
import subprocess
from typing import Callable, Iterable, List, NamedTuple, Optional, Dict, Any, Union
from hammer_logging import HammerVLSIFileLogger, HammerVLSILogging, HammerVLSILoggingContext
from hammer_config import HammerDatabase

class HammerSubmitCommand:

    @abstractmethod
    def submit(self, args: List[str], env: Dict[str,str], logger: HammerVLSILoggingContext, cwd: str = None) -> str:
        """
        Submit the job to the job submission system. This function MUST block until the command is complete.

        :param args: Command-line to run; each item in the list is one token. The first token should be the command to run.
        :param env: The environment variables to set for the command
        :param logger: The logging context
        :param cwd: Working directory (leave as None to use the current working directory).
        :return: The command output
        """
        pass

    @abstractmethod
    def read_settings(self, tool_namespace: str, database: HammerDatabase) -> None:
        """
        Read the HammerDatabase settings into meaningful class variables.

        :param tool_namespace: The tool namespace to use when querying the HammerDatabase (e.g. "synthesis" or "par")
        :param database: The HammerDatabase object with tool settings
        """
        pass


    @staticmethod
    def get(tool_namespace: str, database: HammerDatabase):
        """
        Get a concrete instance of a HammerSubmitCommand for a tool

        :param tool_namespace: The tool namespace to use when querying the HammerDatabase (e.g. "synthesis" or "par")
        :param database: The HammerDatabase object with tool settings
        """

        submit_command_mode = database.get_setting(tool_namespace + ".submit_command", nullvalue="none")
        if submit_command_mode == "none" or submit_command_mode == "bare":
            if database.get_setting(tool_namespace + ".submit_command_settings", nullvalue="") != "":
                raise ValueError("Unexpected " + tool_namespace + ".submit_command_settings for HammerBareSubmitCommand. Did you forget to set " + tool_namespace + ".submit_command?")
            return HammerBareSubmitCommand()
        elif submit_command_mode == "lsf":
            submit_command = HammerLSFSubmitCommand()
            submit_command.read_settings(tool_namespace, database)
            return submit_command
        else:
            raise NotImplementedError("Submit command key for " + tool_namespace + ": " + submit_command_mode + " is not implemented")


class HammerBareSubmitCommand(HammerSubmitCommand):

    def submit(self, args: List[str], env: Dict[str,str], logger: HammerVLSILoggingContext, cwd: str = None) -> str:
        # Just run the command on this host.

        # Short version for easier display in the log.
        PROG_NAME_LEN = 14 # Capture last 14 characters of the command name
        ARG_DISPLAY_LEN = 16 # How many characters of args to display after prog_name
        if len(args[0]) <= PROG_NAME_LEN:
            prog_name = args[0]
        else:
            prog_name = "..." + args[0][len(args[0])-PROG_NAME_LEN:]
        remaining_args = " ".join(args[1:])
        if len(remaining_args) < ARG_DISPLAY_LEN:
            prog_args = remaining_args
        else:
            prog_args = remaining_args[0:ARG_DISPLAY_LEN-1] + "..."
        prog_tag = prog_name + " " + prog_args

        logger.debug("Executing subprocess: " + ' '.join(args))
        subprocess_logger = logger.context("Exec " + prog_tag)
        proc = subprocess.Popen(args, shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, env=env, cwd=cwd)
        atexit.register(proc.kill)

        output_buf = ""
        # Log output and also capture output at the same time.
        while True:
            line = proc.stdout.readline().decode("utf-8")
            if line != '':
                subprocess_logger.debug(line.rstrip())
                output_buf += line
            else:
                break
        # TODO: check errors

        return output_buf

    def read_settings(self, tool_namespace: str, database: HammerDatabase) -> None:
        assert("Should never get here; bare submission command does not have settings")

class HammerLSFSubmitCommand(HammerSubmitCommand):

    # TODO list:
    #  - we should have a submit_command.lsf.global_settings field (this will allow us to have an lsf.yml file with most of the settings that won't change)
    #  - we need to log the command output

    @property
    def bsub_binary(self) -> str:
        """ Get the LSF bsub binary location """
        try:
            return self._bsub_binary
        except AttributeError:
            raise ValueError("LSF bsub binary location not set")

    @bsub_binary.setter
    def bsub_binary(self, value: str) -> None:
        """ Set the LSF bsub binary location """
        if value == "" or value is None:
            raise ValueError("bsub_binary cannot be empty or null")
        self._bsub_binary = value

    @property
    def num_cpus(self) -> int:
        """ Get the number of CPUs to use """
        try:
            return self._num_cpus
        except AttributeError:
            raise ValueError("Did not set the number of CPUs to use (0 for unspecified)")

    @num_cpus.setter
    def num_cpus(self, value: int) -> None:
        """ Set the number of CPUs to use """
        self._num_cpus = value # type: int

    @property
    def queue(self) -> Optional[str]:
        """ Get the LSF queue to use """
        try:
            return self._queue
        except AttributeError:
            raise ValueError("Did not set the queue to use (can be None)")

    @queue.setter
    def queue(self, value: str) -> None:
        """ Set the LSF queue to use """
        self._queue = value # type: str

    @property
    def extra_args(self) -> List[str]:
        """ Get the extra LSF args to use """
        try:
            return self._extra_args
        except AttributeError:
            # Use no extra args if empty
            return [] # type : List[str]

    @extra_args.setter
    def extra_args(self, value: List[str]) -> None:
        """ Set the extra LSF args to use """
        self._extra_args = value

    def read_settings(self, tool_namespace: str, database: HammerDatabase) -> None:
        self.bsub_binary = database.get_setting(tool_namespace + ".submit_command_settings.bsub_binary", nullvalue="")
        try:
            self.num_cpus = int(database.get_setting(tool_namespace + ".submit_command_settings.num_cpus", nullvalue=0))
        except KeyError:
            self.num_cpus = 0
        try:
            self.queue = database.get_setting(tool_namespace + ".submit_command_settings.queue", nullvalue=None)
        except KeyError:
            self.queue = None
        self.extra_args = database.get_setting(tool_namespace + ".submit_command_settings.extra_args", nullvalue=[]) # type: List[str]

    def bsub_args(self) -> List[str]:
        args = [self.bsub_binary, "-K"] # always use -K to block
        if self.queue is not None:
            args.extend(["-q", self.queue])
        if self.num_cpus > 0:
            args.extend(["-n", "%d" % self.num_cpus])
        args.extend(self.extra_args)
        return args

    def submit(self, args: List[str], env: Dict[str,str], logger: HammerVLSILoggingContext, cwd: str = None) -> str:
        # TODO fix output capturing

        # Short version for easier display in the log.
        PROG_NAME_LEN = 14 # Capture last 14 characters of the command name
        ARG_DISPLAY_LEN = 16 # How many characters of args to display after prog_name
        if len(args[0]) <= PROG_NAME_LEN:
            prog_name = args[0]
        else:
            prog_name = "..." + args[0][len(args[0])-PROG_NAME_LEN:]
        remaining_args = " ".join(args[1:])
        if len(remaining_args) < ARG_DISPLAY_LEN:
            prog_args = remaining_args
        else:
            prog_args = remaining_args[0:ARG_DISPLAY_LEN-1] + "..."
        prog_tag = prog_name + " " + prog_args

        logger.debug("Executing subprocess: " + ' '.join(self.bsub_args()) + ' "' + ' '.join(args) + '"')
        subprocess_logger = logger.context("Exec " + prog_tag)
        proc = subprocess.Popen(self.bsub_args() + [' '.join(args)], shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, env=env, cwd=cwd)
        atexit.register(proc.kill)

        output_buf = ""
        # Log output and also capture output at the same time.
        while True:
            line = proc.stdout.readline().decode("utf-8")
            if line != '':
                subprocess_logger.debug(line.rstrip())
                output_buf += line
            else:
                break
        # TODO: check errors

        return output_buf

        return ""
