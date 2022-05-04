.. _hooks:

Extending Hammer with Hooks
=======================================

It is unlikely that using the default Hammer APIs alone will produce DRC- and LVS-clean designs with good QoR in advanced technology nodes if the design is sufficiently complex.
To solve that, Hammer is extensible using *hooks*.
These hooks also afford power users additional flexibility to experiment with CAD tool commands to tweak aspects of their designs.
The hook framework is inherently designed to enable reusability, because successful hook methods that solve a technology-specific problem may be upstreamed into the technology plugin for future designs.

Hook Methods
------------

Hooks are fundamentally Python methods that extend a given tool's set of available steps and can inject additional TCL commands into the flow. 
Hook methods need to take in an instance of a particular ``HammerTool``, which provides them with the full set of Hammer IR available to the tool.
Hooks (depending on how they are included, see below) get turned into step objects that can be targeted with ``--from/after/to/until_step`` and other hooks.

Hooks can live in a Python file inside the design root so that it is available to the class that needs to extend the default ``CLIDriver``.
An example of some skeletons of hooks are found in `Chipyard <https://github.com/ucb-bar/chipyard/blob/master/vlsi/example-vlsi>`__.
For more comprehensive examples, refer to the hooks unit tests in the ``HammerToolHooksTest`` class of `test.py <https://github.com/ucb-bar/hammer/blob/master/src/hammer-vlsi/test.py>`__.

Including Hooks
----------------

Hooks modify the flow using a few ``HammerTool`` methods, such as:

* ``make_replacement_hook(<target>, <hook_method>)``: this swaps out an existing target step/hook with the hook method
* ``make_pre_insertion_hook(<target>, <hook_method>)``: this inserts the hook method before the target step/hook
* ``make_post_insertion_hook(<target>, <hook_method>)``: this inserts the hook method after the target step/hook
* ``make_removal_hook(<target>)``: this removes the target step/hook from the flow

Note: ``<target>`` should be a string (name of step/hook), while ``<hook_method>`` is the hook method itself.
All of the hook methods specified this way are targetable by other hooks.

Sometimes, CAD tools do not save certain settings into checkpoint databases.
As a result, when for example a ``--from_step`` is called, the setting will not be applied when the database from which to continue the flow is read in.
To get around this, a concept of "persistence" is implemented with the following methods:

* ``make_persistent_hook(<hook_method>)``: this inserts the hook method at the beginning of any tool invocation, regardless of which steps/hooks are run
* ``make_pre_persistent_hook(<target>, <hook_method>)``: this inserts the hook method at the beginning of any tool invocation, as long as the target step/hook is located at or after the first step to be run
* ``make_post_persistent_hook(<target>, <hook_method>)``: this inserts the hook method at the beginning of any tool invocation if the target step/hook is before the first step to be run, or right after the target step/hook if that step/hook is within the steps to be run.

All persistent hooks are NOT targetable by flow control options, as their invocation location may vary.
However, persistent hooks ARE targetable by ``make_replacement/pre_insertion/post_insertion/removal_hook``.
In this case, the hook that replaces or is inserted pre/post the target persistent hook takes on the persistence properties of the target persistence hook.

Some examples of these methods are found in the Chipyard example, linked above.

A list of these hooks must be provided in an implementation of method such as ``get_extra_par_hooks`` in the command-line driver. This new file becomes the entry point into Hammer, overriding the default ``hammer-vlsi`` executable.

Technology, Tool, and User-Provided Hooks
-----------------------------------------

Hooks may be provided by the technology plugin, the tool plugin, and/or the user. The order of step & hook priority is as follows, from lowest to highest:

1. technology default steps
2. technology plugin hooks
3. tool plugin hooks
4. user hooks

A technology plugin specifies hooks in its ``__init__.py`` (as a method inside its subclass of ``HammerTechnology``). It should implement a ``get_tech_<action>_hooks(self, tool_name: str)`` method. The tool name parameter may be checked by the hook implementation because multiple tools may implement the same action. Technology plugin hooks may only target technology default steps to insert/replace.

The included ASAP7 technology plugin provides an example of how to inject two different types of hooks: 1) a persistent hook invoked anytime after the ``init_design`` step to set top & bottom routing layers, and 2) two post-insertion hooks, one to modify the floorplan for DRCs and the other to scale down a GDS post-place-and-route using the ``gdstk`` or ``gdspy`` GDS manipulation utilities.
Note that the persistent hook that is included does not necessarily need to be persistent (Innovus does retain this setting in snapshot databases), but it serves as an example for building your own tech plugin.

A tool plugin specifies hooks in its ``__init__.py`` (as a method inside its subclass of ``HammerTool``). It should implement a ``get_tool_hooks(self)`` method. In contrast to the tech-supplied hooks, the action name and tool name are not specified because a tool instance can only correspond to a single action. Tool plugin hooks may target technology default steps and technology plugin hooks to insert/replace.

A user specifies hooks in the command-line driver and should implement a ``get_extra_<action>_hooks(self)`` method. User hooks may target technology default steps, technology plugin hooks, and tool plugin hooks to insert/replace. A good example is the ``example-vlsi`` file in the Chipyard example, which implements a ``get_extra_par_hooks(self)`` method that returns a list of hook inclusion methods. 

The priority means that if both the technology and user specify persistent hooks, any duplicate commands in the user's persistent hook will override those from the techonolgy's persistent hook.
