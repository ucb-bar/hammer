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

Hooks may be provided by the technology plugin, the tool plugin, and/or the user. The order if priority is as follows, from highest to lowest:

1. user hooks
2. tool plugin hooks
3. technology plugin hooks
   
A user specifies hooks in the command-line driver. A good example is the ``example-vlsi`` file in the Chipyard example, which implements a ``get_extra_par_hooks(self)`` method that returns a list of hook inclusion methods. 

A tool plugin specifies hooks in its ``__init__.py`` (as a method inside its subclass of ``HammerTool``). It should implement a ``get_tool_<action>_hooks(self)`` method almost identically to how the user-specified case.

A technology plugin also specifies hooks in its ``__init__.py`` (as a method inside its subclass of ``HammerTechnology``). It should implement a ``get_tech_<action>_hooks(self, tool_name: str)`` method. The dfference here is that the tool name may also be checked, because multiple tools may implement the same action.

The linked Chipyard example includes an example of how the ASAP7 technology plugin injects a hook to scale down a GDS post-place-and-route in Innovus.
