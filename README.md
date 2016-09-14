PLSI: Palmer's VLSI Scripts
---------

This repository contains my VLSI scripts.  These are designed to be highly
automated and portable to multiple technologies, vendors, and generators.  The
entire process is driven by a top-level Makefile.

# Getting Started

The whole PLSI build process is driven by a single top-level Makefile.  To
build a PLSI-based project, you simply obtain the sources and run make.

````
$ git clone git://github.com/palmer-dabbelt/plsi.git
$ cd plsi
$ git submodule update --init --recursive
$ make
````

While the goal of PLSI is to provide a whole chip just by typing "make", since
it's not done yet that won't happen.  Note that in addition to the full-chip
targets, there short names defined for the various sorts of output users might
be interested in.  For example, to get top-level Verilog for the SOC step, run

````
make soc-verilog
````

# Using PLSI

This section is a more advanced introduction to PLSI: it covers using the PLSI
customization features to change the chip and flow, but not modifying the flow
in ways that aren't already supported.

## Customizing the Chip

You can customize the build by using make variables, which can either be set in
"Makefile.project", "Makefile.local", or on the commandline.  The following
variables can be set:

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

### Core Generators

PLSI is designed to have modular support for various "core generators", which
generate the parts of a SOC that aren't tapeout specific.  The canonical
example of this will probably always be Rocket Chip, as that's the one I care
about.  The following core generators are supported:

 * rocket-chip: The interesting one.  This just calls into Rocket Chip and
   generates whatever it does.

 * crossbar: An example of how to customize Rocket Chip for your own top.  This
   is a very intrusive example: it generates just a single AXI crossbar using
   Rocket Chip's implementation.  This isn't meant to be an interesting chip
   but instead an example of how to customize Rocket Chip without forking it.

Other core generators will almost certainly be added, but for now I'm focusing
on getting the flow to work with just Rocket Chip.  The core generator will be
passed two make-level variables from PLSI:

 * CORE_CONFIG: This gets passed as CONFIG to Rocket Chip.  Other core
   generators can do anything.

 * CORE_SIM_CONFIG: Allows users to control the test set that will be run.  For
   Rocket Chip, a setting of "smoke" will run only a few short tests.

### SOC Generators

Since Rocket Chip doesn't generate everything required to actually build a
chip, the next stage in the flow is the "SOC generator".  This generates all
the system-level things necessary to make a chip work, but not things that are
technology specific.  This includes:

 * Mapping the core's IO interfaces to physically realizable ones.  This could
   mean black-boxing some IO IP or generating pure-digital interfaces (like
   HTIF or JTAG).

 * Producing test harness shims to ensure the design is still testable.

The SOC generator is one of the things users will probably want to modify to
their liking in order to produce an interesting chip for them, but
modifications to the flow is outside the scope of this section.  The following
SOC generators are supported:

 * nop: This doesn't do anything, it's mostly there just for illustrative
   purposes.  Since it's the simplest one, it's a good basis for user-specific
   SOC generators.

 * bar-testchip: Generates a test chip like the one that the Berkeley
   Architecture Group builds.  This will have a slow, narrow, single-ended,
   digital-only interface for IO because it's the only IO interface we know how
   to build that's technology agnostic.

 * (TODO)bar-paper: Generates a SOC like the one the Berkeley Architecture
   Group uses for papers.  The most important feature is a timing-accurate
   top-level memory.

While I anticipate that many SOC generators will be written, most of them
probably aren't interesting for upstream.  The SOC generator will be passed a
single make-level variable from PLSI:

 * SOC_CONFIG: Allows users to configure the SOC in different ways.  FIXME:
   right now this does nothing, because the bar-testchip code is crap.

## Customizing the Flow

In addition to customizing the chip, there are variables that can be set to
control the tools used to build the chip.  These variables can also either be
set in "Makefile.project", "Makefile.local", or on the commandline.  The
following variables can be set:

 * SCHEDULER: The mechanism that will be used for scheduling jobs.  It's
   recommended users leave this as the default "auto" scheduler, which will
   try to pick the correct scheduler for the current machine by looking at what
   programs are installed.

 * CORE_SIMULATOR: Allows users to use different simulators for different
   stages of the flow.  CORE_SIMULATOR controls what simulates the output of
   CORE_GENERATOR.  In general, there's one of these for every stage (CORE,
   SOC, ...).

 * TECHNOLOGY: The technology that will be used to implement this design.
   Technologies are described by JSON files in src/technologies, a canonical
   example is the Synopsys educational technology library "saed32".

Source for the various addons can be found in src/addons.

### Running on a Cluser

As configured by default, PLSI will attempt to schedule jobs on a cluster if
the users system appears to have one.  Users can override this behavior by
setting SCHEDULER to something other than "auto", but it's not recommeneded --
whatever changes you have to make are probably just a bug in the auto scheduler
and should be fixed rather than worked around.  The following schedulers are
currently supported:

 * local: Runs jobs on the local machine, using make's jobserver.  This is a
   fallback scheduler and shouldn't be used for real.

 * travis_wait: PLSI is run under continuous integration on travis-ci.org, this
   scheduler improves the user experience there.  It shouldn't be used anywhere
   else.

 * slurm: Submits jobs to the default partition of a SLURM cluster by running
   "srun" on the local machine.  The cluster is queried for core counts and a
   resource allocation that matches the smallest node is requested (except for
   serial jobs, which request a single core).  This is designed to play with
   the CPU cons_res resource manager.

I know there's a bunch of other cluster systems, but I don't use them.  I'll
accept patches for them.

### Support for Simulators

Since simulators have various tradeoffs, PLSI has modular support for
simulators and can mix and match different simulators at different stages of
the flow.  There is currently support for the following simulators:

 * Verilator: This is the best open-source Verilog simulator I know of, and is
   the default simulator in PLSI.  Verilator does not have full Verilog
   support, so it probably won't simulate things like your foundry's
   technology-specific stuff.

 * Synopsys VCS: We're primairially a Synopsys shop internally.  Historically
   this has been the only simulator Rocket Chip has used, so it's the only one
   I'm familiar with.  It's recommended you use VCS to simulate anything that
   comes out of a Synopsys tool.

Support for additional simulators probably won't be added (as we don't use
them), but I'll accept patches.

### Technology Description Files

PLSI is designed to support multiple technologies.  Older PLSI versions allowed
users to write technology-specific Makefile fragments, but this was deemed to
be too difficult to use.  Instead of writing Makefile fragments, technologies
are now described using JSON files.  Examples of technology JSON files can be
found in src/technologies.  It's expected that the following keys are defined
in a technology JSON file:

 * "name": A human-readable name for the technology, used for reports and error
   messages.

 * "tarball name": The name of a tarball that contains the propritary
   technology files.  If your technology doesn't come as a single tarball (for
   example, it's been extracted by your system administrators) then don't set
   this key, set "base directory" instead.

 * "tarball homepage": A URL that describes how to obtain the technology
   tarball, since they won't be automatically downloadable.  If your technology
   doesn't support tarball downloads then don't set this key.

 * "milkway tech files": A list of tech files that will be used when running
   milkyway based tools.  If your technology doesn't support milkyway then
   don't set this variable.

 * "openaccess tech files": A list of tech files that will be used when running
   openaccess based tools.  If your technology doesn't support openaccess then
   don't set this variable.

# Bug Reports

To submit a bug report, run something like

````
$ make SOC_GENERATOR=bar-testchip bugreport |& tee buginfo.txt
````

and then submit the bug report to me so I can see what's going on.  Be sure to
your make variables correctly when submitting the report!
