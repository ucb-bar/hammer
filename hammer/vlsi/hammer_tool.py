#  hammer_tool.py
#  HammerTool - the main Hammer tool abstraction class.
#
#  See LICENSE for licence details.

import inspect
import os
import re
import shlex
from abc import ABCMeta, abstractmethod
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, cast
from inspect import cleandoc
from pathlib import Path

import hammer.config as hammer_config
import hammer.tech as hammer_tech
from hammer.logging import HammerVLSILoggingContext
from hammer.tech import LibraryFilter, Stackup, RoutingDirection, Metal
from hammer.utils import (add_lists, assert_function_type, get_or_else,
                          optional_map, LEFUtils)

from .constraints import *
from .hammer_vlsi_impl import HierarchicalMode
from .hooks import (HammerStepFunction, HammerToolHookAction, HammerToolStep,
                    HookLocation, HammerStartStopStep)
from .submit_command import HammerSubmitCommand
from .units import TemperatureValue, TimeValue, VoltageValue

__all__ = ['HammerTool']


def make_raw_hammer_tool_step(func: HammerStepFunction, name: str) -> HammerToolStep:
    # Check the type of the HammerStepFunction
    check_hammer_step_function(func)
    return HammerToolStep(func, name)


def check_hammer_step_function(func: HammerStepFunction) -> None:
    """Internal alias for checking HammerStepFunction signatures."""
    assert_function_type(func, args=[HammerTool], return_type=bool)


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
        By default, this just adds a flag to indicate that the output fragment
        is output-only/not complete.

        Warning: any subclasses must call this method in the base class
        so that all output configs get added correctly.

        :return: Config dictionary of the outputs of this tool.
        """
        return {
            "vlsi.builtins.is_complete": False
        }

    @abstractmethod
    def tool_config_prefix(self) -> str:
        """
        Returns the config prefix that contains all tool specific settings.
        e.g. "synthesis.yosys".

        :return: A string that is the prefix for all tool specific settings.
        """
        pass

    def version(self) -> int:
        """
        Returns the version number of the current tool version, using version_number
        below.

        :return: The version number of the current tool.
        """
        return self.version_number(self.get_setting(self.tool_config_prefix() + ".version"))

    @abstractmethod
    def version_number(self, version: str) -> int:
        """
        Based on the tool, figures out an integer value for the version number.

        :param version: The version number given by the tool vendor.
        :return: An integer representing the version suitable for comparisons.
        """
        pass

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

    @property
    def first_step(self) -> HammerToolStep:
        """
        The first non-persistent step after hooks resolution.

        :return: The first non-persistent step to be run.
        """
        try:
            return self._first_step
        except AttributeError:
            raise ValueError("Internal error: first step not set by hammer-vlsi")

    @first_step.setter
    def first_step(self, step: HammerToolStep) -> None:
        """Set the first non-persistent step to be run."""
        self._first_step = step

    @property
    def persistent_steps(self) -> List[HammerToolHookAction]:
        """
        List of persistent steps for this tool.

        :return: List of persistent hooks.
        """
        try:
            return self._persistent_steps
        except AttributeError:
            raise ValueError("Internal error: persistent hooks not set by hammer-vlsi")

    @persistent_steps.setter
    def persistent_steps(self, hooks: List[HammerToolHookAction]) -> None:
        """Set the List of persistent hooks."""
        self._persistent_steps = hooks

    def run_persistent_step(self, pst: HammerToolHookAction, target_step: HammerToolStep) -> bool:
        assert pst.step is not None, "Persistent(Pre/Post)Step requires a step"
        if pst.location == HookLocation.PersistentStep:
            self.logger.debug("Running persistent sub-step '{pstep}' before '{step}'".format(pstep=pst.step.name, step=target_step.name))
        if pst.location == HookLocation.PersistentPreStep:
            self.logger.debug("Running persistent sub-step '{pstep}' before '{step}' (pre-step: '{pre_step}')".format(pstep=pst.step.name, step=target_step.name, pre_step=pst.target_name))
        if pst.location == HookLocation.PersistentPostStep:
            self.logger.debug("Running persistent sub-step '{pstep}' after '{step}' (post-step: '{post_step}')".format(pstep=pst.step.name, step=target_step.name, post_step=pst.target_name))
        pst_out = pst.step.func(self)
        assert pst_out, "Persistent step {step} failed!".format(step=pst.step.name)
        return pst_out

    def do_pre_steps(self, first_step: HammerToolStep) -> bool:
        """
        Function to run before the list of steps executes.
        Intended to be overriden by subclasses.
        Note: if you override this, remember to call the superclass method too!

        :param first_step: First step to be taken.
        :return: True if successful, False otherwise.
        """
        pst_out = True
        # Run persistent hooks first
        for pst in list(filter(lambda p: p.location == HookLocation.PersistentStep, self.persistent_steps)):
            pst_out = pst_out and self.run_persistent_step(pst, first_step)
        # If pre-persistent hooks target the first step, run them first
        for pst in list(filter(lambda p: p.location == HookLocation.PersistentPreStep and p.target_name == self.first_step.name, self.persistent_steps)):
            pst_out = pst_out and self.run_persistent_step(pst, first_step)
        return pst_out

    def do_between_steps(self, prev: HammerToolStep, next: HammerToolStep) -> bool:
        """
        Function to run between the execution of two steps.
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
    def package(self) -> str:
        """
        Get the top-level package of this tool (e.g. "hammer.synthesis.nop")
        """
        return self._package

    @package.setter
    def package(self, package: str) -> None:
        self._package: str = package

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
    def input_files(self) -> List[str]:
        """
        Input files for this tool library.
        The exact nature of the files will depend on the type of library.
        """
        try:
            return self._input_files
        except AttributeError:
            raise ValueError("Nothing set for inputs yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """
        Set the input files for this tool library.
        The exact nature of the files will depend on the type of library.
        """
        if not isinstance(value, Iterable):
            raise TypeError("input_files must be a Iterable[str]")
        self._input_files = value


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
        self._technology = value  # type: hammer_tech.HammerTechnology

    @property
    def submit_command(self) -> HammerSubmitCommand:
        """
        Get the submit command used by this tool

        :return HammerSubmitCommand instance
        """
        try:
            return self._submit_command
        except AttributeError:
            raise ValueError("Internal error: technology not set by hammer-vlsi")

    @submit_command.setter
    def submit_command(self, value: HammerSubmitCommand) -> None:
        """
        Set the submit command used by this tool

        :value: HammerSubmitCommand instance
        """
        self._submit_command = value

    @property
    def top_module(self) -> str:
        """
        Get the top-level module.

        :return: The top-level module.
        """
        try:
            return self.attr_getter("_top_module", None)
        except AttributeError:
            raise ValueError("Nothing set for the top-level module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top-level module."""
        if not (isinstance(value, str)):
            raise TypeError("top_module must be a str")
        self.attr_setter("_top_module", value)

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
    def get_tool_hooks(self) -> List[HammerToolHookAction]:
        """
        Get any hooks specific to the tool.
        To be overridden by subclasses that need to implement persistent hooks.
        """
        return list()

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

        # Persistent steps are processed differently from normal steps. Not a List[HammerToolStep]
        # because we need to access its location and target_name later when iterating through new_steps.
        p_steps = []  # type: List[HammerToolHookAction]

        # Where to resume/pause, if such a hook exists
        resume_step = None  # type: Optional[str]
        pause_step = None  # type: Optional[str]
        # If resume/pause_step is not None, whether to resume/pause pre or post this step
        resume_step_pre = True  # type: bool
        pause_step_pre = True  # type: bool

        for action in hook_actions:
            step_id = -1
            pstep_id = -1

            # First, process which step is being targeted - set step_id or pstep_id accordingly.
            if action.location != HookLocation.PersistentStep:
                if not has_step(action.target_name):
                    if action.location in [HookLocation.ResumePreStep, HookLocation.ResumePostStep, HookLocation.PausePreStep, HookLocation.PausePostStep]:
                        self.logger.error("Target step '{step}' specified by --from/after/to/until_step does not exist".format(step=action.target_name))
                        return False
                    else:
                        self.logger.error("Target step '{step}' specified by a hook does not exist".format(step=action.target_name))
                        return False

                for i, nstep in enumerate(new_steps):
                    if nstep.name == action.target_name:
                        step_id = i
                        break
                for i, pstep in enumerate(p_steps):
                    assert pstep.step is not None, "Persistent(Pre/Post)Step requires a step"
                    if pstep.step.name == action.target_name:
                        pstep_id = i
                        break
                assert (step_id > -1) != (pstep_id > -1), "Either a regular or persistent step must be targeted"

            # Next, process hook actions based on location
            if action.location == HookLocation.ReplaceStep:
                assert action.step is not None, "ReplaceStep requires a step"
                if pstep_id > -1:
                    # Inherit replaced persistent step's location and target
                    p_steps[pstep_id] = action._replace(location=p_steps[pstep_id].location,
                                                                 target_name=p_steps[pstep_id].target_name)
                elif step_id > -1:
                    new_steps[step_id] = action.step
                # Replace name so it can be properly targeted by other hook actions, except for removal hooks
                names.remove(action.target_name)
                if action.step.name != "dummy_step":
                    names.add(action.step.name)
            elif action.location == HookLocation.InsertPreStep:
                assert action.step is not None, "InsertPreStep requires a step"
                if has_step(action.step.name):
                    self.logger.error("New step '{step}' already exists".format(step=action.step.name))
                    return False
                if pstep_id > -1:
                    # Inherit replaced persistent step's location and target
                    p_steps.insert(pstep_id, action._replace(location=p_steps[pstep_id].location,
                                                                      target_name=p_steps[pstep_id].target_name))
                elif step_id > -1:
                    new_steps.insert(step_id, action.step)
                names.add(action.step.name)
            elif action.location == HookLocation.InsertPostStep:
                assert action.step is not None, "InsertPostStep requires a step"
                if has_step(action.step.name):
                    self.logger.error("New step '{step}' already exists".format(step=action.step.name))
                    return False
                if pstep_id > -1:
                    # Inherit replaced persistent step's location and target
                    p_steps.insert(pstep_id + 1, action._replace(location=p_steps[pstep_id].location,
                                                                          target_name=p_steps[pstep_id].target_name))
                elif step_id > -1:
                    new_steps.insert(step_id + 1, action.step)
                names.add(action.step.name)
            elif action.location == HookLocation.ResumePreStep or action.location == HookLocation.ResumePostStep:
                if step_id == -1:
                    self.logger.error("ResumePre/PostStep cannot target a persistent step")
                    return False
                if resume_step is not None:
                    self.logger.error("More than one resume hook is present")
                    return False
                resume_step = action.target_name
                resume_step_pre = action.location == HookLocation.ResumePreStep
            elif action.location == HookLocation.PausePreStep or action.location == HookLocation.PausePostStep:
                if step_id == -1:
                    self.logger.error("PausePre/PostStep cannot target a persistent step")
                    return False
                if pause_step is not None:
                    self.logger.error("More than one pause hook is present")
                    return False
                pause_step = action.target_name
                pause_step_pre = action.location == HookLocation.PausePreStep
            elif action.location in [HookLocation.PersistentStep, HookLocation.PersistentPreStep, HookLocation.PersistentPostStep]:
                assert action.step is not None, "Persistent(Pre/Post)Step requires a step"
                if action.location != HookLocation.PersistentStep and step_id == -1:
                    self.logger.error("make_pre/post_persistent_hook cannot target a persistent step")
                    return False
                if has_step(action.step.name):
                    self.logger.error("New step '{step}' already exists".format(step=action.step.name))
                    return False
                p_steps.append(action)
                names.add(action.step.name)
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

        for pstep in p_steps:
            if not isinstance(pstep, HammerToolHookAction):
                raise ValueError("Element in List[HammerToolHookAction] is not a HammerToolHookAction")
            else:
                # Cajole the type checker into accepting that pstep.step is a HammerToolStep
                step = cast(HammerToolStep, pstep.step)
                check_hammer_step_function(step.func)

        # Set properties
        if len(new_steps) == 0:
            def dummy_step(x: HammerTool) -> bool:
                return True
            self.first_step = HammerTool.make_step_from_function(dummy_step)
        else:
            self.first_step = new_steps[0]
        self.persistent_steps = p_steps

        # Run steps.
        prev_step = None  # type: Optional[HammerToolStep]

        for step_index, step in enumerate(new_steps):
            # Do this step?
            do_step = True

            if resume_step_pre and resume_step == step.name:
                self.logger.info("Resuming before '{step}' due to resume hook".format(step=step.name))
                # Remove resume marker
                resume_step = None
            elif resume_step is not None:
                self.logger.debug("Sub-step '{step}' skipped due to resume hook".format(step=step.name))
                do_step = False

            if pause_step_pre and pause_step == step.name:
                self.logger.info("Pausing tool execution before '{step}' due to pause hook".format(step=step.name))
                for s in new_steps[step_index:]:
                    self.logger.debug("Sub-step '{step}' skipped due to pause hook".format(step=s.name))
                break

            if do_step:
                # First step
                if prev_step is None:
                    # Run pre-step hook.
                    self.do_pre_steps(step)
                    # If pre-persistent hooks don't target the first step, now run them
                    for pst in list(filter(lambda p: p.location == HookLocation.PersistentPreStep and any(s.name == p.target_name for s in new_steps[step_index:]), self.persistent_steps)):
                        if pst.target_name != self.first_step.name:
                            self.run_persistent_step(pst, step)
                    # Finally, run the post-persistent hooks whose targets were passed
                    for pst in list(filter(lambda p: p.location == HookLocation.PersistentPostStep and any(s.name == p.target_name for s in new_steps[:step_index]), self.persistent_steps)):
                        self.run_persistent_step(pst, step)
                else:
                    self.do_between_steps(prev_step, step)

                self.logger.debug("Running sub-step '{step}'".format(step=step.name))
                func_out = step.func(self)  # type: bool
                prev_step = step
                assert isinstance(func_out, bool)
                if not func_out:
                    return False

                # Inject PersistentPostStep after we pass its target step
                for pst in list(filter(lambda s: s.target_name == step.name and s.location == HookLocation.PersistentPostStep, self.persistent_steps)):
                    self.run_persistent_step(pst, step)

            if not resume_step_pre and resume_step == step.name:
                self.logger.info("Resuming after '{step}' due to resume hook".format(step=step.name))
                resume_step = None

            if not pause_step_pre and pause_step == step.name:
                self.logger.info("Pausing tool execution after '{step}' due to pause hook".format(step=step.name))
                for s in new_steps[step_index+1:]:
                    self.logger.debug("Sub-step '{step}' skipped due to pause hook".format(step=s.name))
                break

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
    def make_replacement_hook(step: str, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Create a hook action which replaces an existing step.

        :return: Hook action which replaces the given step.
        """
        return HammerToolHookAction(
            target_name=step,
            location=HookLocation.ReplaceStep,
            step=HammerTool.make_step_from_function(func)
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
    def make_resume_pause_hook(step: str, location: HookLocation) -> HammerToolHookAction:
        """
        Create a hook action which will start/stop the execution of the tool at/after the given step.

        :param step: The target step that bounds of the steps to run.
        :param location: Encodes whether this hook will cause a resume/pause pre/post the target step.
        """
        if not location in [HookLocation.ResumePreStep, HookLocation.ResumePostStep, HookLocation.PausePreStep, HookLocation.PausePostStep]:
            raise ValueError("Resume/Pause hook location must be Resume*/Pause*")

        return HammerToolHookAction(
            target_name=step,
            location=location,
            step=None
        )

    @staticmethod
    def make_pre_pause_hook(step: str) -> HammerToolHookAction:
        """
        Create pause before the execution of the given step.
        Note that only one pause hook may be present.
        """
        return HammerTool.make_resume_pause_hook(step, HookLocation.PausePreStep)

    @staticmethod
    def make_post_pause_hook(step: str) -> HammerToolHookAction:
        """
        Create pause before the execution of the given step.
        Note that only one pause hook may be present.
        """
        return HammerTool.make_resume_pause_hook(step, HookLocation.PausePostStep)

    @staticmethod
    def make_pre_resume_hook(step: str) -> HammerToolHookAction:
        """
        Resume before the given step.
        Note that only one resume hook may be present.
        """
        return HammerTool.make_resume_pause_hook(step, HookLocation.ResumePreStep)

    @staticmethod
    def make_post_resume_hook(step: str) -> HammerToolHookAction:
        """
        Resume after the given step.
        Note that only one resume hook may be present.
        """
        return HammerTool.make_resume_pause_hook(step, HookLocation.ResumePostStep)

    @staticmethod
    def make_start_stop_hooks(start: HammerStartStopStep, stop: HammerStartStopStep) -> List[HammerToolHookAction]:
        """
        Helper function to create a HammerToolHookAction list which will run from/after and to/until the given steps.
        The inclusive ones take priority in the event that incompatible options are called.

        :param start: HammerStartStopStep that defines where to resume from
        :param stop: HammerStartStopStep that define where to pause at
        :return: HammerToolHookAction list for running from and to the given steps, inclusive.
        """
        output = []  # type: List[HammerToolHookAction]
        # Determine where to resume from.
        if start.step is not None:
            if start.inclusive:
                output.append(HammerTool.make_pre_resume_hook(start.step))
            else:
                output.append(HammerTool.make_post_resume_hook(start.step))
        # Determine where to stop the flow.
        if stop.step is not None:
            if stop.inclusive:
                output.append(HammerTool.make_post_pause_hook(stop.step))
            else:
                output.append(HammerTool.make_pre_pause_hook(stop.step))
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
            step=HammerTool.make_step_from_function(dummy_step)
        )

    @staticmethod
    def make_persistent_hook(func: HammerStepFunction) -> HammerToolHookAction:
        """
        Helper function to always insert a step at the beginning.

        :return: Hook action which is inserted at the beginning of the list of steps
        """
        return HammerToolHookAction(
            target_name="",
            location=HookLocation.PersistentStep,
            step=HammerTool.make_step_from_function(func)
        )

    @staticmethod
    def make_pre_persistent_hook(step: str, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Helper function to always insert a step at the beginning,
        when the steps to be executed are all before the given step.

        :return: Hook action which is inserted at the beginning of the list of steps
        """
        return HammerToolHookAction(
            target_name=step,
            location=HookLocation.PersistentPreStep,
            step=HammerTool.make_step_from_function(func)
        )

    @staticmethod
    def make_post_persistent_hook(step: str, func: HammerStepFunction) -> HammerToolHookAction:
        """
        Helper function to always insert a step at the beginning,
        when the steps to be executed are all after the given step.

        :return: Hook action which is inserted at the beginning of the list of steps
        """
        return HammerToolHookAction(
            target_name=step,
            location=HookLocation.PersistentPostStep,
            step=HammerTool.make_step_from_function(func)
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

    def get_config(self) -> Tuple[List[dict], List[dict]]:
        """Get the config for this tool."""
        return hammer_config.load_config_from_defaults(self.package, types=True)

    def get_setting(self, key: str, nullvalue: Any = None) -> Any:
        """
        Get a particular setting from the database.

        :param key: Key of the setting to receive.
        :param nullvalue: Value to return in case of null (leave as None to use the default).
        """
        try:
            return self._database.get_setting(key, nullvalue)
        except AttributeError:
            raise ValueError("Internal error: no database set by hammer-vlsi")

    def get_setting_suffix(self, key: str, suffix: str, nullvalue: Any = None) -> Any:
        """
        Get a particular setting from the database with a suffix.

        :param key: Key of the setting to receive.
        :param suffix: Suffix to search for on top of the base.
        :param nullvalue: Value to return in case of null (leave as None to use the default).
        """
        try:
            return self._database.get_setting_suffix(key, suffix, nullvalue)
        except AttributeError:
            raise ValueError("Internal error: no database set by hammer-vlsi")

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a runtime setting in the database.
        """
        self._database.set_setting(key, value)

    def get_settings_from_dict(self, key_default_dict: Dict[str, Any], key_prefix: str = "", optional_keys: List[str] = []) -> Dict[str, str]:
        """
        Gets input values for multiple keys.
        """
        return self._database.get_settings_from_dict(key_default_dict, key_prefix, optional_keys)

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

    def filter_for_mmmc(self, voltage: VoltageValue, temp: TemperatureValue) -> Callable[[hammer_tech.Library],bool]:
        """
        Selecting libraries that match given temp and voltage.
        """
        def extraction_func(lib: hammer_tech.Library) -> bool:
            if lib.corner is None or lib.corner.temperature is None:
                return False
            if lib.supplies is None or lib.supplies.VDD is None:
                return False
            lib_temperature = TemperatureValue(str(lib.corner.temperature))
            lib_VDD = VoltageValue(str(lib.supplies.VDD))
            if lib_temperature == temp:
                if lib_VDD == voltage:
                    return True
                else:
                    return False
            else:
                return False
        return extraction_func

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
    def run_executable(self, args: List[str], cwd: Optional[str] = None) -> str:
        """
        Run an executable and log the command to the log while also capturing the output.

        :param args: Command-line to run; each item in the list is one token. The first token should be the command to run.
        :param cwd: Working directory (leave as None to use the current working directory).
        :return: Output from the command or an error message.
        """
        (output, returncode) = self.submit_command.submit(args, self._subprocess_env, self.logger, cwd)

        if returncode != 0: # negative number denotes killed/terminated
            self.handle_errors(output, returncode)

        return output

    def handle_errors(self, output: str, code: int) -> bool:
        """
        Function to run on tool error (nonzero return code).
        Intended to be overridden by subclasses.

        :return: True if successful, False otherwise.
        """
        return True

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
                uncertainty=None, path=None, generated=None, source_path=None, divisor=None, group=None
            )
            if "path" in clock_port:
                clock = clock._replace(path=clock_port["path"])
            if "uncertainty" in clock_port:
                clock = clock._replace(uncertainty=TimeValue(clock_port["uncertainty"]))
            if "group" in clock_port:
                clock = clock._replace(group=clock_port["group"])
            generated = None  # type: Optional[bool]
            if "generated" in clock_port:
                generated = bool(clock_port["generated"])
                if generated:
                    clock = clock._replace(
                        source_path=clock_port["source_path"],
                        divisor=int(clock_port["divisor"])
                    )
            clock = clock._replace(generated=generated)
            output.append(clock)
        return output

    def get_time_unit(self) -> TimeValue:
        """
        Return the library time value.
        """
        return TimeValue(get_or_else(self.technology.config.time_unit, "1 ns"))


    def get_all_supplies(self, key: str) -> List[Supply]:
        supplies = self.get_setting(key)
        output = []  # type: List[Supply]
        for raw_supply in supplies:
            supply = Supply(name=raw_supply['name'], pin=None, tie=None, weight=1)
            if 'pin' in raw_supply:
                supply = supply._replace(pin=raw_supply['pin'])
            if 'tie' in raw_supply:
                supply = supply._replace(tie=raw_supply['tie'])
            if 'weight' in raw_supply:
                supply = supply._replace(weight=raw_supply['weight'])
            output.append(supply)
        return output

    def get_all_power_nets(self) -> List[Supply]:
        return self.get_all_supplies("vlsi.inputs.supplies.power")

    def get_independent_power_nets(self) -> List[Supply]:
        return list(filter(lambda x: x.tie is None, self.get_all_power_nets()))

    def get_all_ground_nets(self) -> List[Supply]:
        return self.get_all_supplies("vlsi.inputs.supplies.ground")

    def get_independent_ground_nets(self) -> List[Supply]:
        return list(filter(lambda x: x.tie is None, self.get_all_ground_nets()))

    def _get_by_bump_dim_pitch(self) -> Dict[str, float]:
        """
        Return pitches in the x and y directions. 
        """
        pitch_x = self.get_setting_suffix('vlsi.inputs.bumps.pitch', 'x')
        pitch_y = self.get_setting_suffix('vlsi.inputs.bumps.pitch', 'y')

        return {'x': pitch_x, 'y': pitch_y}

    def get_bumps(self) -> Optional[BumpsDefinition]:
        bumps_mode = self.get_setting("vlsi.inputs.bumps_mode")
        if bumps_mode == "empty":
            return None
        elif bumps_mode != "manual":
            self.logger.error("Invalid bumps_mode:{m}, only empty or manual supported. Assuming empty.".format(
                m=bumps_mode))
            return None
        assignments = []  # type: List[BumpAssignment]
        for raw_assign in self.get_setting("vlsi.inputs.bumps.assignments"):
            name = None if not "name" in raw_assign else raw_assign["name"]
            no_con = False if not "no_connect" in raw_assign else raw_assign["no_connect"]
            x = raw_assign["x"]
            y = raw_assign["y"]
            group = None if not "group" in raw_assign else raw_assign["group"]
            cell = None if not "custom_cell" in raw_assign else raw_assign["custom_cell"]
            if name is None and not no_con:
                self.logger.warning("Invalid bump assignment, neither name nor no_connect specified for bump {x},{y}. Assuming it should be unassigned".format(
                    x=x, y=y))
            else:
                assignments.append(BumpAssignment(name=name, no_connect=no_con,
                    x=x, y=y, group=group, custom_cell=cell))
        
        pitch_settings = self._get_by_bump_dim_pitch()

        return BumpsDefinition(
            x=self.get_setting("vlsi.inputs.bumps.x"),
            y=self.get_setting("vlsi.inputs.bumps.y"),
            pitch_x = Decimal(str(pitch_settings['x'])),
            pitch_y = Decimal(str(pitch_settings['y'])),
            global_x_offset=Decimal(str(self.get_setting("vlsi.inputs.bumps.global_x_offset"))),
            global_y_offset=Decimal(str(self.get_setting("vlsi.inputs.bumps.global_y_offset"))),
            cell=self.get_setting("vlsi.inputs.bumps.cell"), assignments=assignments)

    def generate_visualization(self) -> None:
        """
        Generate an SVG visualizing the chip.
        Depending on mode, it will display floorplan (placement constraints for the current hierarchy)
        and/or bumps (overlaid on top of floorplan) and pad designators (if this tool is a PCBDeliverableTool).
        Call this from any custom hook (not used by any default flow).
        Note: visualizations generated within a PCBDeliverableTool are mirrored about the y-axis (assumption: flip-chip on PCB)
        """
        viz_mode = self.get_setting("vlsi.inputs.visualization.mode") #type: str
        viz_file = self.get_setting("vlsi.inputs.visualization.svg_file") #type: str
        shorten_path_depth = self.get_setting("vlsi.inputs.visualization.shorten_path_depth") #type: int

        # Checks
        if not viz_mode in ["all", "floorplan", "bumps", "footprint"]:
            self.logger.error("Invalid type for 'vlsi.inputs.visualization.type'! No visualization generated.")
            return

        fp_consts = self.get_placement_constraints() #type: List[PlacementConstraint]
        # TODO: make pcb action recognize toplevel constraint if par action had hierarchical constraints
        try:
            # Get toplevel constraint
            top = next(filter(lambda x: x.type == PlacementConstraintType.TopLevel, fp_consts)) #type: PlacementConstraint
        except:
            self.logger.error("You must at least have a 'toplevel' type placement constraint to generate a visualization!")
            return

        # TODO: support fractional bump coordinates when generating footprint
        from .hammer_vlsi_impl import HammerPCBDeliverableTool
        is_pcb_tool = isinstance(self, HammerPCBDeliverableTool)
        if not is_pcb_tool:
            if viz_mode == "footprint":
                self.logger.error("Can't generate footprint alone if this isn't a PCBDeliverableTool.")
                return
            elif viz_mode == "all":
                self.logger.info("Visualizing in 'all' mode but not a PCBDeliverableTool. Skipping drawing pad designators.")

        # Shorten path names to first letters except lowest "depth" levels in hierarchy
        def shorten(path: str) -> str:
            if shorten_path_depth > 0:
                parent = path.split('/')[:-shorten_path_depth]
                inst = path.split('/')[-shorten_path_depth:]
                return '/'.join([p[0] for p in parent] + inst)
            else:
                return path

        # Get all bump & macro sizes from their masters when constraint width & height are not defined
        def get_macro_wh(macro: Optional[str]) -> Tuple[Decimal, Decimal]:
            # take 1st definition of macro
            try:
                size = next(filter(lambda x: x.name == macro, macro_sizes))
                return (size.width, size.height)
            except:
                self.logger.warning("Size of {} not found in any LEFs! Defaulting to 10um x 10um. Try manually specifying width & height.".format(macro))
                return (Decimal("10"), Decimal("10"))

        fsvg = open(os.path.join(self.run_dir, viz_file), 'w')

        # Translate all shapes by (1, title height)
        title_height = 100
        translate = "translate(1 {})".format(title_height)

        # Header & style
        fsvg.write("""<?xml version="1.0"?>
        <!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
        <svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}">
        """.format(top.width+2, top.height+title_height+1))
        fsvg.write("""<defs><style type="text/css">
        rect { stroke: #000000; fill: #ffffff; }
        .bold12pt { font-family: sans-serif; font-weight: bold; font-size: 12pt; }
        .bold10pt { font-family: sans-serif; font-weight: bold; font-size: 10pt; }
        #chip_name { font-family: sans-serif; font-weight: bold; font-size: 40pt; }
        .ref_mark { fill: #000000 }
        .macro { fill: #aaaaaa; }
        .obs { fill: #ffff00; }
        .power { fill: #ff4040; }
        .ground { fill: #ffa500; }
        .signal { fill: #6060ff; }
        .nc { fill: #dddddd; }
        .orient { stroke: #000000; stroke-width: 2; }
        </style></defs>\n""")

        # Print chip name on top, draw design & core area bboxes, place reference marking if in any mode but "floorplan"
        fsvg.write("<g>\n")
        fsvg.write('<rect x="1" y="{}" width="{}" height="{}" id="die"/>\n'.format(title_height, top.width, top.height))
        fsvg.write('<text x="{}" y="{}" text-anchor="start" class="bold10pt">visualization mode: {}</text>\n'.format(10, title_height/2-30, viz_mode))
        fsvg.write('<text x="{}" y="{}" text-anchor="start" class="bold10pt">design size: {}um x {}um</text>\n'.format(10, title_height/2-10, top.width, top.height))
        ref_x = 15 if is_pcb_tool else top.width-15
        fsvg.write('<circle cx="{}" cy="{}" r="{}" class="ref_mark" />\n'.format(ref_x, title_height+15, 10))

        core_width = top.width-getattr(top.margins, "left", 0)-getattr(top.margins, "right", 0)
        core_height = top.height-getattr(top.margins, "top", 0)-getattr(top.margins, "bottom", 0)
        fsvg.write('<rect x="{}" y="{}" width="{}" height="{}" id="core"/>\n'.format(getattr(top.margins, "left", 0)+1, title_height+getattr(top.margins, "top", 0), core_width, core_height))
        fsvg.write('<text x="{}" y="{}" text-anchor="middle" alignment-baseline="middle" id="chip_name">{}</text>\n'.format(top.width/2, title_height/2, top.path))

        # Get macro sizes from LEFs
        macro_sizes = self.technology.get_macro_sizes() #type: List[MacroSize]

        # Visualize floorplan (from placement_constraints)
        if viz_mode in ["all", "floorplan"]:
            macro_rects = macro_text = obs_rects = obs_text = orient_lines = '<g transform="{}">\n'.format(translate)
            for c in fp_consts:
                if c.type in [PlacementConstraintType.Placement, PlacementConstraintType.HardMacro, PlacementConstraintType.Hierarchical]:
                    # macros & hierarchical not required to have width/height, will resolve to 0
                    (width, height) = (c.width, c.height)
                    if width == 0 or height == 0:
                        if c.master is None:
                            self.logger.warning('Constraint for {} has no master and is missing width and/or height! It will not show up in visualization.'.format(c.path))
                            continue
                        else:
                            (width, height) = get_macro_wh(c.master)
                    # skip if width/height are larger than core area (probably IO or die ring overlay)
                    if width >= core_width or height >= core_height:
                        self.logger.info("Skipping visualizing {} because it extends beyond core area.".format(c.path))
                        continue
                    c_x = c.x
                    if is_pcb_tool: # mirror about y-axis
                        c_x = top.width - c_x - width
                    macro_rects += '<rect x="{}" y="{}" width="{}" height="{}" class="macro" />\n'.format(c_x, top.height-c.y-height, width, height)
                    macro_text += '<text text-anchor="middle" x="{}" y="{}" class="bold12pt">{}</text>\n'.format(c_x+width/2, top.height-c.y-height/2, shorten(c.path))
                    # calculate orientation line start & end. None orientation implies r0.
                    # only supports r0, mx, my, r180
                    line_start_end = [c_x, top.height-c.y-height/4, c_x + width/8, top.height-c.y] # x1, y1, x2, y2
                    if c.orientation is not None:
                        if (c.orientation.lower() in ["my", "r180"]) ^ is_pcb_tool:
                            line_start_end[0] += width
                            line_start_end[2] += width*6/8
                        if c.orientation.lower() in ["mx", "r180"]:
                            line_start_end[1] -= height*2/4
                            line_start_end[3] -= height
                    orient_lines += '<line x1="{}" y1="{}" x2="{}" y2="{}" class="orient" />\n'.format(*line_start_end)
                elif c.type == PlacementConstraintType.Obstruction:
                    # already enforced to have width & height
                    obs_rects += '<rect x="{}" y="{}" width="{}" height="{}" class="obs" />\n'.format(c.x, top.height-c.y-c.height, c.width, c.height)
                    obs_text += '<text text-anchor="middle" x="{}" y="{}" class="bold10pt">{}</text>\n'.format(c.x+c.width/2, top.height-c.y-c.height/2, shorten(c.path))
                elif c.type == PlacementConstraintType.Overlap:
                    self.logger.info('Overlap constraint {} skipped from visualization.'.format(c.path))

            # Draw order: obstructions, macros, orientation lines
            fsvg.write("</g>\n".join([obs_rects, obs_text, macro_rects, macro_text, orient_lines]) + "</g>\n")

        # Visualize bump placement & assignment
        if viz_mode in ["all", "bumps", "footprint"]:
            bumps = self.get_bumps() #type: Optional[BumpsDefinition]
            if bumps is None:
                self.logger.error("Not using bumps API, can't draw bumps or footprint!")
                fsvg.write("</g>\n</svg>\n")
                fsvg.close()
                return
            bp_x = bumps.pitch_x
            bp_y = bumps.pitch_y
            global_x_os = bumps.global_x_offset
            global_y_os = bumps.global_y_offset
            bump_radius = get_macro_wh(bumps.cell)[0]/2
            # Bumps API centers bumps in design
            x_os = (top.width-(bumps.x-1)*bp_x)/2 + global_x_os
            y_os = (top.height-(bumps.y-1)*bp_y)/2 + global_y_os
            fsvg.write('<text x="{}" y="{}" text-anchor="start" class="bold10pt">bump pitch x: {}um</text>\n'.format(10, title_height/2+10, bp_x))
            fsvg.write('<text x="{}" y="{}" text-anchor="start" class="bold10pt">bump grid: {} x {}</text>\n'.format(10, title_height/2+30, bumps.x, bumps.y))
            bump_circles = bump_text = bump_lblx = bump_lbly = '<g transform="{}">\n'.format(translate)

            p_nets = self.get_all_power_nets() #type: List[Supply]
            g_nets = self.get_all_ground_nets() #type: List[Supply]
            for b in bumps.assignments: # type: BumpAssignment
                bump_type = 'signal'
                if b.no_connect:
                    bump_type = 'nc'
                # TODO: Hammer's concept of P/G nets may be different from what's specified in CPF
                elif b.name in [p.name for p in p_nets]:
                    bump_type = 'power'
                elif b.name in [g.name for g in g_nets]:
                    bump_type = 'ground'

                b_x = x_os+Decimal(str(b.x-1))*bp_x
                if is_pcb_tool: # mirror about y-axis
                    b_x = top.width - b_x
                b_y = top.height-y_os-Decimal(str(b.y-1))*bp_y

                bump_circles += '<circle cx="{}" cy="{}" r="{}" class="{}" />\n'.format(b_x, b_y, bump_radius, bump_type)
                if viz_mode == "bumps" or not is_pcb_tool: # don't print pad designator also
                    bump_text += '<text text-anchor="middle" x="{}" y="{}" class="bold10pt">{}</text>\n'.format(b_x, b_y, b.name)
                else:
                    naming_scheme = self.naming_scheme #type: ignore
                    bump_text += '<text text-anchor="middle" x="{}" y="{}">\n'.format(b_x, b_y)
                    bump_text += '\t<tspan class="bold10pt" x="{}" dy="-.6em">{}</tspan>\n'.format(b_x, naming_scheme.name_bump(bumps, b))
                    bump_text += '\t<tspan class="bold10pt" x="{}" dy="1.2em">{}</tspan>\n'.format(b_x, b.name)
                    bump_text += '</text>\n'

            # Mark every 5th bump (helpful for large chips)
            for i in range(4, bumps.x, 5):
                lbl_x = x_os+i*bp_x
                if is_pcb_tool: # mirror about y-axis
                    lbl_x = top.width - lbl_x
                bump_lblx += '<text text-anchor="middle" x="{}" y="{}" class="bold12pt">{}</text>\n'.format(lbl_x, top.height-10, i+1)
                bump_lblx += '<text text-anchor="middle" x="{}" y="{}" class="bold12pt">{}</text>\n'.format(lbl_x, 15, i+1)
            for i in range(4, bumps.y, 5):
                lbl_y = top.height-y_os-i*bp_y
                bump_lbly += '<text text-anchor="start" x="{}" y="{}" class="bold12pt">{}</text>\n'.format(5, lbl_y, i+1)
                bump_lbly += '<text text-anchor="end" x="{}" y="{}" class="bold12pt">{}</text>\n'.format(top.width-5, lbl_y, i+1)

            fsvg.write("</g>\n".join([bump_circles, bump_text, bump_lblx, bump_lbly]) + "</g>\n")

        fsvg.write("</g>\n</svg>\n")
        fsvg.close()

    def get_pin_assignments(self) -> List[PinAssignment]:
        """
        Get a list of pin assignments in accordance with settings in the Hammer IR.
        :return: A potentially empty list of PinAssigments.
        """
        pin_mode = str(self.get_setting("vlsi.inputs.pin_mode"))  # type: str
        if pin_mode == "none":
            return []
        elif pin_mode == "generated":
            pass
        else:
            self.logger.error(
                "Invalid pin_mode {mode}. Using none pin mode.".format(mode=pin_mode))
            return []

        generate_mode = str(self.get_setting("vlsi.inputs.pin.generate_mode"))
        if generate_mode not in ("full_auto", "semi_auto"):
            raise ValueError("Invalid generate_mode {}".format(generate_mode))
        semi_auto = generate_mode == "semi_auto"

        # Generated pin mode needs to ingest the assignments
        assigns = []  # type: List[PinAssignment]
        for raw_assign in self.get_setting("vlsi.inputs.pin.assignments"):
            try:
                pin = PinAssignment.from_dict(raw_assign, semi_auto)
            except PinAssignmentSemiAutoError as e:
                # Raise this as an error
                self.logger.error("Semi-auto pin assigment feature used without enabling semi_auto mode: " + str(e))
                continue
            except PinAssignmentPreplacedError as e:
                # Accept the pin assignment and ignore extra information
                self.logger.warning(str(e))
                assigns.append(e.pin)
                continue
            except PinAssignmentError as e:
                # Ignore the invalid pin
                self.logger.warning(str(e))
                continue

            if pin.layers is not None:
                stackup = self.get_stackup()
                for layer in pin.layers:
                    direction = stackup.get_metal(layer).direction
                    is_horizontal = direction == RoutingDirection.Horizontal and (
                                pin.side == "left" or pin.side == "right")
                    is_vertical = direction == RoutingDirection.Vertical and (pin.side == "top" or pin.side == "bottom")
                    is_redis = direction == RoutingDirection.Redistribution
                    if not (is_horizontal or is_vertical or is_redis):
                        self.logger.error(
                            "Pins {p} assigned layers {l} that do not match the direction of their side {s}. This is very likely to cause issues.".format(
                                p=pin.pins, l=pin.layers, s=pin.side))
            assigns.append(pin)
        return assigns

    def get_gds_map_file(self) -> Optional[str]:
        """
        Get a GDS map in accordance with settings in the Hammer IR.
        Return a fully-resolved (i.e. already prepended path) path to the GDS map or None if none was specified.
        :return: Fully-resolved path to GDS map file or None.
        """
        # Mode can be auto, empty, or manual
        gds_map_mode = str(self.get_setting("par.inputs.gds_map_mode"))  # type: str

        # gds_map_file will only be used in manual mode
        # Not including the map_file flag includes all layers but with no specific layer numbers
        manual_map_file: Optional[str] = str(self.get_setting("par.inputs.gds_map_file")) if self.get_setting(
            "par.inputs.gds_map_file") is not None else None

        # tech_map_file will only be used in auto mode
        tech_map_file_raw = self.technology.config.gds_map_file
        tech_map_file_optional = str(
            tech_map_file_raw) if tech_map_file_raw is not None else None  # type: Optional[str]
        tech_map_file = optional_map(tech_map_file_optional, lambda p: self.technology.prepend_dir_path(p))

        if gds_map_mode == "auto":
            map_file = tech_map_file
        elif gds_map_mode == "manual":
            if manual_map_file:
                map_file = manual_map_file
            else:
                raise ValueError("par.inputs.gds_map_mode set to manual but no par.inputs.gds_map_file specified!")
        elif gds_map_mode == "empty":
            map_file = None
        else:
            self.logger.error(
                "Invalid gds_map_mode {mode}. Using auto gds map.".format(mode=gds_map_mode))
            map_file = tech_map_file

        return map_file

    def get_physical_only_cells(self) -> List[str]:
        """
        Get a list of physical only cells in accordance with settings in the Hammer IR.
        Return a list of cells which are physical only.
        :return: A list of physical only cells.
        """
        # Mode can be auto, manual, or append
        physical_only_cells_mode = str(self.get_setting("par.inputs.physical_only_cells_mode"))  # type: str

        # physical_only_cells_list will only be used in manual and append mode
        manual_physical_only_cells_list = self.get_setting("par.inputs.physical_only_cells_list")  # type: List[str]
        assert isinstance(manual_physical_only_cells_list, list), "par.inputs.physical_only_cells_list must be a list"

        # tech_physical_only_cells_list will only be used in auto and append mode
        tech_physical_only_cells_list = get_or_else(self.technology.physical_only_cells_list, [])  # type: List[str]

        # Default to auto (use tech_physical_only_cells_list).
        physical_only_cells_list = tech_physical_only_cells_list  # type: List[str]

        if physical_only_cells_mode == "auto":
            pass
        elif physical_only_cells_mode == "manual":
            physical_only_cells_list = manual_physical_only_cells_list
        elif physical_only_cells_mode == "append":
            physical_only_cells_list = tech_physical_only_cells_list + manual_physical_only_cells_list
        else:
            self.logger.error(
                "Invalid physical_only_cells_mode {mode}. Using auto physical only cells list.".format(mode=physical_only_cells_mode))

        return physical_only_cells_list

    def get_dont_use_list(self) -> List[str]:
        """
        Get a "don't use" list in accordance with settings in the Hammer IR.
        Return a list of cells to mark as "don't use".
        :return: A list of cells to avoid using.
        """
        # Mode can be auto, manual, or append
        dont_use_mode = str(self.get_setting("vlsi.inputs.dont_use_mode"))  # type: str

        # dont_use_list will only be used in manual and append mode
        manual_dont_use_list = self.get_setting("vlsi.inputs.dont_use_list")  # type: List[str]
        assert isinstance(manual_dont_use_list, list), "vlsi.inputs.dont_use_list must be a list"

        # tech_dont_use_list will only be used in auto and append mode
        tech_dont_use_list = get_or_else(self.technology.dont_use_list, [])  # type: List[str]

        # Default to auto (use tech_dont_use_list).
        dont_use_list = tech_dont_use_list  # type: List[str]

        if dont_use_mode == "auto":
            pass
        elif dont_use_mode == "manual":
            dont_use_list = manual_dont_use_list
        elif dont_use_mode == "append":
            dont_use_list = tech_dont_use_list + manual_dont_use_list
        else:
            self.logger.error(
                "Invalid dont_use_mode {mode}. Using auto dont use list.".format(mode=dont_use_mode))

        return dont_use_list

    def get_placement_constraints(self) -> List[PlacementConstraint]:
        """
        Get a list of placement constraints as specified in the config.
        """
        constraints = self.get_setting("vlsi.inputs.placement_constraints")
        assert isinstance(constraints, list)
        # At this point, the optional width/height placement constraints have been resolved,
        # so there is no need to pass the masters in here, meaning we can use from_dict.
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

    def get_stackup(self) -> Stackup:
        """
        Get the stackup provided by the technology key
        """
        # TODO how does python cache this? Do we need to avoid re-processing this every time?
        return self.technology.get_stackup_by_name(self.get_setting("technology.core.stackup"))

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

    def get_delay_constraints(self) -> List[DelayConstraint]:
        """
        Get a list of input and output delay constraints as specified in
        the config.
        """
        delays = self.get_setting("vlsi.inputs.delays")  # type: List[dict]
        output = list(map(DelayConstraint.from_dict, delays))  # type: List[DelayConstraint]
        return output

    def get_decap_constraints(self) -> List[DecapConstraint]:
        """
        Get a list of decapacitance constraints as specified in
        the config.
        """
        decaps = self.get_setting("vlsi.inputs.decaps")  # type: List[dict]
        output = list(map(DecapConstraint.from_dict, decaps))  # type: List[DecapConstraint]
        return output

    @property
    def header(self) -> str:
        """
        Header text for files.
        Intended to be overridden by subclasses if syntax- or vendor-specific headers are necessary.
        """
        return "# This script is generated by HAMMER"

    def write_contents_to_path(self, content_to_write: str, target_path: str, append: bool = False) -> None:
        """
        Write or optionally append the given contents to the file located at target_path, if target_path is not empty.

        :param content_to_write: Content to write.
        :param target_path: Where to write the content.
        :param append: True if you want to append to the file, else overwrite it with a header + content_to_write.
        """
        if append:
            if content_to_write != "":
                with open(target_path, "a") as f:
                    f.write(content_to_write)
        else:
             content_with_header = self.header + "\n\n" + content_to_write
             with open(target_path, "w") as f:
                 f.write(content_with_header)

    @staticmethod
    def tcl_append(cmd: str, output_buffer: List[str], clean: bool = False) -> None:
        """
        Helper function to echo and run a command.

        :param cmd: TCL command to run
        :param output_buffer: Buffer in which to enqueue the resulting TCL lines
        :param clean: True if you want to trim the leading indendation from the string, False otherwise. See inspect.cleandoc() for what this does.
        >>>
        """
        output_buffer.append(cleandoc(cmd) if clean else cmd)

    @staticmethod
    def verbose_tcl_append(cmd: str, output_buffer: List[str], clean: bool = False) -> None:
        """
        Helper function to echo and run a command.

        :param cmd: TCL command to run
        :param output_buffer: Buffer in which to enqueue the resulting TCL lines
        :param clean: True if you want to trim the leading indendation from the string, False otherwise. See inspect.cleandoc() for what this does.
        """
        cleaned = cleandoc(cmd) if clean else cmd
        output_buffer.append("""puts "{0}" """.format(cleaned.replace('"', '\"')))
        output_buffer.append(cleaned)
