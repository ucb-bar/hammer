.. _flow-control:

Flow Control
=======================================

Physical design is necessarily an iterative process, and designers will often require fine control of the flow within any given action.
This allows for rapid testing of new changes in the Hammer IR  to improve the quality of results (QoR) after certain steps.

Given the flow defined by tool steps and hooks (described in the next section), users can select ranges of these to run.
The tool script will then be generated with commands corresponding to only the steps that are to be run.

Command-line Interface
----------------------

Flow control is specified with the following optional Hammer command-line flags, which must always target a valid step/hook:

* ``--from_step <target>``: this starts the tool from (inclusive) the target step
* ``--after_step <target>``: this starts the tool from (exclusive) the target step
* ``--to_step``: this stops the tool at (inclusive) the target step
* ``--until_step``: this stops the tool at (exclusive) the target step
* ``--only_step``: this only runs the target step

As ``hammer-vlsi`` is parsing through the steps for a given tool, it will print debugging information indicating which steps are skipped and which are run.

Certain combinations are not allowed:

* ``--only_step`` is not compatible with any of the other flags
* ``--from_step`` and ``after_step`` may not be specified together
* ``--to_step`` and ``--until_step`` may not be specified together
* ``--from_step`` and ``--until_step`` may not be the same step
* ``--after_step`` and ``--to_step`` may not be the same step
* ``--after_step`` and ``--until_step`` may not be the same or adjacent steps

Logically, a target of ``to/until_step`` before ``from/after_step`` will also not run anything (though it is not explicitly checked).
