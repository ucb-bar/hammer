Hammer Tech defaults.yml
===============================

The ``defaults.yml`` for a technology specifies some key parameters that are technology specific. Some of the them work directly with the keys in the ``tech.json``.

Most of the keys in the ``defaults.yml`` are a part of the ``vlsi`` namespace. This includes specifying which node the technology is and the nominal supply voltage. The technology corners are also specified here in the ``mmmc_corners`` key. 

An example of the setup of the ``defaults.yml`` is located in ``hammer/src/hammer-vlsi/technology/asap7/defaults.yml``.

