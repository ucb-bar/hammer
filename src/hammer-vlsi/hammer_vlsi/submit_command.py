#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# submit_command.py
#

from abc import ABCMeta, abstractmethod
import atexit
import subprocess
import hammer_utils
from typing import Callable, Iterable, List, NamedTuple, Optional, Dict, Any, Union
from hammer_logging import HammerVLSIFileLogger, HammerVLSILogging, HammerVLSILoggingContext
from hammer_config import HammerDatabase
from functools import reduce

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
    def read_settings(self, settings: Dict[str, Any], tool_namespace: str) -> None:
        """
        Read the settings object (a Dict[str, Any]) into meaningful class variables

        :param settings: A Dict[str, Any] comprising the settings for this command
        :param tool_namespace: The namespace for the tool (useful for logging)
        """
        pass


    @staticmethod
    def get(tool_namespace: str, database: HammerDatabase) -> "HammerSubmitCommand":
        """
        Get a concrete instance of a HammerSubmitCommand for a tool

        :param tool_namespace: The tool namespace to use when querying the HammerDatabase (e.g. "synthesis" or "par")
        :param database: The HammerDatabase object with tool settings
        """

        submit_command_mode = database.get_setting(tool_namespace + ".submit.command", nullvalue="none")
        submit_command_settings = database.get_setting(tool_namespace + ".submit.settings", nullvalue=[]) # type: List[Dict[str, Dict[str, Any]]]

        # Settings is a List[Dict[str, Dict[str, Any]]] object. The first Dict key is the submit command name.
        # Its value is a Dict[str, Any] comprising the settings for that command.
        # The top-level list elements are merged from 0 to the last index, with later indices overriding previous entries.
        def combine_settings(settings: List[Dict[str, Dict[str, Any]]], key: str) -> Dict[str, Any]:
            return reduce(hammer_utils.add_dicts, map(lambda d: d[key], settings))

        submit_command = None # type: Optional[HammerSubmitCommand]
        if submit_command_mode == "none" or submit_command_mode == "local":
            # Do not read the options, return immediately
            return HammerLocalSubmitCommand()
        elif submit_command_mode == "lsf":
            submit_command = HammerLSFSubmitCommand()
        else:
            raise NotImplementedError("Submit command key for " + tool_namespace + ": " + submit_command_mode + " is not implemented")

        submit_command.read_settings(combine_settings(submit_command_settings, submit_command_mode), tool_namespace)
        return submit_command


class HammerLocalSubmitCommand(HammerSubmitCommand):

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

    def read_settings(self, settings: Dict[str, Any], tool_namespace: str) -> None:
        assert("Should never get here; local submission command does not have settings")

class HammerLSFSubmitCommand(HammerSubmitCommand):

    # TODO list:
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
    def num_cpus(self) -> Optional[int]:
        """ Get the number of CPUs to use """
        try:
            return self._num_cpus
        except AttributeError:
            raise ValueError("Did not set the number of CPUs to use (can be None)")

    @num_cpus.setter
    def num_cpus(self, value: int) -> None:
        """ Set the number of CPUs to use """
        self._num_cpus = value # type: Optional[int]

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
        self._queue = value # type: Optional[str]

    @property
    def extra_args(self) -> List[str]:
        """ Get the extra LSF args to use """
        try:
            return self._extra_args
        except AttributeError:
            raise ValueError("Did not set the extra_args to use (can be [])")

    @extra_args.setter
    def extra_args(self, value: List[str]) -> None:
        """ Set the extra LSF args to use """
        self._extra_args = value

    def read_settings(self, settings: Dict[str, Any], tool_name):
        try:
            self.bsub_binary = settings["bsub_binary"]
        except KeyError:
            raise ValueError("Missing mandatory LSF setting bsub_binary for tool %s", tool_name)
        try:
            self.num_cpus = settings["num_cpus"] # type: Optional[int]
        except KeyError:
            self.num_cpus = None
        try:
            self.queue = settings["queue"] # type: Optional[str]
        except KeyError:
            self.queue = None
        try:
            self.extra_args = settings["extra_args"] # type: List[str]
        except KeyError:
            self.extra_args = [] # type: List[str]

    def bsub_args(self) -> List[str]:
        args = [self.bsub_binary, "-K"] # always use -K to block
        if self.queue is not None:
            args.extend(["-q", self.queue])
        if self.num_cpus is not None:
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
