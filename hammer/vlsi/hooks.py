#  hooks.py
#  Classes and functions related to Hammer hooks.
#
#  See LICENSE for licence details.

from enum import Enum
from typing import Callable, NamedTuple, Optional, TYPE_CHECKING

__all__ = ['HammerStepFunction', 'HammerToolStep', 'HookLocation', 'HammerToolHookAction']

# Necessary for mypy to learn about HammerTool.
if TYPE_CHECKING:
    from .hammer_tool import HammerTool  # pylint: disable=unused-import

HammerStepFunction = Callable[['HammerTool'], bool]

HammerToolStep = NamedTuple('HammerToolStep', [
    # Function to call to execute this step
    ('func', HammerStepFunction),
    # Name of the step
    ('name', str)
])

# Specify step to start/stop
HammerStartStopStep = NamedTuple('HammerStartStopStep', [
    # Name of the step
    ('step', Optional[str]),
    # Whether it is inclusive
    ('inclusive', bool)
])

# Where to insert/replace the given step.
# Persistent steps always execute depending on from/after/to/until steps.
class HookLocation(Enum):
    InsertPreStep = 1
    InsertPostStep = 2
    ReplaceStep = 10
    ResumePreStep = 20
    ResumePostStep = 21
    PausePreStep = 30
    PausePostStep = 31
    PersistentStep = 40
    PersistentPreStep = 41
    PersistentPostStep = 42

# An hook action. Actions can insert new steps before or after an existing one,
# or replace an existing stage.
# Note: hook actions are executed in the order provided.
HammerToolHookAction = NamedTuple('HammerToolHookAction', [
    # Where/what to do
    ('location', HookLocation),
    # Target step to insert before/after or replace
    ('target_name', str),
    # Step to insert/replace
    ('step', Optional[HammerToolStep])
])
