#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hooks.py
#  Classes and functions related to Hammer hooks.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from enum import Enum
from typing import Callable, NamedTuple, Optional, TYPE_CHECKING

__all__ = ['HammerStepFunction', 'HammerToolStep', 'HookLocation', 'HammerToolHookAction']

# Necessary for mypy to learn about HammerTool.
if TYPE_CHECKING:
    from .hammer_tool import HammerTool

HammerStepFunction = Callable[['HammerTool'], bool]

HammerToolStep = NamedTuple('HammerToolStep', [
    # Function to call to execute this step
    ('func', HammerStepFunction),
    # Name of the step
    ('name', str)
])


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
    ('step', Optional[HammerToolStep])
])
