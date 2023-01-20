.. image:: logo_transparent.png
   :width: 600
   :alt: Logo design by @kenhoberkeley

|

Hammer is a physical design framework that wraps around vendor specific technologies and tools to provide a single API to create ASICs.
Hammer allows for reusability in ASIC design while still providing the designers leeway to make their own modifications.

Introduction to Hammer
===============================

Hammer (Highly Agile Masks Made Effortlessly from RTL) is a framework for building physical design generators for digital VLSI flows.
It is an evolving set of APIs that enable reuse in an effort to speed up VLSI flows, which have traditionally been entirely rebuilt for different projects, technologies, and tools.

Hammer is able to generate scripts and collateral for a growing range of CAD tools while remaining technology-agnostic using a well-defined set of common APIs.
Tool- and technology-specific concerns live inside plugins, implement APIs, and provide a set of working default configurations.

The vision of Hammer is to reduce the cycle time on VLSI designs, enabling rapid RTL design space exploration and allowing a designer to investigate the impact of various parameters like timing constraints and floorplans without needing to worry about low-level details.

For high-level details about Hammer's design principles and capabilities, please refer to our DAC 2022 paper entitled `Hammer: A Modular and Reusable Physical Design Flow Tool <https://dl.acm.org/doi/abs/10.1145/3489517.3530672>`_. We kindly request that this paper be cited in any publications where Hammer was used.

.. toctree::
   :maxdepth: 3
   :caption: Contents:
   :numbered:

   Hammer-Basics/index

   Technology/index
   
   CAD-Tools/index

   Hammer-Flow/index

   Hammer-Use/index

   Examples/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
