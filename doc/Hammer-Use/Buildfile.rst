.. _buildfile:

Hammer Buildfile
==========================================

Hammer natively supports a GNU Make-based build system to manage build dependencies.
To use this flow, ``vlsi.core.build_system`` must be set to ``make``.
Hammer will generate a Makefile include in the object directory named ``hammer.d`` after calling the ``build`` action:

.. code-block:: shell

    hammer-vlsi -e env.yml -p config.yml --obj_dir build build

``build/hammer.d`` will contain environment variables needed by Hammer and a target for each major Hammer action (e.g. ``par``, ``synthesis``, etc. but not ``syn-to-par``, which is run automatically when calling ``make par``).
For a flat design, the dependencies are created betwen the major Hammer actions.
For hierarchical designs, Hammer will use the hierarchy to build a dependency graph and construct the Make target dependencies appropriately.

``hammer.d`` should be included in a higher-level Makefile.
While ``hammer.d`` defines all of the variables that it needs, there are often reasons to set these elsewhere.
Because ``hammer.d`` uses ``?=`` assignment, the settings created in the top-level Makefile will persist.
An example of this setup is found in `Chipyard <https://github.com/ucb-bar/chipyard/blob/master/vlsi/Makefile>`__.


To enable interactive usage, ``hammer.d`` also containts a set of companion "redo" targets (e.g. ``redo-par`` and ``redo-syn``).
These targets intentionally have no dependency information; they are for advanced users to make changes to the input config and/or edit the design manually, then continue the flow.
Additional arguments can be passed to the "redo" targets with the ``HAMMER_EXTRA_ARGS`` environment variable, for the following example uses:

* "Patching" the configuration for an action using ``HAMMER_EXTRA_ARGS="-p patch.yml"``.
* Flow control using ``--to_step/--until_step`` and ``--from_step/after_step`` to stop a run at a particular step or resume one from a previous iteration.

