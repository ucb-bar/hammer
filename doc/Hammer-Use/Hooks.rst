Extending Hammer with Hooks
=======================================

It is unlikely that using the default Hammer APIs alone will produce DRC- and LVS-clean designs with good QoR in advanced technology nodes if the design is sufficiently complex.
To solve that, Hammer is extensible using *hooks*.
These hooks also afford power users additional flexibility to experiment with CAD tool commands to tweak aspects of their designs.

Hook Methods
------------

Hooks are fundamentally Python methods that extend a given tool's set of available steps and can inject additional TCL commands into the flow. Hook methods need to take in an instance of a particular ``HammerTool``, which provides them with the full set of Hammer IR available to the tool.

Hooks can live in a Python file inside the design root so that it is available to the class that needs to extend the default ``CLIDriver``. An example of some skeletons of hooks are found in `Chipyard <https://github.com/ucb-bar/chipyard/blob/master/vlsi/example-vlsi>`__.

Including Hooks
----------------

Hooks modify the flow using a few ``HammerTool`` methods, such as:
* ``make_replacement_hook``: this swaps out an existing step with the hook
* ``make_pre_insertion_hook``: this inserts the desired hook before a step or another hook
* ``make_post_insertion_hook``: this inserts the desired hook step a step or another hook
* ``make_removal_hook``: this just removes the given step/hook from the flow

All of these are found in the Chipyard example above.

A list of these hooks must be provided in an implementation of method such as ``get_extra_par_hooks`` in the command-line driver. This new file becomes the entry point into Hammer, overriding the default ``hammer-vlsi`` executable.

Plugin-Provided Hooks
---------------------

Hooks can also be provided by the technology or tool plugin. The linked Chipyard example includes an example of how the ASAP7 technology plugin injects a hook to scale down a GDS post-place-and-route.
