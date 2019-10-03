Hammer Buildfile
==========================================

Hammer natively supports a GNU Make-based build system to manage dependencies. When the ``vlsi.core.build_system`` is set to ``make`` and hammer is evoked like as follows:

.. code-block:: shell

    ``hammer-vlsi -e env.yml -p config.yml --obj_dir build build``

Hammer will generate a file ``hammer.d`` in the ``build`` folder. Inside, it will contain environment variables needed by Hammer and a set of targets articulating Hammer commands for every action. Dependencies are tracked, e.g. if the ``config.yml`` was changed, it will automatically re-run synthesis.

To enable advanced usage, a set of "redo" targets is provided for manual dependency breaking and the ability to add additional arguments to the ``hammer-vlsi`` command using the ``HAMMER_REDO_ARGS`` variable.

This buildfile can be included in any higher-level Makefile. An example is found in `Chipyard <https://github.com/ucb-bar/chipyard/blob/master/vlsi/Makefile>`__.
