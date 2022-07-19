.. _tech-defaults:

Hammer Tech defaults.yml
===============================

The ``defaults.yml`` for a technology specifies some technology-specific Hammer IR that should be left as default unless you desire to override them. Some of the them work directly with the keys in the ``tech.json``.

Most of the keys in the ``defaults.yml`` are a part of the ``vlsi`` and ``technology`` namespaces. An example of the setup of the ``defaults.yml`` is located in ``hammer/src/hammer-vlsi/technology/asap7/defaults.yml`` and certain important keys should be common to most technology plugins:

* ``vlsi.core.node`` defines the node that the place-and-route tool expects. It affects what kind of licenses are needed.
* ``vlsi.inputs`` should at least have the nominal supplies and a typical pair of characterized setup & hold corners.
* ``vlsi.technology`` needs to specify a ``placement_site`` as defined in the technology LEF, a ``bump_block_cut_layer`` to set blockages under bumps, and optional ``tap_cell_interval`` and ``tap_cell_offset`` for placing well taps.
* ``technology.core`` needs to specify the stackup to use, which layer the standard cell power rails are on, and a reference cell to draw the lowest layer power rails over.

Tool environment variables (commonly needed for DRC/LVS decks) and other necessary default options should be set in this file. As always, they can be overriden by other snippets of Hammer IR.

The data types for all keys in ``defaults.yml`` can be found in ``defaults_types.yml``. When adding or overriding to ``defaults.yml``, make sure that said data types are updated accordingly to prevent problems with the type checker.
