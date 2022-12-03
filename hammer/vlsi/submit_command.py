#  submit_command.py
#  Hammer job submit command APIs.
#
#  See LICENSE for licence details.

# pylint: disable=bad-continuation

import atexit
import subprocess
import termios
import sys
import datetime
from abc import abstractmethod
from functools import reduce
from typing import Any, Dict, List, Tuple, NamedTuple, Optional

from hammer.config import HammerDatabase
from hammer.logging import HammerVLSILoggingContext
from hammer.utils import add_dicts, get_or_else

__all__ = ['HammerSubmitCommand', 'HammerLocalSubmitCommand',
           'HammerLSFSettings', 'HammerLSFSubmitCommand']


class HammerSubmitCommand:

    @abstractmethod
    def submit(self, args: List[str], env: Dict[str, str],
               logger: HammerVLSILoggingContext, cwd: Optional[str] = None) -> Tuple[str, int]:
        """
        Submit the job to the job submission system. This function MUST block
        until the command is complete.

        :param args: Command-line to run; each item in the list is one token.
                     The first token should be the command to run.
        :param env: The environment variables to set for the command
        :param logger: The logging context
        :param cwd: Working directory (leave as None to use the current working directory).
        :return: Tuple of the command output and a return code
        """
        pass

    @abstractmethod
    def read_settings(self, settings: Dict[str, Any], tool_namespace: str) -> None:
        """
        Read the settings object (a Dict[str, Any]) into meaningful class variables.

        :param settings: A Dict[str, Any] comprising the settings for this command.
        :param tool_namespace: The namespace for the tool (useful for logging).
        """
        pass

    @staticmethod
    def get(tool_namespace: str, database: HammerDatabase) -> "HammerSubmitCommand":
        """
        Get a concrete instance of a HammerSubmitCommand for a tool

        :param tool_namespace: The tool namespace to use when querying the
                               HammerDatabase (e.g. "synthesis" or "par").
        :param database: The HammerDatabase object with tool settings
        """

        submit_command_mode = database.get_setting(tool_namespace + ".submit.command",
                                                   nullvalue="none")
        # pylint: disable=line-too-long
        submit_command_settings = database.get_setting(tool_namespace + ".submit.settings",
                                                       nullvalue=[])  # type: List[Dict[str, Dict[str, Any]]]

        # Settings is a List[Dict[str, Dict[str, Any]]] object. The first Dict
        # key is the submit command name.
        # Its value is a Dict[str, Any] comprising the settings for that command.
        # The top-level list elements are merged from 0 to the last index, with
        # later indices overriding previous entries.
        def combine_settings(settings: List[Dict[str, Dict[str, Any]]], key: str) -> Dict[str, Any]:
            return reduce(add_dicts, map(lambda d: d[key], settings), {})

        submit_command = None  # type: Optional[HammerSubmitCommand]
        if submit_command_mode in {"none", "local"}:  # pylint: disable=no-else-return
            # Do not read the options, return immediately
            return HammerLocalSubmitCommand()
        elif submit_command_mode == "lsf":
            submit_command = HammerLSFSubmitCommand()
        else:
            raise NotImplementedError(
                "Submit command key for {0}: {1} is not implemented".format(
                    tool_namespace, submit_command_mode))

        submit_command.read_settings(
            combine_settings(submit_command_settings, submit_command_mode),
            tool_namespace)
        return submit_command

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


class HammerLocalSubmitCommand(HammerSubmitCommand):

    def submit(self, args: List[str], env: Dict[str, str],
               logger: HammerVLSILoggingContext, cwd: Optional[str] = None) -> Tuple[str, int]:
        # Just run the command on this host.

        prog_tag = self.get_program_tag(args)
        term_settings = termios.tcgetattr(sys.stdin.fileno()) if sys.stdin.isatty() else None

        logger.debug("Executing subprocess: " + ' '.join(args))
        subprocess_logger = logger.context("Exec " + prog_tag)
        proc = subprocess.Popen(args, shell=False, stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE, env=env, cwd=cwd)
        # These are run in reverse order of registration
        # Terminate is first to allow for the possibility of graceful shutdown
        # Then the program will be forceably terminated and we restore the terminal settings
        if term_settings is not None:
            atexit.register(termios.tcsetattr, sys.stdin.fileno(), termios.TCSANOW, term_settings)
        atexit.register(proc.kill)
        atexit.register(proc.terminate)

        output_buf = ""
        # Log output and also capture output at the same time.
        so = proc.stdout
        assert so is not None
        while True:
            line = so.readline().decode("utf-8")
            if line != '':
                subprocess_logger.debug(line.rstrip())
                output_buf += line
            else:
                break
        # check errors
        proc.communicate()

        return output_buf, proc.returncode

    def read_settings(self, settings: Dict[str, Any], tool_namespace: str) -> None:
        # Should never get here
        raise ValueError("Local submission command does not have settings")


class HammerLSFSettings(NamedTuple('HammerLSFSettings', [
    ('bsub_binary', str),
    ('num_cpus', Optional[int]),
    ('queue', Optional[str]),
    ('log_file', Optional[str]),
    ('extra_args', List[str])
])):
    __slots__ = ()

    @staticmethod
    def from_setting(settings: Dict[str, Any]) -> "HammerLSFSettings":
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

    # TODO(johnwright): log the command output

    @property
    def settings(self) -> HammerLSFSettings:
        if not hasattr(self, "_settings"):
            raise ValueError("Nothing set for settings yet")
        return getattr(self, "_settings")

    @settings.setter
    def settings(self, value: HammerLSFSettings) -> None:
        """
        Set the settings class variable

        :param value: The HammerLSFSettings NapedTuple to use
        """
        setattr(self, "_settings", value)

    def read_settings(self, settings: Dict[str, Any], tool_namespace: str) -> None:  # pylint: disable=unused-argument
        self.settings = HammerLSFSettings.from_setting(settings)

    def bsub_args(self) -> List[str]:
        args = [self.settings.bsub_binary, "-K"]  # always use -K to block
        args.extend(["-o", self.settings.log_file if self.settings.log_file is not None else
            datetime.datetime.now().strftime("hammer-vlsi-bsub-%Y%m%d-%H%M%S.log")])  # always use -o to log to a file
        if self.settings.queue is not None:
            args.extend(["-q", self.settings.queue])
        if self.settings.num_cpus is not None:
            args.extend(["-n", "%d" % self.settings.num_cpus])
        args.extend(self.settings.extra_args)
        return args

    def submit(self, args: List[str], env: Dict[str, str],
               logger: HammerVLSILoggingContext, cwd: Optional[str] = None) -> Tuple[str, int]:
        # TODO fix output capturing

        prog_tag = self.get_program_tag(args)

        subprocess_format_str = 'Executing subprocess: {bsub_args} "{args}"'
        logger.debug(subprocess_format_str.format(bsub_args=' '.join(self.bsub_args()),
                                                  args=' '.join(args)))
        subprocess_logger = logger.context("Exec " + prog_tag)
        proc = subprocess.Popen(self.bsub_args() + [' '.join(args)],
                                shell=False, stderr=subprocess.STDOUT,
                                stdout=subprocess.PIPE, env=env, cwd=cwd)

        output_buf = ""
        # Log output and also capture output at the same time.
        so = proc.stdout
        assert so is not None
        while True:
            line = so.readline().decode("utf-8")
            if line != '':
                subprocess_logger.debug(line.rstrip())
                output_buf += line
            else:
                break
        # check errors
        proc.communicate()

        return output_buf, proc.returncode
