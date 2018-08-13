#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_tool.py
#  HammerTool - the main Hammer tool abstraction class.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from abc import ABCMeta, abstractmethod
import atexit
from functools import reduce
import inspect
from numbers import Number
import os
import re
import shlex
import subprocess
from typing import Callable, Iterable, List, Tuple, Optional, Dict, Any, Union, Set, cast
import warnings

import hammer_config
import hammer_tech

from hammer_logging import HammerVLSILoggingContext
from .constraints import *

from .hooks import HammerToolHookAction, HammerToolStep, HammerStepFunction, HookLocation

from .hammer_vlsi_impl import HierarchicalMode, LibraryFilter, HammerToolPauseException
from .units import TimeValue, VoltageValue, TemperatureValue
from hammer_utils import add_lists, in_place_unique, reduce_named


__all__ = ['HammerTool']


def make_raw_hammer_tool_step(func: HammerStepFunction, name: str) -> HammerToolStep:
    check_hammer_step_function(func)
    return HammerToolStep(func, name)


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
        This should return an absolute path.

        :return: Path to the location of the library.
        """
        try:
            return self._rundir
        except AttributeError:
            raise ValueError("Internal error: run dir location not set by hammer-vlsi")

    @run_dir.setter
    def run_dir(self, path: str) -> None:
        """Set the location of a writable directory which the tool can use to store temporary information."""
        # If the path isn't absolute, make it absolute.
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        self._rundir = path  # type: str

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
    def hierarchical_mode(self) -> HierarchicalMode:
        """
        Input files for this tool library.
        The exact nature of the files will depend on the type of library.
        """
        try:
            return self.attr_getter("_hierarchical_mode", None)
        except AttributeError:
            raise ValueError("HierarchicalMode not set")

    @hierarchical_mode.setter
    def hierarchical_mode(self, value: HierarchicalMode) -> None:
        """
        Set the input files for this tool library.
        The exact nature of the files will depend on the type of library.
        """
        if not isinstance(value, HierarchicalMode):
            raise TypeError("hierarchical_mode must be a HierarchicalMode")
        self.attr_setter("_hierarchical_mode", value)

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
        """Helper function for implementing the getter of a property with a default.
        If default is None, then raise a AttributeError."""
        if not hasattr(self, key):
            if default is not None:
                setattr(self, key, default)
            else:
                raise AttributeError("No such attribute " + str(key))
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
                assert action.step is not None, "ReplaceStep requires a step"
                assert action.target_name == action.step.name, "Replacement step should have the same name"
                new_steps[step_id] = action.step
            elif action.location == HookLocation.InsertPreStep:
                assert action.step is not None, "InsertPreStep requires a step"
                if has_step(action.step.name):
                    self.logger.error("New step '{step}' already exists".format(step=action.step.name))
                    return False
                new_steps.insert(step_id, action.step)
                names.add(action.step.name)
            elif action.location == HookLocation.InsertPostStep:
                assert action.step is not None, "InsertPostStep requires a step"
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
            else:
                # Cajole the type checker into accepting that step is a HammerToolStep
                step = cast(HammerToolStep, step)
                check_hammer_step_function(step.func)

        # Run steps.
        prev_step = None  # type: Optional[HammerToolStep]

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

    @property
    def config_dirs(self) -> List[str]:
        """
        List of folders where (default) configs can live.
        Defaults to self.tool_dir.

        :return: List of default config folders.
        """
        return [self.tool_dir]

    def get_config(self) -> List[dict]:
        """Get the config for this tool."""
        return reduce(add_lists, map(lambda path: hammer_config.load_config_from_defaults(path), self.config_dirs))

    def get_setting(self, key: str, nullvalue: Optional[str] = None) -> Any:
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

        lib_results = list(
            reduce(add_lists, list(map(extraction_func, filtered_libs)), []))  # type: List[str]

        # Uniquify results.
        # TODO: think about whether this really belongs here and whether we always need to uniquify.
        # This is here to get stuff working since some CAD tools dislike duplicated arguments (e.g. duplicated stdcell
        # lib, etc).
        in_place_unique(lib_results)

        lib_results_with_extra_funcs = reduce(lambda arr, extra_func: list(map(extra_func, arr)), extra_funcs, lib_results)

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
        Select ASCII liberty (.lib) timing libraries. Prefers CCS if available; picks NLDM as a fallback.
        """
        warnings.warn("Use timing_lib_filter instead", DeprecationWarning, stacklevel=2)

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib", "CCS/NLDM timing lib (ASCII .lib)",
                                 extraction_func=extraction_func, is_file=True)

    @property
    def timing_lib_filter(self) -> LibraryFilter:
        """
        Select ASCII .lib timing libraries. Prefers CCS if available; picks NLDM as a fallback.
        """

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            # Choose ccs if available, if not, nldm.
            if lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib", "CCS/NLDM timing lib (ASCII .lib)",
                                 extraction_func=extraction_func, is_file=True)

    @property
    def timing_lib_with_ecsm_filter(self) -> LibraryFilter:
        """
        Select ASCII .lib timing libraries. Prefers ECSM, then CCS, then NLDM if multiple are present for
        a single given .lib.
        """

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            if lib.ecsm_liberty_file is not None:
                return [lib.ecsm_liberty_file]
            elif lib.ccs_liberty_file is not None:
                return [lib.ccs_liberty_file]
            elif lib.nldm_liberty_file is not None:
                return [lib.nldm_liberty_file]
            else:
                return []

        return LibraryFilter.new("timing_lib_with_ecsm", "ECSM/CCS/NLDM timing lib (liberty ASCII .lib)",
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
    def verilog_synth_filter(self) -> LibraryFilter:
        """
        Selecting verilog_synth files which are synthesizable wrappers (e.g. for SRAM) which are needed in some
        technologies.
        """

        def extraction_func(lib: hammer_tech.Library) -> List[str]:
            if lib.verilog_synth is not None:
                return [lib.verilog_synth]
            else:
                return []

        return LibraryFilter.new("verilog_synth", "Synthesizable Verilog wrappers",
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

    def process_library_filter(self, pre_filts: List[Callable[[hammer_tech.Library], bool]], filt: LibraryFilter, output_func: Callable[[str, LibraryFilter], List[str]],
                               must_exist: bool = True) -> List[str]:
        """
        Process the given library filter and return a list of items from that library filter with any extra
        post-processing.

        - Get a list of lib items
        - Run any extra_post_filter_funcs (if needed)
        - For every lib item in each lib items, run output_func

        :param pre_filts: List of functions with which to pre-filter the libraries. Each function must return true
                          in order for this library to be used.
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
        return list(reduce(add_lists, after_output_functions, []))

    def read_libs(self, library_types: Iterable[LibraryFilter], output_func: Callable[[str, LibraryFilter], List[str]],
            pre_filters: Optional[List[Callable[[hammer_tech.Library],bool]]] = None,
            must_exist: bool = True) -> List[str]:
        """
        Read the given libraries and return a list of strings according to some output format.

        :param library_types: List of libraries to filter, specified as a list of LibraryFilter elements.
        :param output_func: Function which processes the outputs, taking in the filtered lib and the library filter
                            which generated it.
        :param pre_filters: List of additional filter functions to use to filter the list of libraries.
        :param must_exist: Must each library item actually exist? Default: True (yes, they must exist)
        :return: List of filtered libraries processed according output_func.
        """

        if pre_filters is None:
            pre_filts = [self.filter_for_supplies]  # type: List[Callable[[hammer_tech.Library], bool]]
        else:
            assert isinstance(pre_filters, List)
            pre_filts = pre_filters

        return list(reduce(
            add_lists,
            map(
                lambda lib: self.process_library_filter(pre_filts=pre_filts, filt=lib, output_func=output_func, must_exist=must_exist),
                library_types
            )
        ))

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
        assert isinstance(constraints, list)
        return list(map(PlacementConstraint.from_dict, constraints))

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
                voltage=VoltageValue(str(corner["voltage"])),
                temp=TemperatureValue(str(corner["temp"])),
            )
            output.append(corn)
        return output

    def get_input_ilms(self) -> List[ILMStruct]:
        """
        Get a list of input ILM modules for hierarchical mode.
        """
        ilms = self.get_setting("vlsi.inputs.ilms")  # type: List[dict]
        assert isinstance(ilms, list)
        return list(map(ILMStruct.from_setting, ilms))

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


