.. _technology:

Hammer Technology Plugins
========================================

This guide will walk you through how to set up a technology plugin to be used in Hammer.

You may use the included `free ASAP7 PDK <https://github.com/ucb-bar/hammer/tree/master/hammer/technology/asap7>`__ or the `open-source Sky130 PDK <https://github.com/ucb-bar/hammer/tree/master/hammer/technology/sky130>`__ plugins as reference when building your own technology plugin.

Technology plugins must be structured as Python packages underneath the ``hammer`` package. The package should contain an class object named ``tech`` to create an instance of the technology. This object should be a subclass of ``HammerTechnology``.

Technology plugins must also have ``.tech.json`` and ``defaults.yml`` files. See the following sections for how to write them.

.. toctree::
   :maxdepth: 2
   :caption: Hammer Technology:

   Tech-class
   Tech-json
   Tech-defaults
