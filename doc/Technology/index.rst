.. _technology:

Technology Setup and Use
========================================

These guides will walk you through how to set up a technology to be used in Hammer.

You may use the included `free ASAP7 PDK <https://github.com/ucb-bar/hammer/tree/master/src/hammer-vlsi/technology/asap7>`__ or the `open-source Sky130 PDK <https://github.com/ucb-bar/hammer/tree/master/src/hammer-vlsi/technology/sky130>`__ plugins as reference when building your own technology plugin.

Technologies should have their own folder along with a corresponding ".tech.json" file. For example, "asap7" would have a "asap7.tech.json" file inside of the "asap7" folder.

.. toctree::
   :maxdepth: 2
   :caption: Hammer Technology:

   Tech-json
   Tech-defaults
