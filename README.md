Highly Agile Masks Made Effortlessly from RTL 
=============================================

This is the master (unstable) development branch.

Documentation
=============
The main documentation is found at https://hammer-vlsi.readthedocs.io
Docs sources are available at `doc/` for offline reading.

Hammer currently requires Python 3.6+.

For a deeper dive into available options and environment configuration:

* [Core Hammer settings](src/hammer-vlsi/defaults.yml)
* [Documentation for hammer-vlsi](src/hammer-vlsi/README.md)
* [Hammer technology library schema](src/hammer-tech/schema.json)
* For CAD tool settings, please see the relevant `defaults.yml` for those plugins.

Hammer is an integral component of UC Berkeley Architecture Research's [Chipyard framework](https://github.com/ucb-bar/chipyard).
Useful documentation for how an example block is pushed through the VLSI flow with Hammer in the free ASAP7 PDK is at https://chipyard.readthedocs.io/en/latest/VLSI.

History
=======
The list of contributors can be found in the Git history of the project, or online at https://github.com/ucb-bar/hammer/graphs/contributors

The Hammer project builds upon the legacy of the [PLSI project by Palmer Dabbelt](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2017/EECS-2017-77.html), a previous project which aimed to build a portable VLSI flow. The Hammer project is grateful for the feedback and lessons learned which provided valuable insight that ultimately led to the design and software architecture of Hammer as it is now.
