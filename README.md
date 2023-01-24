![Logo design by @kenhoberkeley](https://github.com/ucb-bar/hammer/raw/master/doc/logo_transparent.png)

![Hammer PR CI](https://github.com/ucb-bar/hammer/actions/workflows/pr.yml/badge.svg?event=push) ![Hammer publish CI](https://github.com/ucb-bar/hammer/actions/workflows/publish.yml/badge.svg)

Highly Agile Masks Made Effortlessly from RTL (Hammer)
=============================================

This is the master (unstable) development branch.

Documentation
=============
The documentation is found at https://hammer-vlsi.readthedocs.io
Doc sources are available at `doc/` for offline reading.

Hammer currently requires Python 3.9+.

For a deeper dive into available options and environment configuration:

* [Core Hammer settings](hammer/config/defaults.yml)
* [Setup documentation](doc/Hammer-Basics/Hammer-Setup.md)
* [Hammer technology library schema](hammer/tech/__init__.py)
* For CAD tool settings, please see the relevant `defaults.yml` for those plugins.

Hammer is an integral component of UC Berkeley Architecture Research's [Chipyard framework](https://github.com/ucb-bar/chipyard).
Useful documentation for how an example block is pushed through the VLSI flow with Hammer in the free ASAP7 and Sky130 PDKs is at https://chipyard.readthedocs.io/en/latest/VLSI.

History
=======
The list of contributors can be found in the Git history of the project, or online at https://github.com/ucb-bar/hammer/graphs/contributors

The Hammer project builds upon the legacy of the PLSI project by Palmer Dabbelt, a previous project which aimed to build a portable VLSI flow. The Hammer project is grateful for the feedback and lessons learned which provided valuable insight that ultimately led to the design and software architecture of Hammer as it is now.

Below is the list of Hammer publications in reverse chronological order:
- [Hammer: a modular and reusable physical design flow tool (DAC 2022)](https://dl.acm.org/doi/abs/10.1145/3489517.3530672)
- [A Methodology for Reusable Physical Design (ISQED 2020)](https://ieeexplore.ieee.org/document/9136999)
- [PLSI: A Portable VLSI Flow (Master's Thesis, 2017)](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2017/EECS-2017-77.html)
