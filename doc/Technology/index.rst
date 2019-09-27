Technology Setup and Use
========================================

These guides will walk you through how to set up a technology to be used in Hammer.

Setting up a technology to use with Hammer consists of three parts: a ``tech.json`` that points to required files in the PDK and encodes stackup information, a ``defaults.yml`` that sets some technology defaults, and a few Hammer input keys to include in your config to specify that Hammer should use that technology. There is an example of how this is done in Hammer already for the free PDK `ASAP7 <https://github.com/ucb-bar/hammer/tree/master/src/hammer-vlsi/technology/asap7>`__

.. toctree::
   :maxdepth: 2
   :caption: Hammer Technology:

   Tech-json
   Tech-defaults
