PLSI: Palmer's VLSI Scripts
---------

This repository contains my VLSI scripts.  These are designed to be highly
automated and portable to multiple technologies, vendors, and generators.  The
entire process is driven by a top-level Makefile.

# Using PLSI

The whole PLSI build process is driven by a single top-level Makefile.  To
build a PLSI-based project, you simply obtain the sources and run make.

````
$ git clone git://github.com/palmer-dabbelt/plsi.git
$ cd plsi
$ git submodule update --init --recursive
$ make
````

You can customize the build by using make variables, which can either be set in
"Makefile.project" or on the commandline.  The following variables can be set:

 * CORE_GENERATOR: The project that will be used to generate the core.  There's
   two currently supported: "rocket-chip" which generates a Rocket Chip based
   core, and "crossbar" which generates a single AXI crossbar (using Rocket
   Chip's crossbar implementation).

 * CORE_CONFIG: A configuration specific to the core being generated.  For
   Rocket Chip based projects this passes a CDE-based top-level parameter class
   by name to the build system (it's exactly the same as setting CONFIG in
   Rocket Chip's build system).

 * SOC_GENERATOR: The family of SOC that will be generated.  Right now there's
   two: "nop" doesn't do anything (it just spits the core back out), and
   "bar-testchip" generates a Berkeley-style test chip.

Source for the various addons can be found in src/addons.

# Bug Reports

To submit a bug report, run something like

````
$ make SOC_GENERATOR=bar-testchip bugreport |& tee buginfo.txt
````

and then submit the bug report to me so I can see what's going on.  Be sure to
your make variables correctly when submitting the report!
