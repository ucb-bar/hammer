#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_vlsi.py
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
import inspect
from abc import ABCMeta, abstractmethod
from enum import Enum
from numbers import Number

from typing import Callable, Iterable, List, NamedTuple, Tuple, TypeVar, Type, Optional, Dict, Any, Union, Set

from functools import reduce

import atexit
import datetime
import importlib
import os
import re
import shlex
import subprocess
import sys

import hammer_config


class Level(Enum):
    """
    Logging levels.
    """
    # Explanation of logging levels:
    # DEBUG - for debugging only, too verbose for general use
    # INFO - general informational messages (e.g. "starting synthesis")
    # WARNING - things the user should check out (e.g. a setting uses something very usual)
    # ERROR - something gone wrong but the process can still continue (e.g. synthesis run failed), though the user should definitely check it out.
    # FATAL - an error which will abort the process immediately without warning (e.g. assertion failure)
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL = 4


# Message including additional metadata such as level and context.
FullMessage = NamedTuple('FullMessage', [
    ('message', str),
    ('level', Level),
    ('context', List[str])
])


HammerStepFunction = Callable[['HammerTool'], bool]


class HammerToolPauseException(Exception):
    """
    Internal hammer-vlsi exception raised to indicate that a step has stopped execution of the tool.
    This is not necessarily an error condition.
    """
    pass


def check_hammer_step_function(func: HammerStepFunction) -> None:
    msg = "Function {func} does not meet the required signature".format(func=str(func))

    inspected = inspect.getfullargspec(func)
    annotations = inspected.annotations
    args = inspected.args
    if len(args) != 1:
        raise TypeError(msg)
    else:
        if annotations[args[0]] != HammerTool:
            raise TypeError(msg)
    if annotations['return'] != bool:
        raise TypeError(msg)


HammerToolStep = NamedTuple('HammerToolStep', [
    # Function to call to execute this step
    ('func', HammerStepFunction),
    # Name of the step
    ('name', str)
])


def make_raw_hammer_tool_step(func: HammerStepFunction, name: str) -> HammerToolStep:
    check_hammer_step_function(func)
    return HammerToolStep(func, name)


# Where to insert/replace the given step.
class HookLocation(Enum):
    InsertPreStep = 1
    InsertPostStep = 2
    ReplaceStep = 10
    ResumePreStep = 20
    ResumePostStep = 21


# An hook action. Actions can insert new steps before or after an existing one, or replace an existing stage.
# Note: hook actions are executed in the order provided.
HammerToolHookAction = NamedTuple('HammerToolHookAction', [
    # Where/what to do
    ('location', HookLocation),
    # Target step to insert before/after or replace
    ('target_name', str),
    # Step to insert/replace
    ('step', HammerToolStep)
])

# Need a way to bind the callbacks to the class...
def with_default_callbacks(cls):
    # TODO: think about how to remove default callbacks
    cls.add_callback(cls.callback_print)
    cls.add_callback(cls.callback_buffering)
    return cls

class HammerVLSIFileLogger:
    """A file logger for HammerVLSILogging."""

    def __init__(self, output_path: str, format_msg_callback: Callable[[FullMessage], str] = None) -> None:
        """
        Create a new file logger.

        :param output_path: Output path of the logger.
        :param format_msg_callback: Optional callback to run to build the message. None to use HammerVLSILogging.build_log_message.
        """
        self._file = open(output_path, "a")
        self._format_msg_callback = format_msg_callback

    def __enter__(self):
        return self

    def close(self) -> None:
        """
        Close this file logger.
        """
        self._file.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def callback(self) -> Callable[[FullMessage], None]:
        """Get the callback for HammerVLSILogging.add_callback."""
        def file_callback(fullmessage: FullMessage) -> None:
            if self._format_msg_callback is not None:
                self._file.write(self._format_msg_callback(fullmessage) + "\n")
            else:
                self._file.write(HammerVLSILogging.build_log_message(fullmessage) + "\n")
        return file_callback

@with_default_callbacks
class HammerVLSILogging:
    """Singleton which handles logging in hammer-vlsi.

    This class is generally not intended to be used directly for logging, but through HammerVLSILoggingContext instead.
    """

    # Enable colour in logging?
    enable_colour = True # type: bool

    # If buffering is enabled, instead of printing right away, we will store it
    # into a buffer for later retrival.
    enable_buffering = False # type: bool

    # Enable printing the tag (e.g. "[synthesis] ...).
    enable_tag = True # type: bool

    # Various escape characters for colour output.
    COLOUR_BLUE = "\033[96m"
    COLOUR_GREY = "\033[37m"
    COLOUR_YELLOW = "\033[33m"
    COLOUR_RED = "\033[91m"
    COLOUR_RED_BG = "\033[101m"
    # Restore the default terminal colour.
    COLOUR_CLEAR = "\033[0m"

    # Some default callback implementations.
    @classmethod
    def callback_print(cls, fullmessage: FullMessage) -> None:
        """Default callback which prints a colour message."""
        print(cls.build_message(fullmessage))

    output_buffer = [] # type: List[str]
    @classmethod
    def callback_buffering(cls, fullmessage: FullMessage) -> None:
        """Get the current contents of the logging buffer and clear it."""
        if not cls.enable_buffering:
            return
        cls.output_buffer.append(cls.build_message(fullmessage))

    @classmethod
    def build_log_message(cls, fullmessage: FullMessage) -> str:
        """Build a plain message for logs, without colour."""
        template = "{context} {level}: {message}"

        return template.format(context=cls.get_tag(fullmessage.context), level=fullmessage.level, message=fullmessage.message)

    # List of callbacks to call for logging.
    callbacks = [] # type: List[Callable[[FullMessage], None]]

    @classmethod
    def clear_callbacks(cls) -> None:
        """Clear the list of callbacks."""
        cls.callbacks = []

    @classmethod
    def add_callback(cls, callback: Callable[[FullMessage], None]) -> None:
        """Add a callback."""
        cls.callbacks.append(callback)

    @classmethod
    def context(cls, new_context: str = "") -> "HammerVLSILoggingContext":
        """
        Create a new context.

        :param new_context: Context name. Leave blank to get the global context.
        """
        if new_context == "":
            return HammerVLSILoggingContext([], cls)
        else:
            return HammerVLSILoggingContext([new_context], cls)

    @classmethod
    def get_colour_escape(cls, level: Level) -> str:
        """Colour table to translate level -> colour in logging."""
        table = {
            Level.DEBUG: cls.COLOUR_GREY,
            Level.INFO: cls.COLOUR_BLUE,
            Level.WARNING: cls.COLOUR_YELLOW,
            Level.ERROR: cls.COLOUR_RED,
            Level.FATAL: cls.COLOUR_RED_BG
        }
        if level in table:
            return table[level]
        else:
            return ""

    @classmethod
    def log(cls, fullmessage: FullMessage) -> None:
        """
        Log the given message at the given level in the given context.
        """
        for callback in cls.callbacks:
            callback(fullmessage)

    @classmethod
    def build_message(cls, fullmessage: FullMessage) -> str:
        """Build a colour message."""
        message = fullmessage.message
        level = fullmessage.level
        context = fullmessage.context

        context_tag = cls.get_tag(context) # type: str

        output = "" # type: str
        output += cls.get_colour_escape(level) if cls.enable_colour else ""
        if cls.enable_tag and context_tag != "":
            output += context_tag + " "
        output += message
        output += cls.COLOUR_CLEAR if cls.enable_colour else ""

        return output

    @staticmethod
    def get_tag(context: List[str]) -> str:
        """Helper function to get the tag for outputing a message given a context."""
        if len(context) > 0:
            return str(reduce(lambda a, b: a + " " + b, map(lambda x: "[%s]" % (x), context)))
        else:
            return "[<global>]"

    @classmethod
    def get_buffer(cls) -> Iterable[str]:
        """Get the current contents of the logging buffer and clear it."""
        if not cls.enable_buffering:
            raise ValueError("Buffering is not enabled")
        output = list(cls.output_buffer)
        cls.output_buffer = []
        return output

VT = TypeVar('VT', bound='HammerVLSILoggingContext')
class HammerVLSILoggingContext:
    """
    Logging interface to hammer-vlsi which contains a context (list of strings denoting hierarchy where the log occurred).
    e.g. ["synthesis", "subprocess run-synthesis"]
    """
    def __init__(self, context: List[str], logging_class: Type[HammerVLSILogging]) -> None:
        """
        Create a new interface with the given context.
        """
        self._context = context # type: List[str]
        self.logging_class = logging_class # type: Type[HammerVLSILogging]

    def context(self: VT, new_context: str) -> VT:
        """
        Create a new subcontext from this context.
        """
        context2 = list(self._context)
        context2.append(new_context)
        return HammerVLSILoggingContext(context2, self.logging_class)

    def debug(self, message: str) -> None:
        """Create an debug-level log message."""
        return self.log(message, Level.DEBUG)

    def info(self, message: str) -> None:
        """Create an info-level log message."""
        return self.log(message, Level.INFO)

    def warning(self, message: str) -> None:
        """Create an warning-level log message."""
        return self.log(message, Level.WARNING)

    def error(self, message: str) -> None:
        """Create an error-level log message."""
        return self.log(message, Level.ERROR)

    def fatal(self, message: str) -> None:
        """Create an fatal-level log message."""
        return self.log(message, Level.FATAL)

    def log(self, message: str, level: Level) -> None:
        return self.logging_class.log(FullMessage(message, level, self._context))

import hammer_tech

class HammerVLSISettings:
    """
    Static class which holds global hammer-vlsi settings.
    """
    hammer_vlsi_path = "" # type: str

    @staticmethod
    def get_config() -> dict:
        """Export settings as a config dictionary."""
        return {
            "vlsi.builtins.hammer_vlsi_path": HammerVLSISettings.hammer_vlsi_path
        }

    @classmethod
    def set_hammer_vlsi_path_from_environment(cls) -> bool:
        """
        Try to set hammer_vlsi_path from the environment variable HAMMER_VLSI.
        :return: True if successfully set, False otherwise
        """
        if "HAMMER_VLSI" not in os.environ:
            return False
        else:
            cls.hammer_vlsi_path = os.environ["HAMMER_VLSI"]
            return True


class TimeValue:
    """Time value - e.g. "4 ns".
    Parses time values from strings.
    """

    # From https://stackoverflow.com/a/10970888
    _prefix_table = {
        'y': 1e-24,  # yocto
        'z': 1e-21,  # zepto
        'a': 1e-18,  # atto
        'f': 1e-15,  # femto
        'p': 1e-12,  # pico
        'n': 1e-9,   # nano
        'u': 1e-6,   # micro
        'm': 1e-3,   # mili
        'c': 1e-2,   # centi
        'd': 1e-1,   # deci
        'k': 1e3,    # kilo
        'M': 1e6,    # mega
        'G': 1e9,    # giga
        'T': 1e12,   # tera
        'P': 1e15,   # peta
        'E': 1e18,   # exa
        'Z': 1e21,   # zetta
        'Y': 1e24,   # yotta
    }

    def __init__(self, value: str, default_prefix: str = 'n') -> None:
        """Create a time value from parsing the given string.
        Default prefix: ns
        """
        import re

        regex = r"^([\d.]+) *(.*)s$"
        m = re.search(regex, value)
        if m is None:
            try:
                num = str(float(value))
                prefix = default_prefix
            except ValueError:
                raise ValueError("Malformed time value %s" % (value))
        else:
            num = m.group(1)
            prefix = m.group(2)

        if num.count('.') > 1 or len(prefix) > 1:
            raise ValueError("Malformed time value %s" % (value))

        if prefix not in self._prefix_table:
            raise ValueError("Bad prefix for %s" % (value))

        self._value = float(num) # type: float
        # Preserve the prefix too to preserve precision
        self._prefix = self._prefix_table[prefix] # type: float

    @property
    def value(self) -> float:
        """Get the value of this time value."""
        return self._value * self._prefix

    def value_in_units(self, prefix: str, round_zeroes: bool = True) -> float:
        """Get this time value in the given prefix. e.g. "ns"
        """
        retval = self._value * (self._prefix / self._prefix_table[prefix[0]])
        if round_zeroes:
            return round(retval, 2)
        else:
            return retval

    def str_value_in_units(self, prefix: str, round_zeroes: bool = True) -> str:
        """Get this time value in the given prefix but including the units.
        e.g. return "5 ns".

        :param prefix: Prefix for the resulting value - e.g. "ns".
        :param round_zeroes: True to round 1.00000001 etc to 1 within 2 decimal places.
        """
        # %g removes trailing zeroes
        return "%g" % (self.value_in_units(prefix, round_zeroes)) + " " + prefix


ClockPort = NamedTuple('ClockPort', [
    ('name', str),
    ('period', TimeValue),
    ('port', Optional[str]),
    ('uncertainty', Optional[TimeValue])
])

OutputLoadConstraint = NamedTuple('OutputLoadConstraint', [
    ('name', str),
    ('load', float)
])


class PlacementConstraintType(Enum):
    Dummy = 1
    Placement = 2
    TopLevel = 3
    HardMacro = 4
    Hierarchical = 5

    @staticmethod
    def from_string(s: str) -> "PlacementConstraintType":
        if s == "dummy":
            return PlacementConstraintType.Dummy
        elif s == "placement":
            return PlacementConstraintType.Placement
        elif s == "toplevel":
            return PlacementConstraintType.TopLevel
        elif s == "hardmacro":
            return PlacementConstraintType.HardMacro
        elif s == "hierarchical":
            return PlacementConstraintType.Hierarchical
        else:
            raise ValueError("Invalid placement constraint type '{}'".format(s))

# For the top-level chip size constraint, set the margin from core area to left/bottom/right/top.
Margins = NamedTuple('Margins', [
    ('left', float),
    ('bottom', float),
    ('right', float),
    ('top', float)
])

PlacementConstraint = NamedTuple('PlacementConstraint', [
    ('path', str),
    ('type', PlacementConstraintType),
    ('x', float),
    ('y', float),
    ('width', float),
    ('height', float),
    ('orientation', Optional[str]),
    ('margins', Optional[Margins])
])

class MMMCCornerType(Enum):
    Setup = 1
    Hold = 2
    Extra = 3

    @staticmethod
    def from_string(s: str) -> "MMMCCornerType":
        if s == "setup":
            return MMMCCornerType.Setup
        elif s == "hold":
            return MMMCCornerType.Hold
        elif s == "extra":
            return MMMCCornerType.Extra
        else:
            raise ValueError("Invalid mmmc corner type '{}'".format(s))

MMMCCorner = NamedTuple('MMMCCorner', [
    ('name', str),
    ('type', MMMCCornerType),
    ('voltage', float),
    ('temp', int),
])


# Library filter containing a filtering function, identifier tag, and a
# short human-readable description.
class LibraryFilter(NamedTuple('LibraryFilter', [
    ('tag', str),
    ('description', str),
    # Is the resulting string intended to be a file?
    ('is_file', bool),
    # Function to extract desired string(s) out of the library.
    ('extraction_func', Callable[[hammer_tech.Library], List[str]]),
    # Additional filter function to use to exclude possible libraries.
    ('filter_func', Optional[Callable[[hammer_tech.Library], bool]]),
    # Sort function to control the order in which outputs are listed
    ('sort_func', Optional[Callable[[hammer_tech.Library], Union[Number, str, tuple]]]),
    # List of functions to call on the list-level (the list of elements generated by func) before output and
    # post-processing.
    ('extra_post_filter_funcs', List[Callable[[List[str]], List[str]]])
])):
    __slots__ = ()

    @staticmethod
    def new(
            tag: str, description: str, is_file: bool,
            extraction_func: Callable[[hammer_tech.Library], List[str]],
            filter_func: Optional[Callable[[hammer_tech.Library], bool]] = None,
            sort_func: Optional[Callable[[hammer_tech.Library], Union[Number, str, tuple]]] = None,
            extra_post_filter_funcs: List[Callable[[List[str]], List[str]]] = []) -> "LibraryFilter":
        """Convenience "constructor" with some default arguments."""
        return LibraryFilter(
            tag, description, is_file,
            extraction_func,
            filter_func,
            sort_func,
            list(extra_post_filter_funcs)
        )


class HammerTool(metaclass=ABCMeta):
    # Interface methods.
    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!

        :return: Mapping of environment variable -> contents of said variable.
        """
        return {}

    def export_config_outputs(self) -> Dict[str, Any]:
        """
        Export the outputs of this tool to a config.
        :return: Config dictionary of the outputs of this tool.
        """
        return {}

    # Setup functions.
    def run(self, hook_actions: List[HammerToolHookAction] = []) -> bool:
        """Run this tool.

        Perform some setup operations to set up the config and tool environment, runs the tool-specific actions defined
        in steps, and collects the outputs.

        :return: True if the tool finished successfully; false otherwise.
        """

        # Ensure that the run_dir exists.
        os.makedirs(self.run_dir, exist_ok=True)

        # Run the list of steps defined for this tool.
        if not self.run_steps(self.steps, hook_actions):
            return False

        # Fill the outputs of the tool.
        return self.fill_outputs()

    @property
    @abstractmethod
    def steps(self) -> List[HammerToolStep]:
        """
        List of steps defined for the execution of this tool.
        """
        pass

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        """
        Function to run before the list of steps executes.
        Intended to be overridden by subclasses.
        :param first_step: First step to be taken.
        :return: True if successful, False otherwise.
        """
        return True

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        """
        Function to run after the list of steps executes.
        Does not include pause hooks.
        Intended to be overridden by subclasses.
        :param prev: The step that just finished
        :param next: The next step about to run.
        :return: True if successful, False otherwise.
        """
        return True

    def do_post_steps(self) -> bool:
        """
        Function to run after the list of steps executes.
        Intended to be overridden by subclasses.
        :return: True if successful, False otherwise.
        """
        return True

    def fill_outputs(self) -> bool:
        """
        Fill the outputs of the tool.
        Note: if you override this, remember to call the superclass method too!
        :return: True if successful, False otherwise.
        """
        return True

    @property
    def _subprocess_env(self) -> dict:
        """
        Internal helper function to set the environment variables for
        self.run_executable().
        """
        env = os.environ.copy()
        # Add HAMMER_DATABASE to the environment for the script.
        env.update({"HAMMER_DATABASE": self.dump_database()})
        env.update(self.env_vars)
        return env

    # Properties.
    @property
    def name(self) -> str:
        """
        Short name of the tool library.
        Typically the folder name (e.g. "dc", "yosys", etc).

        :return: Short name of the tool library.
        """
        try:
            return self._name
        except AttributeError:
            raise ValueError("Internal error: Short name of the tool library not set by hammer-vlsi")

    @name.setter
    def name(self, value: str) -> None:
        """Set the Short name of the tool library."""
        self._name = value # type: str

    @property
    def tool_dir(self) -> str:
        """
        Get the location of the tool library.

        :return: Path to the location of the library.
        """
        try:
            return self._tooldir
        except AttributeError:
            raise ValueError("Internal error: tool dir location not set by hammer-vlsi")

    @tool_dir.setter
    def tool_dir(self, value: str) -> None:
        """Set the directory which contains this tool library."""
        self._tooldir = value # type: str

    @property
    def run_dir(self) -> str:
        """
        Get the location of the run dir, a writable temporary information for use by the tool.

        :return: Path to the location of the library.
        """
        try:
            return self._rundir
        except AttributeError:
            raise ValueError("Internal error: run dir location not set by hammer-vlsi")

    @run_dir.setter
    def run_dir(self, value: str) -> None:
        """Set the location of a writable directory which the tool can use to store temporary information."""
        self._rundir = value # type: str

    @property
    def input_files(self) -> Iterable[str]:
        """
        Input files for this tool library.
        The exact nature of the files will depend on the type of library.
        """
        try:
            return self._input_files
        except AttributeError:
            raise ValueError("Nothing set for inputs yet")

    @input_files.setter
    def input_files(self, value: Iterable[str]) -> None:
        """
        Set the input files for this tool library.
        The exact nature of the files will depend on the type of library.
        """
        if not isinstance(value, Iterable):
            raise TypeError("input_files must be a Iterable[str]")
        self._input_files = value # type: Iterable[str]

    @property
    def technology(self) -> hammer_tech.HammerTechnology:
        """
        Get the technology library currently in use.

        :return: HammerTechnology instance
        """
        try:
            return self._technology
        except AttributeError:
            raise ValueError("Internal error: technology not set by hammer-vlsi")

    @technology.setter
    def technology(self, value: hammer_tech.HammerTechnology) -> None:
        """Set the HammerTechnology currently in use."""
        self._technology = value # type: hammer_tech.HammerTechnology

    @property
    def logger(self) -> HammerVLSILoggingContext:
        """Get the logger for this tool."""
        try:
            return self._logger
        except AttributeError:
            raise ValueError("Internal error: logger not set by hammer-vlsi")

    @logger.setter
    def logger(self, value: HammerVLSILoggingContext) -> None:
        """Set the logger for this tool."""
        self._logger = value # type: HammerVLSILoggingContext

    ##############################
    # Implementation helpers for properties
    ##############################
    def attr_getter(self, key: str, default: Any) -> Any:
        """Helper function for implementing the getter of a property with a default."""
        if not hasattr(self, key):
            setattr(self, key, default)
        return getattr(self, key)

    def attr_setter(self, key: str, value: Any) -> None:
        """Helper function for implementing the setter of a property with a default."""
        setattr(self, key, value)

    ##############################
    # Hooks
    ##############################
    def check_duplicates(self, lst: List[HammerToolStep]) -> Tuple[bool, Set[str]]:
        """Check that no two steps have the same name."""
        seen_names = set()  # type: Set[str]
        for step in lst:
            if step.name in seen_names:
                self.logger.error("Duplicate step '{step}' encountered".format(step=step.name))
                return False, set()
            else:
                seen_names.add(step.name)
        return True, seen_names

    def run_steps(self, steps: List[HammerToolStep], hook_actions: List[HammerToolHookAction] = []) -> bool:
        """
        Run the given steps, checking for errors/conditions between each step.
        :param steps: List of steps.
        :param hook_actions: List of hook actions.
        :return: Returns true if all the steps are successful.
        """
        duplicate_free, names = self.check_duplicates(steps)
        if not duplicate_free:
            return False

        def has_step(name: str) -> bool:
            return name in names

        # Copy the list of steps
        new_steps = list(steps)

        # Where to resume, if such a hook exists
        resume_step = None  # type: Optional[str]
        # If resume_step is not None, whether to resume pre or post this step
        resume_step_pre = True  # type: bool

        for action in hook_actions:
            if not has_step(action.target_name):
                self.logger.error("Target step '{step}' does not exist".format(step=action.target_name))
                return False

            step_id = -1
            for i in range(len(new_steps)):
                if new_steps[i].name == action.target_name:
                    step_id = i
                    break
            assert step_id != -1

            if action.location == HookLocation.ReplaceStep:
                assert action.target_name == action.step.name, "Replacement step should have the same name"
                new_steps[step_id] = action.step
            elif action.location == HookLocation.InsertPreStep:
                if has_step(action.step.name):
                    self.logger.error("New step '{step}' already exists".format(step=action.step.name))
                    return False
                new_steps.insert(step_id, action.step)
                names.add(action.step.name)
            elif action.location == HookLocation.InsertPostStep:
                if has_step(action.step.name):
                    self.logger.error("New step '{step}' already exists".format(step=action.step.name))
                    return False
                new_steps.insert(step_id + 1, action.step)
                names.add(action.step.name)
            elif action.location == HookLocation.ResumePreStep or action.location == HookLocation.ResumePostStep:
                if resume_step is not None:
                    self.logger.error("More than one resume hook is present")
                    return False
                resume_step = action.target_name
                resume_step_pre = action.location == HookLocation.ResumePreStep
            else:
                assert False, "Should not reach here"

        # Check function types before running
        for step in new_steps:
            if not isinstance(step, HammerToolStep):
                raise ValueError("Element in List[HammerToolStep] is not a HammerToolStep")
            check_hammer_step_function(step.func)

        # Run steps.
        prev_step = None  # type: HammerToolStep

        for step_index in range(len(new_steps)):
            step = new_steps[step_index]

            self.logger.debug("Running sub-step '{step}'".format(step=step.name))

            # Do this step?
            do_step = True

            if resume_step is not None:
                if resume_step_pre:
                    if resume_step == step.name:
                        self.logger.info("Resuming before '{step}' due to resume hook".format(step=step.name))
                        # Remove resume marker
                        resume_step = None
                    else:
                        self.logger.info("Sub-step '{step}' skipped due to resume hook".format(step=step.name))
                        do_step = False
                else:
                    self.logger.info("Sub-step '{step}' skipped due to resume hook".format(step=step.name))
                    do_step = False

            if do_step:
                try:
                    if prev_step is None:
                        # Run pre-step hook.
                        self.do_pre_steps(step)
                    else:
                        # TODO: find a cleaner way of detecting a pause hook
                        if step.name == "pause":
                            # Don't include "pause" for do_between_steps
                            if step_index + 1 < len(new_steps):
                                self.do_between_steps(prev_step, new_steps[step_index + 1])
                        else:
                            self.do_between_steps(prev_step, step)
                    func_out = step.func(self)  # type: bool
                    prev_step = step
                except HammerToolPauseException:
                    self.logger.info("Sub-step '{step}' paused the tool execution".format(step=step.name))
                    break
                assert isinstance(func_out, bool)
                if not func_out:
                    return False

            if resume_step is not None:
                if not resume_step_pre and resume_step == step.name:
                    self.logger.info("Resuming after '{step}' due to resume hook".format(step=step.name))
                    resume_step = None

        # Run post-steps hook.
        self.do_post_steps()

        return True

    @staticmethod
    def make_step_from_method(func: Callable[[], bool], name: str = "") -> HammerToolStep:
        """
        Create a HammerToolStep from a method.
        :param func: Method for the given substep (e.g. self.elaborate)
        :param name: Name of the hook. If unspecified, defaults to func.__name__.
        :return: A HammerToolStep defining this step.
        """
        if not callable(func):
            raise TypeError("func is not callable")
        if not hasattr(func, "__self__"):
            raise ValueError("This function does not take unbound functions")
        annotations = inspect.getfullargspec(func).annotations
        if annotations != {'return': bool}:
            raise TypeError("Function {func} does not meet the required signature".format(func=str(func)))

        # Wrapper to make __func__ take a proper type annotation for "self"
        def wrapper(x: HammerTool) -> bool:
            return func.__func__(x)  # type: ignore # no type stub for builtin __func__

        if name == "":
            name = func.__name__
        return make_raw_hammer_tool_step(func=wrapper, name=name)

    @staticmethod
    def make_steps_from_methods(funcs: List[Callable[[], bool]]) -> List[HammerToolStep]:
        """
        Create a series of HammerToolStep from the given list of bound methods.
        :param funcs: List of bound methods (e.g. [self.step1, self.step2])
        :return: List of HammerToolSteps
        """
        return list(map(lambda x: HammerTool.make_step_from_method(x), funcs))

    @staticmethod
    def make_step_from_function(func: HammerStepFunction, name: str = "") -> HammerToolStep:
        """
        Create a HammerToolStep from a function.
        :param func: Class function for the given substep
        :param name: Name of the hook. If unspecified, defaults to func.__name__.
        :return: A HammerToolStep defining this step.
        """
        if hasattr(func, "__self__"):
            raise ValueError("This function does not take bound methods")
        if name == "":
            name = func.__name__
        return make_raw_hammer_tool_step(func=func, name=name)

    @staticmethod
    def make_pause_function() -> HammerStepFunction:
        """
        Get a step function which will stop the execution of the tool.
        """
        def pause(x: HammerTool) -> bool:
            raise HammerToolPauseException()
        return pause

    @staticmethod
    def make_replacement_hook(step: str, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Create a hook action which replaces an existing step.
        :return: Hook action which replaces the given step.
        """
        return HammerToolHookAction(
            target_name=step,
            location=HookLocation.ReplaceStep,
            step=HammerTool.make_step_from_function(func, step)
        )

    @staticmethod
    def make_insertion_hook(step: str, location: HookLocation, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Create a hook action is inserted relative to the given step.
        """
        if location != HookLocation.InsertPreStep and location != HookLocation.InsertPostStep:
            raise ValueError("Insertion hook location must be Insert*")

        return HammerToolHookAction(
            target_name=step,
            location=location,
            step=HammerTool.make_step_from_function(func)
        )

    @staticmethod
    def make_resume_hook(step: str, location: HookLocation) -> HammerToolHookAction:
        """
        Create a hook action is inserted relative to the given step.
        """
        if location != HookLocation.ResumePreStep and location != HookLocation.ResumePostStep:
            raise ValueError("Resume hook location must be Resume*")

        return HammerToolHookAction(
            target_name=step,
            location=location,
            step=None
        )

    @staticmethod
    def make_pre_pause_hook(step: str) -> HammerToolHookAction:
        """
        Create pause before the execution of the given step.
        """
        return HammerTool.make_insertion_hook(step, HookLocation.InsertPreStep, HammerTool.make_pause_function())

    @staticmethod
    def make_post_pause_hook(step: str) -> HammerToolHookAction:
        """
        Create pause before the execution of the given step.
        """
        return HammerTool.make_insertion_hook(step, HookLocation.InsertPostStep, HammerTool.make_pause_function())

    @staticmethod
    def make_pre_resume_hook(step: str) -> HammerToolHookAction:
        """
        Resume before the given step.
        Note that only one resume hook may be present.
        """
        return HammerTool.make_resume_hook(step, HookLocation.ResumePreStep)

    @staticmethod
    def make_post_resume_hook(step: str) -> HammerToolHookAction:
        """
        Resume after the given step.
        Note that only one resume hook may be present.
        """
        return HammerTool.make_resume_hook(step, HookLocation.ResumePostStep)

    @staticmethod
    def make_from_to_hooks(from_step: Optional[str] = None,
                           to_step: Optional[str] = None) -> List[HammerToolHookAction]:
        """
        Helper function to create a HammerToolHookAction list which will run from and to the given steps, inclusive.
        :param from_step: Run from the given step, inclusive. Leave as None to resume from the beginning.
        :param to_step: Run to the given step, inclusive. Leave as None to run to the end.
        :return: HammerToolHookAction list for running from and to the given steps, inclusive.
        """
        output = []  # type: List[HammerToolHookAction]
        if from_step is not None:
            output.append(HammerTool.make_pre_resume_hook(from_step))
        if to_step is not None:
            output.append(HammerTool.make_post_pause_hook(to_step))
        return output

    @staticmethod
    def make_pre_insertion_hook(step: str, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Create a hook action is inserted prior to the given step.
        """
        return HammerTool.make_insertion_hook(step, HookLocation.InsertPreStep, func)

    @staticmethod
    def make_post_insertion_hook(step: str, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Create a hook action is inserted after the given step.
        """
        return HammerTool.make_insertion_hook(step, HookLocation.InsertPostStep, func)

    @staticmethod
    def make_removal_hook(step: str) -> HammerToolHookAction:
        """
        Helper function to remove a step by replacing it with an empty step.
        :return: Hook action which replaces the given step.
        """
        def dummy_step(x: HammerTool) -> bool:
            return True
        return HammerToolHookAction(
            target_name=step,
            location=HookLocation.ReplaceStep,
            step=HammerTool.make_step_from_function(dummy_step, step)
        )


    ##############################
    # Accessory functions available to tools.
    # TODO(edwardw): maybe move set_database/get_setting into an interface like UsesHammerDatabase?
    ##############################
    def set_database(self, database: hammer_config.HammerDatabase) -> None:
        """Set the settings database for use by the tool."""
        self._database = database # type: hammer_config.HammerDatabase

    def dump_database(self) -> str:
        """Dump the current database JSON in a temporary file in the run_dir and return the path.
        """
        path = os.path.join(self.run_dir, "config_db_tmp.json")
        db_contents = self._database.get_database_json()
        with open(path, 'w') as f:
            f.write(db_contents)
        return path

    def get_config(self) -> List[dict]:
        """Get the config for this tool."""
        return hammer_config.load_config_from_defaults(self.tool_dir)

    def get_setting(self, key: str, nullvalue: Optional[str] = None):
        """
        Get a particular setting from the database.
        :param key: Key of the setting to receive.
        :param nullvalue: Value to return in case of null (leave as None to use the default).
        """
        try:
            if nullvalue is None:
                return self._database.get_setting(key)
            else:
                return self._database.get_setting(key, nullvalue)
        except AttributeError:
            raise ValueError("Internal error: no database set by hammer-vlsi")

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a runtime setting in the database.
        """
        self._database.set_setting(key, value)

    def create_enter_script(self, enter_script_location: str = "", raw: bool = False) -> None:
        """
        Create the enter script inside the rundir which can be used to
        create an interactive environment with all the same variables
        used to launch this tool.

        :param enter_script_location: Location to create the enter script. Defaults to self.run_dir + "/enter"
        :param raw: Emit the raw string without shell escaping (without quotes!!!)
        """
        def escape_value(val: str) -> str:
            if raw:
                return val
            else:
                if val == "":
                    return '""'
                quoted = shlex.quote(val) # type: str
                # For readability e.g. export X="9" vs export X=9
                if quoted == val:
                    return '"' + val + '"'
                else:
                    return quoted

        if enter_script_location == "":
            enter_script_location = os.path.join(self.run_dir, "enter")
        enter_script = "\n".join(map(lambda k_v: "export {0}={1}".format(k_v[0], escape_value(k_v[1])), sorted(self.env_vars.items())))
        with open(enter_script_location, "w") as f:
            f.write(enter_script)

    def check_input_files(self, extensions: List[str]) -> bool:
        """Verify that input files exist and have the specified extensions.

        :param extensions: List of extensions e.g. [".v", ".sv"]
        :return: True if all files exist and have the specified extensions.
        """
        verilog_args = self.input_files
        error = False
        for v in verilog_args:
            if not v.endswith(tuple(extensions)):
                self.logger.error("Input of unsupported type {0} detected!".format(v))
                error = True
            if not os.path.isfile(v):
                self.logger.error("Input file {0} does not exist!".format(v))
                error = True
        return not error

    # TODO: should some of these live in hammer_tech instead?
    def filter_and_select_libs(self,
                               lib_filters: List[Callable[[hammer_tech.Library], bool]] = [],
                               sort_func: Optional[Callable[[hammer_tech.Library], Union[Number, str, tuple]]] = None,
                               extraction_func: Callable[[hammer_tech.Library], List[str]] = None,
                               extra_funcs: List[Callable[[str], str]] = [],
                               ) -> List[str]:
        """
        Generate a list by filtering the list of libraries and selecting some parts of it.

        :param lib_filters: Filters to filter the list of libraries before selecting desired results from them.
        e.g. remove libraries of the wrong type
        :param sort_func: Sort function to re-order the resultant components.
        e.g. put stdcell libraries before any other libraries
        :param extraction_func: Function to call to extract the desired component of the lib.
        e.g. turns the library into the ".lib" file corresponding to that library
        :param extra_funcs: List of extra functions to call before wrapping them in the arg prefixes.

        :return: List generated from list of libraries
        """
        if extraction_func is None:
            raise TypeError("extraction_func is required")

        filtered_libs = reduce_named(
            sequence=lib_filters,
            initial=self.technology.config.libraries,
            function=lambda libs, func: filter(func, libs)
        )

        if sort_func is not None:
            filtered_libs = sorted(filtered_libs, key=sort_func)

        lib_results = list(reduce(self.util_add_lists, list(map(extraction_func, filtered_libs))))  # type: List[str]

        # Uniquify results.
        # TODO: think about whether this really belongs here and whether we always need to uniquify.
        # This is here to get stuff working since some CAD tools dislike duplicated arguments (e.g. duplicated stdcell
        # lib, etc).
        self.util_in_place_unique(lib_results)

        lib_results_with_extra_funcs = reduce(lambda arr, extra_func: map(extra_func, arr), extra_funcs, lib_results)

        return list(lib_results_with_extra_funcs)

    def filter_for_supplies(self, lib: hammer_tech.Library) -> bool:
        """Function to help filter a list of libraries to find libraries which have matching supplies.
        Will also use libraries with no supplies annotation.

        :param lib: Library to check
        :return: True if the supplies of this library match the inputs for this run, False otherwise.
        """
        if lib.supplies is None:
            # TODO: add some sort of wildcard value for supplies for libraries which _actually_ should
            # always be used.
            self.logger.warning("Lib %s has no supplies annotation! Using anyway." % (lib.serialize()))
            return True
        return self.get_setting("vlsi.inputs.supplies.VDD") == lib.supplies.VDD and self.get_setting("vlsi.inputs.supplies.GND") == lib.supplies.GND

    def filter_for_mmmc(self, voltage, temp) -> Callable[[hammer_tech.Library],bool]:
        """
        Selecting libraries that match given temp and voltage.
        """
        def extraction_func(lib: hammer_tech.Library) -> bool:
            if lib.corner is None or lib.corner.temperature is None:
                return False
            if lib.supplies is None or lib.supplies.VDD is None:
                return False
            if lib.corner.temperature == temp:
                if lib.supplies.VDD == voltage:
                    return True
                else:
                    return False
            else:
                return False
        return extraction_func

    @staticmethod
    def make_check_isdir(description: str = "Path") -> Callable[[str], str]:
        """
        Utility function to generate functions which check whether a path exists.
        """
        def check_isdir(path: str) -> str:
            if not os.path.isdir(path):
                raise ValueError("%s %s is not a directory or does not exist" % (description, path))
            else:
                return path
        return check_isdir

    @staticmethod
    def make_check_isfile(description: str = "File") -> Callable[[str], str]:
        """
        Utility function to generate functions which check whether a path exists.
        """
        def check_isfile(path: str) -> str:
            if not os.path.isfile(path):
                raise ValueError("%s %s is not a file or does not exist" % (description, path))
            else:
                return path
        return check_isfile

    @staticmethod
    def replace_tcl_set(variable: str, value: str, tcl_path: str, quotes: bool = True) -> None:
        """
        Utility function to replaces a "set VARIABLE ..." line with set VARIABLE
        "value" in the given TCL script file.

        :param variable: Variable name to replace
        :param value: Value to replace it with (default quoted)
        :param tcl_path: Path to the TCL script.
        :param quotes: (optional) Set to False to disable quoting of the value.
        """
        with open(tcl_path, "r") as f:
            tcl_contents = f.read() # type: str

        value_string = value
        if quotes:
            value_string = '"' + value_string + '"'
        replacement_string = "set %s %s;" % (variable, value_string)

        regex = r'^set +%s.*' % (re.escape(variable))
        if re.search(regex, tcl_contents, flags=re.MULTILINE) is None:
            raise ValueError("set %s line not found in tcl file %s!" % (variable, tcl_path))

        new_tcl_contents = re.sub(regex, replacement_string, tcl_contents, flags=re.MULTILINE) # type: str

        with open(tcl_path, "w") as f:
            f.write(new_tcl_contents)

    # TODO(edwardw): consider pulling this out so that hammer_tech can also use this
    def run_executable(self, args: List[str], cwd: str = None) -> str:
        """
        Run an executable and log the command to the log while also capturing the output.

        :param args: Command-line to run; each item in the list is one token. The first token should be the command to run.
        :param cwd: Working directory (leave as None to use the current working directory).
        :return: Output from the command or an error message.
        """
        self.logger.debug("Executing subprocess: " + ' '.join(args))

        # Short version for easier display in the log.
        PROG_NAME_LEN = 14 # Capture last 14 characters of the command name
        if len(args[0]) <= PROG_NAME_LEN:
            prog_name = args[0]
        else:
            prog_name = "..." + args[0][len(args[0])-PROG_NAME_LEN:]
        remaining_args = " ".join(args[1:])
        if len(remaining_args) <= 15:
            prog_args = remaining_args
        else:
            prog_args = remaining_args[0:15] + "..."
        prog_tag = prog_name + " " + prog_args
        subprocess_logger = self.logger.context("Exec " + prog_tag)

        proc = subprocess.Popen(args, shell=False, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, env=self._subprocess_env, cwd=cwd)
        atexit.register(proc.kill)
        # Log output and also capture output at the same time.
        output_buf = ""
        while True:
            line = proc.stdout.readline().decode("utf-8")
            if line != '':
                subprocess_logger.debug(line.rstrip())
                output_buf += line
            else:
                break
        # TODO: check errors
        return line

    # Common convenient filters useful to many different tools.
    @staticmethod
    def create_nonempty_check(description: str) -> Callable[[List[str]], List[str]]:
        def check_nonempty(l: List[str]) -> List[str]:
            if len(l) == 0:
                raise ValueError("Must have at least one " + description)
            else:
                return l
        return check_nonempty

    @staticmethod
    def to_command_line_args(lib_item: str, filt: LibraryFilter) -> List[str]:
        """
        Generate command-line args in the form --<filt.tag> <lib_item>.
        """
        return ["--" + filt.tag, lib_item]

    @staticmethod
    def to_plain_item(lib_item: str, filt: LibraryFilter) -> List[str]:
        """
        Generate plain outputs in the form of <lib_item1> <lib_item2> ...
        """
        return [lib_item]

    @property
    def timing_db_filter(self) -> LibraryFilter:
        """
        Selecting Synopsys timing libraries (.db). Prefers CCS if available; picks NLDM as a fallback.
        """

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_library_file is not None:
                return [lib.ccs_library_file]
            elif lib.nldm_library_file is not None:
                return [lib.nldm_library_file]
            else:
                return []

        return LibraryFilter.new("timing_db", "CCS/NLDM timing lib (Synopsys .db)", extraction_func=extraction_func,
                                 is_file=True)

    @property
    def liberty_lib_filter(self) -> LibraryFilter:
        """
        Selecting ASCII liberty (.lib) libraries. Prefers CCS if available; picks NLDM as a fallback.
        """

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib", "CCS/NLDM timing lib (liberty ASCII .lib)",
                                 extraction_func=extraction_func, is_file=True)

    @property
    def qrc_tech_filter(self) -> LibraryFilter:
        """
        Selecting qrc RC Corner tech (qrcTech) files.
        """

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            if lib.qrc_techfile is not None:
                return [lib.qrc_techfile]
            else:
                return []

        return LibraryFilter.new("qrc", "qrc RC corner tech file",
                                 extraction_func=extraction_func, is_file=True)

    @property
    def lef_filter(self) -> LibraryFilter:
        """
        Select LEF files for physical layout.
        """

        def filter_func(lib: hammer_tech.Library) -> bool:
            return lib.lef_file is not None

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            assert lib.lef_file is not None
            return [lib.lef_file]

        def sort_func(lib: hammer_tech.Library):
            if lib.provides is not None:
                for provided in lib.provides:
                    if provided.lib_type is not None and provided.lib_type == "technology":
                        return 0  # put the technology LEF in front
            return 100  # put it behind

        return LibraryFilter.new("lef", "LEF physical design layout library", is_file=True, filter_func=filter_func,
                                 extraction_func=extraction_func, sort_func=sort_func)

    @property
    def milkyway_lib_dir_filter(self) -> LibraryFilter:
        def select_milkyway_lib(lib: hammer_tech.Library) -> List[str]:
            if lib.milkyway_lib_in_dir is not None:
                return [os.path.dirname(lib.milkyway_lib_in_dir)]
            else:
                return []

        return LibraryFilter.new("milkyway_dir", "Milkyway lib", is_file=False, extraction_func=select_milkyway_lib)

    @property
    def milkyway_techfile_filter(self) -> LibraryFilter:
        """Select milkyway techfiles."""

        def select_milkyway_tfs(lib: hammer_tech.Library) -> List[str]:
            if lib.milkyway_techfile is not None:
                return [lib.milkyway_techfile]
            else:
                return []

        return LibraryFilter.new("milkyway_tf", "Milkyway techfile", is_file=True, extraction_func=select_milkyway_tfs,
                                 extra_post_filter_funcs=[self.create_nonempty_check("Milkyway techfile")])

    @property
    def tlu_max_cap_filter(self) -> LibraryFilter:
        """TLU+ max cap filter."""

        def select_tlu_max_cap(lib: hammer_tech.Library) -> List[str]:
            if lib.tluplus_files is not None and lib.tluplus_files.max_cap is not None:
                return [lib.tluplus_files.max_cap]
            else:
                return []

        return LibraryFilter.new("tlu_max", "TLU+ max cap db", is_file=True, extraction_func=select_tlu_max_cap)

    @property
    def tlu_min_cap_filter(self) -> LibraryFilter:
        """TLU+ min cap filter."""

        def select_tlu_min_cap(lib: hammer_tech.Library) -> List[str]:
            if lib.tluplus_files is not None and lib.tluplus_files.min_cap is not None:
                return [lib.tluplus_files.min_cap]
            else:
                return []

        return LibraryFilter.new("tlu_min", "TLU+ min cap db", is_file=True, extraction_func=select_tlu_min_cap)

    def process_library_filter(self, pre_filts: Iterable[Callable[[hammer_tech.Library], bool]], filt: LibraryFilter, output_func: Callable[[str, LibraryFilter], List[str]],
                               must_exist: bool = True) -> List[str]:
        """
        Process the given library filter and return a list of items from that library filter with any extra
        post-processing.

        - Get a list of lib items
        - Run any extra_post_filter_funcs (if needed)
        - For every lib item in each lib items, run output_func
        :param filt: LibraryFilter to check against the list.
        :param output_func: Function which processes the outputs, taking in the filtered lib and the library filter
                            which generated it.
        :param must_exist: Must each library item actually exist? Default: True (yes, they must exist)
        :return: Resultant items from the filter and post-processed. (e.g. --timing foo.db --timing bar.db)
        """
        if must_exist:
            existence_check_func = self.make_check_isfile(filt.description) if filt.is_file else self.make_check_isdir(
                filt.description)
        else:
            existence_check_func = lambda x: x  # everything goes

        lib_filters = pre_filts
        if filt.filter_func is not None:
            lib_filters.append(filt.filter_func)
        lib_items = self.filter_and_select_libs(
            lib_filters=lib_filters,
            sort_func=filt.sort_func,
            extraction_func=filt.extraction_func,
            extra_funcs=[self.technology.prepend_dir_path, existence_check_func])  # type: List[str]

        # Quickly check that lib_items is actually a List[str].
        if not isinstance(lib_items, List):
            raise TypeError("lib_items is not a List[str], but a " + str(type(lib_items)))
        for i in lib_items:
            if not isinstance(i, str):
                raise TypeError("lib_items is a List but not a List[str]")

        # Apply any list-level functions.
        after_post_filter = reduce_named(
            sequence=filt.extra_post_filter_funcs,
            initial=lib_items,
            function=lambda libs, func: func(list(libs)),
        )

        # Finally, apply any output functions.
        # e.g. turning foo.db into ["--timing", "foo.db"].
        after_output_functions = map(lambda item: output_func(item, filt), after_post_filter)

        # Concatenate lists of List[str] together.
        return list(reduce(self.util_add_lists, after_output_functions, []))

    def read_libs(self, library_types: Iterable[LibraryFilter], output_func: Callable[[str, LibraryFilter], List[str]],
            pre_filters: Iterable[Callable[[hammer_tech.Library],bool]] = [],
            must_exist: bool = True) -> List[str]:
        """
        Read the given libraries and return a list of strings according to some output format.

        :param library_types: List of libraries to filter, specified as a list of LibraryFilter elements.
        :param output_func: Function which processes the outputs, taking in the filtered lib and the library filter
                            which generated it.
        :param must_exist: Must each library item actually exist? Default: True (yes, they must exist)
        :return: List of filtered libraries processed according output_func.
        """
        if pre_filters == []:
            pre_filters = [self.filter_for_supplies]
        return list(reduce(
            self.util_add_lists,
            map(
                lambda lib: self.process_library_filter(pre_filts=pre_filters, filt=lib, output_func=output_func, must_exist=must_exist),
                library_types
            )
        ))

    @staticmethod
    def util_add_lists(a: List[str], b: List[str]) -> List[str]:
        """Helper method: join two lists together while type checking."""
        # TODO: move this to a util class/package eventually
        assert isinstance(a, List)
        assert isinstance(b, List)
        return a + b

    @staticmethod
    def util_in_place_unique(items: List[Any]) -> None:
        """
        "Fast" in-place uniquification of a list.
        :param items: List to be uniquified.
        """
        seen = set()  # type: Set[Any]
        i = 0
        # We will be all done when i == len(items)
        while i < len(items):
            item = items[i]
            if item in seen:
                # Delete and keep index pointer the same.
                del items[i]
                continue
            else:
                seen.add(item)
                i += 1

    # TODO: these helper functions might get a bit out of hand, put them somewhere more organized?
    def get_clock_ports(self) -> List[ClockPort]:
        """
        Get the clock ports of the top-level module, as specified in vlsi.inputs.clocks.
        """
        clocks = self.get_setting("vlsi.inputs.clocks")
        output = [] # type: List[ClockPort]
        for clock_port in clocks:
            clock = ClockPort(
                name=clock_port["name"], period=TimeValue(clock_port["period"]),
                uncertainty=None, port=None
            )
            if "port" in clock_port:
                clock = clock._replace(port=clock_port["port"])
            if "uncertainty" in clock_port:
                clock = clock._replace(uncertainty=TimeValue(clock_port["uncertainty"]))
            output.append(clock)
        return output

    def get_placement_constraints(self) -> List[PlacementConstraint]:
        """
        Get a list of placement constraints as specified in the config.
        """
        constraints = self.get_setting("vlsi.inputs.placement_constraints")
        output = []  # type: List[PlacementConstraint]
        for constraint in constraints:
            constraint_type = PlacementConstraintType.from_string(str(constraint["type"]))
            margins = None  # type: Optional[Margins]
            orientation = None # type: Optional[str]
            if constraint_type == PlacementConstraintType.TopLevel:
                margins_dict = constraint["margins"]
                margins = Margins(
                    left=float(margins_dict["left"]),
                    bottom=float(margins_dict["bottom"]),
                    right=float(margins_dict["right"]),
                    top=float(margins_dict["top"])
                )
            if "orientation" in constraint:
                orientation = str(constraint["orientation"])
            load = PlacementConstraint(
                path=str(constraint["path"]),
                type=constraint_type,
                x=float(constraint["x"]),
                y=float(constraint["y"]),
                width=float(constraint["width"]),
                height=float(constraint["height"]),
                orientation=orientation,
                margins=margins
            )
            output.append(load)
        return output

    def get_mmmc_corners(self) -> List[MMMCCorner]:
        """
        Get a list of MMMC corners as specified in the config.
        """
        corners = self.get_setting("vlsi.inputs.mmmc_corners")
        output = []  # type: List[MMMCCorner]
        for corner in corners:
            corner_type = MMMCCornerType.from_string(str(corner["type"]))
            corn = MMMCCorner(
                name=str(corner["name"]),
                type=corner_type,
                voltage=str(corner["voltage"]),
                temp=str(corner["temp"]),
            )
            output.append(corn)
        return output

    def get_output_load_constraints(self) -> List[OutputLoadConstraint]:
        """
        Get a list of output load constraints as specified in the config.
        """
        output_loads = self.get_setting("vlsi.inputs.output_loads")
        output = []  # type: List[OutputLoadConstraint]
        for load_src in output_loads:
            load = OutputLoadConstraint(
                name=str(load_src["name"]),
                load=float(load_src["load"])
            )
            output.append(load)
        return output

    @staticmethod
    def append_contents_to_path(content_to_append: str, target_path: str) -> None:
        """
        Append the given contents to the file located at target_path, if target_path is not empty.
        :param content_to_append: Content to append.
        :param target_path: Where to append the content.
        """
        if content_to_append != "":
            content_lines = content_to_append.split("\n")  # type: List[str]

            # TODO(edwardw): come up with a more generic "source locator" for hammer
            header_text = "# The following snippet was added by HAMMER"
            content_lines.insert(0, header_text)

            with open(target_path, "a") as f:
                f.write("\n".join(content_lines))

    @staticmethod
    def tcl_append(cmd: str, output_buffer: List[str]) -> None:
        """
        Helper function to echo and run a command.
        :param cmd: TCL command to run
        :param output_buffer: Buffer in which to enqueue the resulting TCL lines.
        """
        output_buffer.append(cmd)

    @staticmethod
    def verbose_tcl_append(cmd: str, output_buffer: List[str]) -> None:
        """
        Helper function to echo and run a command.
        :param cmd: TCL command to run
        :param output_buffer: Buffer in which to enqueue the resulting TCL lines.
        """
        output_buffer.append("""puts "{0}" """.format(cmd.replace('"', '\"')))
        output_buffer.append(cmd)

class HammerSynthesisTool(HammerTool):
    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = dict(super().export_config_outputs())
        outputs["synthesis.outputs.output_files"] = self.output_files
        outputs["synthesis.inputs.input_files"] = self.input_files
        outputs["synthesis.inputs.top_module"] = self.top_module
        return outputs

    ### Inputs ###

    @property
    def input_files(self) -> Iterable[str]:
        """
        Get the input collection of source RTL files (e.g. *.v).

        :return: The input collection of source RTL files (e.g. *.v).
        """
        try:
            return self._input_files
        except AttributeError:
            raise ValueError("Nothing set for the input collection of source RTL files (e.g. *.v) yet")

    @input_files.setter
    def input_files(self, value: Iterable[str]) -> None:
        """Set the input collection of source RTL files (e.g. *.v)."""
        if not isinstance(value, Iterable):
            raise TypeError("input_files must be a Iterable[str]")
        self._input_files = value  # type: Iterable[str]

    @property
    def top_module(self) -> str:
        """
        Get the top-level module.

        :return: The top-level module.
        """
        try:
            return self._top_module
        except AttributeError:
            raise ValueError("Nothing set for the top-level module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top-level module."""
        if not isinstance(value, str):
            raise TypeError("top_module must be a str")
        self._top_module = value  # type: str

    ### Outputs ###

    @property
    def output_files(self) -> Iterable[str]:
        """
        Get the output collection of mapped (post-synthesis) RTL files.

        :return: The output collection of mapped (post-synthesis) RTL files.
        """
        try:
            return self._output_files
        except AttributeError:
            raise ValueError("Nothing set for the output collection of mapped (post-synthesis) RTL files yet")

    @output_files.setter
    def output_files(self, value: Iterable[str]) -> None:
        """Set the output collection of mapped (post-synthesis) RTL files."""
        if not isinstance(value, Iterable):
            raise TypeError("output_files must be a Iterable[str]")
        self._output_files = value  # type: Iterable[str]

    @property
    def output_sdc(self) -> str:
        """
        Get the (optional) output post-synthesis SDC constraints file.

        :return: The (optional) output post-synthesis SDC constraints file.
        """
        try:
            return self._output_sdc
        except AttributeError:
            raise ValueError("Nothing set for the (optional) output post-synthesis SDC constraints file yet")

    @output_sdc.setter
    def output_sdc(self, value: str) -> None:
        """Set the (optional) output post-synthesis SDC constraints file."""
        if not isinstance(value, str):
            raise TypeError("output_sdc must be a str")
        self._output_sdc = value  # type: str


class HammerPlaceAndRouteTool(HammerTool):
    ### Generated interface HammerPlaceAndRouteTool ###
    ### Inputs ###

    @property
    def input_files(self) -> Iterable[str]:
        """
        Get the input post-synthesis netlist files.

        :return: The input post-synthesis netlist files.
        """
        try:
            return self._input_files
        except AttributeError:
            raise ValueError("Nothing set for the input post-synthesis netlist files yet")

    @input_files.setter
    def input_files(self, value: Iterable[str]) -> None:
        """Set the input post-synthesis netlist files."""
        if not isinstance(value, Iterable):
            raise TypeError("input_files must be a Iterable[str]")
        self._input_files = value # type: Iterable[str]


    @property
    def top_module(self) -> str:
        """
        Get the top RTL module.

        :return: The top RTL module.
        """
        try:
            return self._top_module
        except AttributeError:
            raise ValueError("Nothing set for the top RTL module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top RTL module."""
        if not isinstance(value, str):
            raise TypeError("top_module must be a str")
        self._top_module = value # type: str

    @property
    def post_synth_sdc(self) -> str:
        """
        Get the input post-synthesis SDC constraint file.

        :return: The input post-synthesis SDC constraint file.
        """
        try:
            return self._post_synth_sdc
        except AttributeError:
            raise ValueError("Nothing set for the input post-synthesis SDC constraint file yet")

    @post_synth_sdc.setter
    def post_synth_sdc(self, value: str) -> None:
        """Set the input post-synthesis SDC constraint file."""
        if not isinstance(value, str):
            raise TypeError("post_synth_sdc must be a str")
        self._post_synth_sdc = value  # type: str

    ### Outputs ###

# Options for invoking the driver.
HammerDriverOptions = NamedTuple('HammerDriverOptions', [
    # List of environment config files in .json
    ('environment_configs', List[str]),
    # List of project config files in .json
    ('project_configs', List[str]),
    # Log file location.
    ('log_file', str),
    # Folder for storing runtime files / CAD junk.
    ('obj_dir', str)
])


class HammerDriver:
    @staticmethod
    def get_default_driver_options() -> HammerDriverOptions:
        """Get default driver options."""
        return HammerDriverOptions(
            environment_configs=[],
            project_configs=[],
            log_file=datetime.datetime.now().strftime("hammer-vlsi-%Y%m%d-%H%M%S.log"),
            obj_dir=HammerVLSISettings.hammer_vlsi_path
        )

    def __init__(self, options: HammerDriverOptions, extra_project_config: dict = {}) -> None:
        """
        Create a hammer-vlsi driver, which is a higher level convenience function
        for quickly using hammer-vlsi. It imports and uses the hammer-vlsi blocks.

        Set up logging, databases, context, etc.

        :param options: Driver options.
        :param extra_project_config: An extra flattened config for the project. Optional.
        """

        # Create global logging context.
        file_logger = HammerVLSIFileLogger(options.log_file)
        HammerVLSILogging.add_callback(file_logger.callback)
        self.log = HammerVLSILogging.context() # type: HammerVLSILoggingContext

        # Create a new hammer database.
        self.database = hammer_config.HammerDatabase() # type: hammer_config.HammerDatabase

        self.log.info("Loading hammer-vlsi libraries and reading settings")

        # Store the run dir.
        self.obj_dir = options.obj_dir # type: str

        # Load in builtins.
        self.database.update_builtins([
            hammer_config.load_config_from_file(os.path.join(HammerVLSISettings.hammer_vlsi_path, "builtins.yml"), strict=True),
            HammerVLSISettings.get_config()
        ])

        # Read in core defaults.
        self.database.update_core(hammer_config.load_config_from_defaults(HammerVLSISettings.hammer_vlsi_path))

        # Read in the environment config for paths to CAD tools, etc.
        for config in options.environment_configs:
            if not os.path.exists(config):
                self.log.error("Environment config %s does not exist!" % (config))
        self.database.update_environment(hammer_config.load_config_from_paths(options.environment_configs, strict=True))

        # Read in the project config to find the syn, par, and tech.
        project_configs = hammer_config.load_config_from_paths(options.project_configs, strict=True)
        project_configs.append(extra_project_config)
        self.database.update_project(project_configs)
        # Store input config for later.
        self.project_config = hammer_config.combine_configs(project_configs) # type: dict

        # Get the technology and load technology settings.
        self.tech = None # type: hammer_tech.HammerTechnology
        self.load_technology()

        # Keep track of what the synthesis and par configs are since
        # update_tools() just takes a whole list.
        self.tool_configs = {} # type: Dict[str, List[dict]]

        # Initialize tool fields.
        self.syn_tool = None # type: HammerSynthesisTool
        self.par_tool = None # type: HammerPlaceAndRouteTool

        # Initialize tool hooks.
        self.syn_tool_hooks = []  # type: List[HammerToolHookAction]
        self.par_tool_hooks = []  # type: List[HammerToolHookAction]

    def load_technology(self, cache_dir: str = "") -> None:
        tech_str = self.database.get_setting("vlsi.core.technology")

        if cache_dir == "":
            cache_dir = os.path.join(self.obj_dir, "tech-%s-cache" % tech_str)

        tech_paths = self.database.get_setting("vlsi.core.technology_path")
        tech_json_path = "" # type: str
        for path in tech_paths:
            tech_json_path = os.path.join(path, tech_str, "%s.tech.json" % tech_str)
            if os.path.exists(tech_json_path):
                break
        if tech_json_path == "":
            self.log.error("Technology {0} not found or missing .tech.json!".format(tech_str))
            return
        self.log.info("Loading technology '{0}'".format(tech_str))
        self.tech = hammer_tech.HammerTechnology.load_from_dir(tech_str, os.path.dirname(tech_json_path))  # type: hammer_tech.HammerTechnology
        self.tech.logger = self.log.context("tech")
        self.tech.set_database(self.database)
        self.tech.cache_dir = cache_dir
        self.tech.extract_technology_files()
        self.database.update_technology(self.tech.get_config())

    def update_tool_configs(self) -> None:
        """
        Calls self.database.update_tools with self.tool_configs as a list.
        """
        tools = reduce(lambda a, b: a + b, list(self.tool_configs.values()))
        self.database.update_tools(tools)

    def load_par_tool(self, run_dir: str = "") -> bool:
        """
        Load the place and route tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
        constructor.
        """
        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "par-rundir")

        par_tool_name = self.database.get_setting("vlsi.core.par_tool")
        par_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.par_tool_path"),
            tool_name=par_tool_name
        )
        assert isinstance(par_tool_get, HammerPlaceAndRouteTool), "Par tool must be a HammerPlaceAndRouteTool"
        par_tool = par_tool_get # type: HammerPlaceAndRouteTool
        par_tool.name = par_tool_name
        par_tool.logger = self.log.context("par")
        par_tool.technology = self.tech
        par_tool.set_database(self.database)
        par_tool.run_dir = run_dir

        # TODO: automate this based on the definitions
        par_tool.input_files = self.database.get_setting("par.inputs.input_files")
        par_tool.top_module = self.database.get_setting("par.inputs.top_module")
        par_tool.post_synth_sdc = self.database.get_setting("par.inputs.post_synth_sdc", nullvalue="")

        self.par_tool = par_tool

        self.tool_configs["par"] = par_tool.get_config()
        self.update_tool_configs()
        return True

    def load_synthesis_tool(self, run_dir: str = "") -> bool:
        """
        Load the synthesis tool based on the given database.

        :param run_dir: Directory to use for the tool run_dir. Defaults to the run_dir passed in the HammerDriver
        constructor.
        :return: True if synthesis tool loading was successful, False otherwise.
        """
        if run_dir == "":
            run_dir = os.path.join(self.obj_dir, "syn-rundir")

        # Find the synthesis/par tool and read in their configs.
        syn_tool_name = self.database.get_setting("vlsi.core.synthesis_tool")
        syn_tool_get = load_tool(
            path=self.database.get_setting("vlsi.core.synthesis_tool_path"),
            tool_name=syn_tool_name
        )
        if not isinstance(syn_tool_get, HammerSynthesisTool):
            self.log.error("Synthesis tool must be a HammerSynthesisTool")
            return False
        # TODO: generate this automatically
        syn_tool = syn_tool_get # type: HammerSynthesisTool
        syn_tool.name = syn_tool_name
        syn_tool.logger = self.log.context("synthesis")
        syn_tool.technology = self.tech
        syn_tool.set_database(self.database)
        syn_tool.run_dir = run_dir

        syn_tool.input_files = self.database.get_setting("synthesis.inputs.input_files")
        syn_tool.top_module = self.database.get_setting("synthesis.inputs.top_module", nullvalue="")
        missing_inputs = False
        if syn_tool.top_module == "":
            self.log.error("Top module not specified for synthesis")
            missing_inputs = True
        if len(syn_tool.input_files) == 0:
            self.log.error("No input files specified for synthesis")
            missing_inputs = True
        if missing_inputs:
            return False

        self.syn_tool = syn_tool

        self.tool_configs["synthesis"] = syn_tool.get_config()
        self.update_tool_configs()
        return True

    def set_syn_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the default list of synthesis tool hooks to be used in run_synthesis.
        :param hooks: Hooks to run
        """
        self.syn_tool_hooks = list(hooks)

    def set_par_tool_hooks(self, hooks: List[HammerToolHookAction]) -> None:
        """
        Set the default list of place and route tool hooks to be used in run_par.
        :param hooks: Hooks to run
        """
        self.par_tool_hooks = list(hooks)

    def run_synthesis(self, hook_actions: Optional[List[HammerToolHookAction]] = None) -> Tuple[bool, dict]:
        """
        Run synthesis based on the given database.
        :param hook_actions: List of hook actions, or leave as None to use the hooks sets in set_synthesis_hooks.
        :return: Tuple of (success, output config dict)
        """

        # TODO: think about artifact storage?
        self.log.info("Starting synthesis with tool '%s'" % (self.syn_tool.name))
        if hook_actions is None:
            hooks_to_use = self.syn_tool_hooks
        else:
            hooks_to_use = hook_actions
        run_succeeded = self.syn_tool.run(hooks_to_use)
        if not run_succeeded:
            self.log.error("Synthesis tool %s failed! Please check its output." % (self.syn_tool.name))
            # Allow the flow to keep running, just in case.
            # TODO: make this an option

        # Record output from the syn_tool into the JSON output.
        output_config = dict(self.project_config)
        # TODO(edwardw): automate this
        try:
            output_config.update(self.syn_tool.export_config_outputs())
        except ValueError as e:
            self.log.fatal(e.args[0])
            return False, {}

        return run_succeeded, output_config

    @staticmethod
    def generate_par_inputs_from_synthesis(config_in: dict) -> dict:
        """Generate the appropriate inputs for running place-and-route from the outputs of synthesis run."""
        output_dict = dict(config_in)
        # Plug in the outputs of synthesis into the par inputs.
        output_dict["par.inputs.input_files"] = output_dict["synthesis.outputs.output_files"]
        output_dict["par.inputs.top_module"] = output_dict["synthesis.inputs.top_module"]
        if "synthesis.outputs.sdc" in output_dict:
            output_dict["par.inputs.post_synth_sdc"] = output_dict["synthesis.outputs.sdc"]
        return output_dict

    def run_par(self, hook_actions: Optional[List[HammerToolHookAction]] = None) -> Tuple[bool, dict]:
        """
        Run place and route based on the given database.
        """
        # TODO: update API to match run_synthesis and deduplicate logic
        self.log.info("Starting place and route with tool '%s'" % (self.par_tool.name))
        if hook_actions is None:
            hooks_to_use = self.par_tool_hooks
        else:
            hooks_to_use = hook_actions
        # TODO: get place and route working
        self.par_tool.run(hooks_to_use)
        return True, {}

class HasSDCSupport(HammerTool):
    """Mix-in trait with functions useful for tools with SDC-style
    constraints."""
    @property
    def sdc_clock_constraints(self) -> str:
        """Generate TCL fragments for top module clock constraints."""
        output = [] # type: List[str]

        clocks = self.get_clock_ports()
        for clock in clocks:
            # TODO: FIXME This assumes that library units are always in ns!!!
            if clock.port is not None:
                output.append("create_clock {0} -name {1} -period {2}".format(clock.port, clock.name, clock.period.value_in_units("ns")))
            else:
                output.append("create_clock {0} -name {0} -period {1}".format(clock.name, clock.period.value_in_units("ns")))
            if clock.uncertainty is not None:
                output.append("set_clock_uncertainty {1} [get_clocks {0}]".format(clock.name, clock.uncertainty.value_in_units("ns")))

        output.append("\n")
        return "\n".join(output)

    @property
    def sdc_pin_constraints(self) -> str:
        """Generate a fragment for I/O pin constraints."""
        output = []  # type: List[str]

        default_output_load = float(self.get_setting("vlsi.inputs.default_output_load"))

        # Specify default load.
        output.append("set_load {load} [all_outputs]".format(
            load=default_output_load
        ))

        # Also specify loads for specific pins.
        for load in self.get_output_load_constraints():
            output.append("set_load {load} [get_port \"{name}\"]".format(
                load=load.load,
                name=load.name
            ))
        return "\n".join(output)


class CadenceTool(HasSDCSupport, HammerTool):
    """Mix-in trait with functions useful for Cadence-based tools."""

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        return {
            "CDS_LIC_FILE": self.get_setting("cadence.CDS_LIC_FILE"),
            "CADENCE_HOME": self.get_setting("cadence.cadence_home")
        }

    def get_liberty_libs(self) -> str:
        """
        Helper function to get the list of ASCII liberty files in space separated format.
        :return: List of lib files separated by spaces
        """
        lib_args = self.read_libs([
            self.liberty_lib_filter
        ], self.to_plain_item)
        return " ".join(lib_args)

    def get_mmmc_libs(self, corner: MMMCCorner) -> str:
        lib_args = self.read_libs([self.liberty_lib_filter],self.to_plain_item, pre_filters=[
            self.filter_for_mmmc(voltage=corner.voltage, temp=corner.temp)])
        return " ".join(lib_args)

    def get_mmmc_qrc(self, corner: MMMCCorner) -> str:
        lib_args = self.read_libs([self.qrc_tech_filter],self.to_plain_item, pre_filters=[
            self.filter_for_mmmc(voltage=corner.voltage, temp=corner.temp)])
        return " ".join(lib_args)

    def get_qrc_tech(self) -> str:
        """
        Helper function to get the list of rc corner tech files in space separated format.
        :return: List of qrc tech files separated by spaces
        """
        lib_args = self.read_libs([
            self.qrc_tech_filter
        ], self.to_plain_item)
        return " ".join(lib_args)

    def generate_mmmc_script(self) -> str:
        """
        Output for the mmmc.tcl script.
        Innovus (init_design) requires that the timing script be placed in a separate file.
        :return: Contents of the mmmc script.
        """
        mmmc_output = []  # type: List[str]

        def append_mmmc(cmd: str) -> None:
            self.verbose_tcl_append(cmd, mmmc_output)

        # Create an Innovus constraint mode.
        constraint_mode = "my_constraint_mode"
        sdc_files = []  # type: List[str]

        # Generate constraints
        clock_constraints_fragment = os.path.join(self.run_dir, "clock_constraints_fragment.sdc")
        with open(clock_constraints_fragment, "w") as f:
            f.write(self.sdc_clock_constraints)
        sdc_files.append(clock_constraints_fragment)
        # Generate port constraints.
        pin_constraints_fragment = os.path.join(self.run_dir, "pin_constraints_fragment.sdc")
        with open(pin_constraints_fragment, "w") as f:
            f.write(self.sdc_pin_constraints)
        sdc_files.append(pin_constraints_fragment)
        # Add the post-synthesis SDC, if present.
        if hasattr(self, 'post_synth_sdc'):
            if self.post_synth_sdc != "":
                sdc_files.append(self.post_synth_sdc)
        # TODO: add floorplanning SDC
        if len(sdc_files) > 0:
            sdc_files_arg = "-sdc_files [list {sdc_files}]".format(
                sdc_files=" ".join(sdc_files)
            )
        else:
            blank_sdc = os.path.join(self.run_dir, "blank.sdc")
            self.run_executable(["touch", blank_sdc])
            sdc_files_arg = "-sdc_files {{ {} }}".format(blank_sdc)
        append_mmmc("create_constraint_mode -name {name} {sdc_files_arg}".format(
            name=constraint_mode,
            sdc_files_arg=sdc_files_arg
        ))

        corners = self.get_mmmc_corners()
        # In parallel, create the delay corners
        if corners:
            setup_corner = corners[0]
            hold_corner = corners[0]
            # TODO (colins): handle more than one corner and do something with extra corners
            for corner in corners:
                if corner.type is MMMCCornerType.Setup:
                    setup_corner = corner
                if corner.type is MMMCCornerType.Hold:
                    hold_corner = corner

            # First, create Innovus library sets
            append_mmmc("create_library_set -name {name} -timing [list {list}]".format(
                name="{n}.setup_set".format(n=setup_corner.name),
                list=self.get_mmmc_libs(setup_corner)
            ))
            append_mmmc("create_library_set -name {name} -timing [list {list}]".format(
                name="{n}.hold_set".format(n=hold_corner.name),
                list=self.get_mmmc_libs(hold_corner)
            ))
            # Skip opconds for now
            # Next, create Innovus timing conditions
            append_mmmc("create_timing_condition -name {name} -library_sets [list {list}]".format(
                name="{n}.setup_cond".format(n=setup_corner.name),
                list="{n}.setup_set".format(n=setup_corner.name)
            ))
            append_mmmc("create_timing_condition -name {name} -library_sets [list {list}]".format(
                name="{n}.hold_cond".format(n=hold_corner.name),
                list="{n}.hold_set".format(n=hold_corner.name)
            ))
            # Next, create Innovus rc corners from qrc tech files
            append_mmmc("create_rc_corner -name {name} -temperature {tempInCelsius} {qrc}".format(
                name="{n}.setup_rc".format(n=setup_corner.name),
                tempInCelsius=setup_corner.temp.split(" ")[0],
                qrc="-qrc_tech {}".format(self.get_mmmc_qrc(setup_corner)) if self.get_mmmc_qrc(setup_corner) != '' else ''
            ))
            append_mmmc("create_rc_corner -name {name} -temperature {tempInCelsius} {qrc}".format(
                name="{n}.hold_rc".format(n=hold_corner.name),
                tempInCelsius=hold_corner.temp.split(" ")[0],
                qrc="-qrc_tech {}".format(self.get_mmmc_qrc(hold_corner)) if self.get_mmmc_qrc(hold_corner) != '' else ''
            ))
            # Next, create an Innovus delay corner.
            append_mmmc(
                "create_delay_corner -name {name}_delay -timing_condition {name}_cond -rc_corner {name}_rc".format(
                    name="{n}.setup".format(n=setup_corner.name)
                ))
            append_mmmc(
                "create_delay_corner -name {name}_delay -timing_condition {name}_cond -rc_corner {name}_rc".format(
                    name="{n}.hold".format(n=hold_corner.name)
                ))
            # Next, create the analysis views
            append_mmmc("create_analysis_view -name {name}_view -delay_corner {name}_delay -constraint_mode {constraint}".format(
                name="{n}.setup".format(n=setup_corner.name), constraint=constraint_mode))
            append_mmmc("create_analysis_view -name {name}_view -delay_corner {name}_delay -constraint_mode {constraint}".format(
                name="{n}.hold".format(n=hold_corner.name), constraint=constraint_mode))
            # Finally, apply the analysis view.
            append_mmmc("set_analysis_view -setup {{ {setup_view} }} -hold {{ {hold_view} }}".format(
                setup_view="{n}.setup_view".format(n=setup_corner.name),
                hold_view="{n}.hold_view".format(n=hold_corner.name)
            ))
        else:
            # First, create an Innovus library set.
            library_set_name = "my_lib_set"
            append_mmmc("create_library_set -name {name} -timing [list {list}]".format(
                name=library_set_name,
                list=self.get_liberty_libs()
            ))
            # Next, create an Innovus timing condition.
            timing_condition_name = "my_timing_condition"
            append_mmmc("create_timing_condition -name {name} -library_sets [list {list}]".format(
                name=timing_condition_name,
                list=library_set_name
            ))
            # extra junk: -opcond ...
            rc_corner_name = "rc_cond"
            append_mmmc("create_rc_corner -name {name} -temperature {tempInCelsius} {qrc}".format(
                name=rc_corner_name,
                tempInCelsius=120,  # TODO: this should come from tech config
                qrc="-qrc_tech {}".format(self.get_qrc_tech()) if self.get_qrc_tech() != '' else ''
            ))
            # Next, create an Innovus delay corner.
            delay_corner_name = "my_delay_corner"
            append_mmmc(
                "create_delay_corner -name {name} -timing_condition {timing_cond} -rc_corner {rc}".format(
                    name=delay_corner_name,
                    timing_cond=timing_condition_name,
                    rc=rc_corner_name
                ))
            # extra junk: -rc_corner my_rc_corner_maybe_worst
            # Next, create an Innovus analysis view.
            analysis_view_name = "my_view"
            append_mmmc("create_analysis_view -name {name} -delay_corner {corner} -constraint_mode {constraint}".format(
                name=analysis_view_name, corner=delay_corner_name, constraint=constraint_mode))
            # Finally, apply the analysis view.
            # TODO: introduce different views of setup/hold and true multi-corner
            append_mmmc("set_analysis_view -setup {{ {setup_view} }} -hold {{ {hold_view} }}".format(
                setup_view=analysis_view_name,
                hold_view=analysis_view_name
            ))

        return "\n".join(mmmc_output)

class SynopsysTool(HasSDCSupport, HammerTool):
    """Mix-in trait with functions useful for Synopsys-based tools."""
    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        return {
            "SNPSLMD_LICENSE_FILE": self.get_setting("synopsys.SNPSLMD_LICENSE_FILE"),
            # TODO: this is actually a Mentor Graphics licence, not sure why the old dc scripts depend on it.
            "MGLS_LICENSE_FILE": self.get_setting("synopsys.MGLS_LICENSE_FILE")
        }

    def get_synopsys_rm_tarball(self, product: str, settings_key: str = "") -> str:
        """Locate reference methodology tarball.

        :param product: Either "DC" or "ICC"
        :param settings_key: Key to retrieve the version for the product. Leave blank for DC and ICC.
        """
        key = settings_key # type: str
        if product == "DC":
            key = "synthesis.dc.dc_version"
        elif product == "ICC":
            key = "par.icc.icc_version"

        synopsys_rm_tarball = os.path.join(self.get_setting("synopsys.rm_dir"), "%s-RM_%s.tar" % (product, self.get_setting(key)))
        if not os.path.exists(synopsys_rm_tarball):
            # TODO: convert these to logger calls
            raise FileNotFoundError("Expected reference methodology tarball not found at %s. Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a DC reference methodology. If these tarballs have been pre-downloaded, you can set synopsys.rm_dir instead of generating them yourself." % (synopsys_rm_tarball))
        else:
            return synopsys_rm_tarball

def load_tool(tool_name: str, path: Iterable[str]) -> HammerTool:
    """
    Load the given tool.
    See the hammer-vlsi README for how it works.

    :param tool_name: Name of the tool
    :param path: List of paths to get
    :return: HammerTool of the given tool
    """
    # Temporarily add to the import path.
    for p in path:
        sys.path.insert(0, p)
    try:
        mod = importlib.import_module(tool_name)
    except ImportError:
        raise ValueError("No such tool " + tool_name)
    # Now restore the original import path.
    for _ in path:
        sys.path.pop(0)
    try:
        htool = getattr(mod, "tool")
    except AttributeError:
        raise ValueError("No such tool " + tool_name + ", or tool does not follow the hammer-vlsi tool library format")

    if not isinstance(htool, HammerTool):
        raise ValueError("Tool must be a HammerTool")

    # Set the tool directory.
    htool.tool_dir = os.path.dirname(os.path.abspath(mod.__file__))
    return htool


def reduce_named(function: Callable, sequence: Iterable, initial=None) -> Any:
    """
    Version of functools.reduce with named arguments.
    See https://mail.python.org/pipermail/python-ideas/2014-October/029803.html
    """
    if initial is None:
        return reduce(function, sequence)
    else:
        return reduce(function, sequence, initial)
