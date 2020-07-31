.. _hooks:

OpenROAD and nangate45
=======================================

The `OpenROAD-flow <https://github.com/The-OpenROAD-Project/OpenROAD-flow>`__ is an open-source, technology-independent VLSI toolchain. As of this writing, it has the ability to run synthesis, place-and-route, and drc through various open-source tools. 

The OpenROAD-flow repository contains the nangate45 example pdk, which you might find useful for high-level architectural exploration.

Hammer has the ability to target the OpenROAD toolchain and it's nangate45 pdk. So you can now simply push a button in `Chipyard <https://github.com/ucb-bar/chipyard>`__ to go from your Chisel design to a somewhat reasonable gds at an example 45-nm node.

Instructions
---------------------------
In addition to following the chipyard and hammer setup instructions, you must also setup OpenROAD-flow before using it. The steps to run the default RocketConfig through OpenROAD's drc are:

1) install OpenROAD-flow (follow the repo's instructions) on your machine
2) ``cd /work/OpenROAD-flow && source setup_env.sh``
3) ``cd /work/chipyard/vlsi && make tech_name=nangate45 drc``

This assumes you already have chipyard's ``env.sh`` and hammer's ``sourceme.sh`` already sourced into your shell.
