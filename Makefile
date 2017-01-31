# Copyright 2016-2017 Palmer Dabbelt <palmer@dabbelt.com>

# The default target, which runs everything and tells you if it passed or not.
all: report

###############################################################################
# Default Variables
###############################################################################

# Don't change these variables here, instead override them with a
# "Makefile.project" in the directory above this one, or on the command line
# (if you want to do experiments).
-include Makefile.local
-include ../Makefile.project

# The "core generator" generates top-level RTL, but doesn't include anything
# that's technology specific
CORE_GENERATOR ?= rocketchip

# The "soc generator" is used to add everything to a soc that isn't part of
# the core generator (maybe because it's a NDA or something).  This default
# soc generator doesn't actually do anything at all.
SOC_GENERATOR ?= nop

# The technology that will be used to implement this design.
TECHNOLOGY ?= tsmc180osu

# Selects the CAD tools that will be run.  For now, I'm defaulting to Synopsys
# as they're the only ones I've actually implemeted wrappers for.
SYNTHESIS_TOOL ?= dc
PAR_TOOL ?= icc

# The configuration to run when running various steps of the process
CORE_CONFIG ?= DefaultConfig
CORE_SIM_CONFIG ?= default
SOC_CONFIG ?= default
MAP_CONFIG ?= default
SYN_CONFIG ?= default
PAR_CONFIG ?= default

# Defines the simulator used to run simulation at different levels
SIMULATOR ?= verilator
CORE_SIMULATOR ?= $(SIMULATOR)
SOC_SIMULATOR ?= $(SIMULATOR)
MAP_SIMULATOR ?= $(SIMULATOR)
SYN_SIMULATOR ?= $(SIMULATOR)
PAR_SIMULATOR ?= $(SIMULATOR)

# Defines the formal verification tool to use at different levels.
FORMAL_TOOL ?= none
SYN_FORMAL_TOOL ?= $(FORMAL_TOOL)

# This allows post-synthesis power-related signoff, which while not being
# exactly accurate can be used to get a general idea if a design is viable.
POWER_SIGNOFF_TOOL ?= none
SYN_POWER_SIGNOFF_TOOL ?= $(POWER_SIGNOFF_TOOL)

# The scheduler to use when running large jobs.  Changing this doesn't have any
# effect on the generated files, just the manner in which they are generated.
SCHEDULER ?= auto

# A cache directory for things that are, for some reason, difficult to create
# and never change.  This is suitable for installing as a read-only shared
# directory as long as someone writes to it first.
PLSI_CACHE_DIR ?= obj/cache

# A directory that contains the tools that PLSI builds, in case you want to
# share them.
OBJ_TOOLS_DIR ?= obj/tools

##############################################################################
# Internal Variables
##############################################################################

# These variables aren't meant to be overridden by users -- you probably
# shouldn't be changing them at all.

# Versions of externally developed programs to download
TCLAP_VERSION = 1.2.1
TCL_LIBRARY_VERSION = 8.6
TCL_VERSION = 8.6.6
GCC_VERSION = 4.9.3
PYTHON3_VERSION = 3.4.5

# OBJ_*_DIR are the directories in which outputs end up
OBJ_TOOLS_SRC_DIR = $(OBJ_TOOLS_DIR)/src
OBJ_TOOLS_BIN_DIR = $(OBJ_TOOLS_DIR)/install
OBJ_CORE_DIR = obj/core-$(CORE_GENERATOR)-$(CORE_CONFIG)
OBJ_SOC_DIR = obj/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)
OBJ_TECH_DIR = obj/technology/$(TECHNOLOGY)
OBJ_MAP_DIR = obj/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)
OBJ_SYN_DIR = obj/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)
OBJ_PAR_DIR = obj/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)

# CHECK_* directories are where the output of tests go
CHECK_CORE_DIR = check/sim/core-$(CORE_GENERATOR)-$(CORE_CONFIG)
CHECK_SOC_DIR = check/sim/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)
CHECK_MAP_DIR = check/sim/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)
CHECK_SYN_DIR = check/sim/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)
CHECK_PAR_DIR = check/sim/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)

# TRACE_* directories are where VPDs go
TRACE_CORE_DIR = trace/core-$(CORE_GENERATOR)-$(CORE_CONFIG)
TRACE_SOC_DIR = trace/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)
TRACE_MAP_DIR = trace/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)
TRACE_SYN_DIR = trace/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)
TRACE_PAR_DIR = trace/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)

# SIGNOFF_* directories are where signoff-related checks go
SIGNOFF_SYN_FORMAL_DIR = check/formal/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)
SIGNOFF_SYN_POWER_DIR = check/power/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(MAP_CONFIG)-$(SYN_CONFIG)

CMD_PTEST = $(OBJ_TOOLS_BIN_DIR)/pconfigure/bin/ptest
CMD_PCONFIGURE = $(OBJ_TOOLS_BIN_DIR)/pconfigure/bin/pconfigure
CMD_PPKGCONFIG = $(OBJ_TOOLS_BIN_DIR)/pconfigure/bin/ppkg-config
CMD_PHC = $(OBJ_TOOLS_BIN_DIR)/pconfigure/bin/phc
CMD_PCAD_INFER_DECOUPLED = $(OBJ_TOOLS_BIN_DIR)/pcad/bin/pcad-pipe-infer_decoupled
CMD_PCAD_MACRO_COMPILER = $(OBJ_TOOLS_BIN_DIR)/pcad/bin/pcad-pipe-macro_compiler
CMD_PCAD_LIST_MACROS = $(OBJ_TOOLS_BIN_DIR)/pcad/bin/pcad-pipe-list_macros
CMD_SBT = $(OBJ_TOOLS_BIN_DIR)/sbt/sbt
CMD_GCC = $(OBJ_TOOLS_BIN_DIR)/gcc-$(GCC_VERSION)/bin/gcc
CMD_GXX = $(OBJ_TOOLS_BIN_DIR)/gcc-$(GCC_VERSION)/bin/g++
CMD_PSON2JSON = $(OBJ_TOOLS_BIN_DIR)/pson/bin/pson2json
CMD_FIRRTL_GENERATE_TOP = $(OBJ_TOOLS_BIN_DIR)/pfpmp/bin/GenerateTop
CMD_FIRRTL_GENERATE_HARNESS = $(OBJ_TOOLS_BIN_DIR)/pfpmp/bin/GenerateHarness
CMD_PYTHON3 = $(OBJ_TOOLS_BIN_DIR)/python3-$(PYTHON3_VERSION)/bin/python3

PKG_CONFIG_PATH=$(abspath $(OBJ_TOOLS_BIN_DIR)/tclap-$(TCLAP_VERSION)/lib/pkgconfig):$(abspath $(OBJ_TOOLS_BIN_DIR)/pconfigure/lib/pkgconfig):$(abspath $(OBJ_TOOLS_BIN_DIR)/pson/lib/pkgconfig)
export PKG_CONFIG_PATH

##############################################################################
# Addon Loading
##############################################################################

# This section loads the various PLSI addons.  You shouldn't be screwing with
# this, but if you're trying to add a new addon then you might want to look
# here to see what variables it's expected to set.

# Locates the various addons that will be used to setup 
SCHEDULER_ADDON = $(wildcard src/addons/scheduler/$(SCHEDULER)/ $(ADDONS_DIR)/scheduler/$(SCHEDULER)/)
ifneq ($(words $(SCHEDULER_ADDON)),1)
$(error Unable to resolve SCHEDULER=$(SCHEDULER): found "$(SCHEDULER_ADDON)")
endif

CORE_GENERATOR_ADDON = $(wildcard src/addons/core-generator/$(CORE_GENERATOR)/ $(ADDONS_DIR)/core-generator/$(CORE_GENERATOR)/)
ifneq ($(words $(CORE_GENERATOR_ADDON)),1)
$(error Unable to resolve CORE_GENERATOR=$(CORE_GENERATOR): found "$(CORE_GENERATOR_ADDON)")
endif

CORE_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(CORE_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(CORE_SIMULATOR)/)
ifneq ($(words $(CORE_SIMULATOR_ADDON)),1)
$(error Unable to resolve CORE_SIMULATOR=$(CORE_SIMULATOR): found "$(CORE_SIMULATOR_ADDON)")
endif

SOC_GENERATOR_ADDON = $(wildcard src/addons/soc-generator/$(SOC_GENERATOR)/ $(ADDONS_DIR)/soc-generator/$(SOC_GENERATOR)/)
ifneq ($(words $(SOC_GENERATOR_ADDON)),1)
$(error Unable to resolve SOC_GENERATOR=$(SOC_GENERATOR): found "$(SOC_GENERATOR_ADDON)")
endif

SOC_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(SOC_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(SOC_SIMULATOR)/)
ifneq ($(words $(SOC_SIMULATOR_ADDON)),1)
$(error Unable to resolve SOC_SIMULATOR=$(SOC_SIMULATOR): found "$(SOC_SIMULATOR_ADDON)")
endif

MAP_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(MAP_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(MAP_SIMULATOR)/)
ifneq ($(words $(MAP_SIMULATOR_ADDON)),1)
$(error Unable to resolve MAP_SIMULATOR=$(MAP_SIMULATOR): found "$(MAP_SIMULATOR_ADDON)")
endif

SYNTHESIS_TOOL_ADDON = $(wildcard src/addons/synthesis/$(SYNTHESIS_TOOL)/ $(ADDONS_DIR)/synthesis/$(SYNTHESIS_TOOL)/)
ifneq ($(words $(SYNTHESIS_TOOL_ADDON)),1)
$(error Unable to resolve SYNTHESIS_TOOL=$(SYNTHESIS_TOOL): found "$(SYNTHESIS_TOOL_ADDON)")
endif

SYN_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(SYN_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(SYN_SIMULATOR)/)
ifneq ($(words $(SYN_SIMULATOR_ADDON)),1)
$(error Unable to resolve SYN_SIMULATOR=$(SYN_SIMULATOR): found "$(SYN_SIMULATOR_ADDON)")
endif

SYN_FORMAL_ADDON = $(wildcard src/addons/formal/$(SYN_FORMAL_TOOL)/ $(ADDONS_DIR)/formal/$(SYN_FORMAL_TOOLS))
ifneq ($(words $(SYN_FORMAL_ADDON)),1)
$(error Unable to resolve SYN_FORMAL_TOOL=$(SYN_FORMAL_TOOL): found "$(SYN_FORMAL_ADDON)")
endif

PAR_TOOL_ADDON = $(wildcard src/addons/par/$(PAR_TOOL)/ $(ADDONS_DIR)/par/$(PAR_TOOL)/)
ifneq ($(words $(PAR_TOOL_ADDON)),1)
$(error Unable to resolve PAR_TOOL=$(PAR_TOOL): found "$(PAR_TOOL_ADDON)")
endif

PAR_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(PAR_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(PAR_SIMULATOR)/)
ifneq ($(words $(PAR_SIMULATOR_ADDON)),1)
$(error Unable to resolve PAR_SIMULATOR=$(PAR_SIMULATOR): found "$(PAR_SIMULATOR_ADDON)")
endif

SYN_POWER_SIGNOFF_ADDON = $(wildcard src/addons/signoff-power/$(SYN_POWER_SIGNOFF_TOOL)/ $(ADDONS_DIR)/signoff-power/$(SYN_POWER_SIGNOFF_TOOLS))
ifneq ($(words $(SYN_POWER_SIGNOFF_ADDON)),1)
$(error Unable to resolve SYN_POWER_SIGNOFF_TOOL=$(SYN_POWER_SIGNOFF_TOOL): found "$(SYN_FORMAL_ADDON)")
endif

# Check to ensure all the configurations actually exist.
SYN_CONFIG_FILE=src/configs/$(TECHNOLOGY)-$(SYN_CONFIG).syn_config.json
ifeq ($(wildcard $(SYN_CONFIG_FILE)),)
$(error Unable to find synthesis configuration $(SYN_CONFIG), looked in $(SYN_CONFIG_FILE))
endif

PAR_CONFIG_FILE=src/configs/$(TECHNOLOGY)-$(PAR_CONFIG).par_config.json
ifeq ($(wildcard $(PAR_CONFIG_FILE)),)
$(error Unable to find synthesis configuration $(PAR_CONFIG), looked in $(PAR_CONFIG_FILE))
endif

# In order to prevent EEs from seeing Makefiles, the technology description is
# a JSON file.  This simply checks to see that the file exists before
# continuing, in order to ensure there's no trickier errors.
TECHNOLOGY_JSON = $(wildcard src/technologies/$(TECHNOLOGY).tech.json)
ifeq ($(TECHNOLOGY_JSON),)
$(error "Unable to find technology $(TECHNOLOGY), expected a cooresponding .tech.json file")
endif

OBJ_TECHNOLOGY_MACRO_LIBRARY = $(OBJ_TECH_DIR)/plsi-generated/all.macro_library.json

# Actually loads the various addons, this is staged so we load "vars" first
# (which set variables) and "rules" second, which set the make rules (which can
# depend on those variables).
include $(SCHEDULER_ADDON)/vars.mk

ifeq ($(SCHEDULER_CMD),)
# A command that schedules large jobs.  This should respect the jobserver if
# it's run locally on this machine, but it's expected that some of this stuff
# will run on clusters and therefor won't respect the jobserver.
$(error SCHEDULER needs to set SCHEDULER_CMD)
endif

include $(CORE_GENERATOR_ADDON)/vars.mk
include $(CORE_SIMULATOR_ADDON)/core-vars.mk
include $(CORE_GENERATOR_ADDON)/rules.mk
include $(CORE_SIMULATOR_ADDON)/core-rules.mk

ifeq ($(CORE_TOP),)
# The name of the top-level RTL module that comes out of the core generator.
$(error CORE_GENERATOR needs to set CORE_TOP)
endif

ifeq ($(OBJ_CORE_SIM_FILES),)
# The extra files that are needed to simulate the core, but those that won't be
# replaced by the eventual macro generation steps.  These won't be touched by
# any tools.
$(error CORE_GENERATOR needs to set OBJ_CORE_SIM_FILES)
endif

ifeq ($(OBJ_CORE_SIM_MACRO_FILES),)
# The extra files that are necessary to simulate the core, but will be replaced
# by some sort of technology-specific macro generation that the CAD tools won't
# automatically map to -- for example SRAMs.  These will be replaced by other
# things in various stages of simulation.
$(error CORE_GENERATOR needs to set OBJ_CORE_SIM_MACRO_FILES)
endif

ifeq ($(OBJ_CORE_MACROS),)
# This is a JSON description of the macros that a core generator can request
# from PLSI.  Various other PLSI tools will consume these macro descriptions in
# order to insert them into other parts of the flow (for example, SRAM macros
# will be used in synthesis, floorplanning, and P&R).
$(error CORE_GENERATOR needs to set OBJ_CORE_MACROS)
endif

ifeq ($(OBJ_CORE_RTL_V)$(OBJ_CORE_RTL_VHD),)
# The name of the top-level RTL Verilog output by the core.
$(error CORE_GENERATOR needs to set OBJ_CORE_RTL_V or OBJ_CORE_RTL_VHD)
endif

include $(SOC_GENERATOR_ADDON)/vars.mk
include $(SOC_SIMULATOR_ADDON)/soc-vars.mk

ifeq ($(OBJ_SOC_RTL_V)$(OBJ_SOC_RTL_VHD),)
# The name of the top-level RTL Verilog output by the SOC generator.
$(error SOC_GENERATOR needs to set OBJ_SOC_RTL_V or OBJ_SOC_RTL_VHD)
endif

ifeq ($(OBJ_SOC_SIM_FILES),)
# This is just like OBJ_CORE_SIM_FILES, but if the soc needs something extra it
# can be stuck in here.
$(error SOC_GENERATOR needs to set OBJ_SOC_SIM_FILES)
endif

ifeq ($(OBJ_SOC_SIM_MACRO_FILES),)
# This is just like OBJ_SOC_SIM_MACRO_FILES, but if the soc needs something
# extra it can be stuck in here.
$(error SOC_GENERATOR needs to set OBJ_SOC_SIM_MACRO_FILES)
endif

ifeq ($(OBJ_SOC_MACROS),)
# Like OBJ_CORE_MACROS, but for the whole SOC
$(error SOC_GENERATOR needs to set OBJ_SOC_MACROS)
endif

# This selects the technology to implement the design with.
-include $(OBJ_TECH_DIR)/makefrags/vars.mk

ifneq ($(wildcard $(OBJ_TECH_DIR)/makefrags/vars.mk),)
ifeq ($(TECHNOLOGY_CCS_LIBERTY_FILES)$(TECHNOLOGY_NLDM_LIBERTY_FILES),)
$(error TECHNOLOGY needs to set TECHNOLOGY_CCS_LIBERTY_FILES or TECHNOLOGY_NLDM_LIBERTY_FILES)
endif

ifeq ($(TECHNOLOGY_CCS_LIBRARY_FILES)$(TECHNOLOGY_NLDM_LIBRARY_FILES),)
$(error TECHNOLOGY needs to set TECHNOLOGY_CCS_LIBRARY_FILES or TECHNOLOGY_NLDM_LIBRARY_FILES)
endif
endif

# The map step implements technology-specific macros (SRAMs, pads, clock stuff)
# in a manner that's actually technology-specific (as opposed to using the
# generic PLSI versions).  This results in some verilog for simulation, but it
# may result in some additional verilog for synthesis (building large SRAMs out
# of smaller ones, for example).
MAP_TOP = $(SOC_TOP)
MAP_SIM_TOP = $(CORE_SIM_TOP)

# There's always a mapped Verilog file since there's macros in it and I'm only
# going to bother generating macros as Verilog.
OBJ_MAP_RTL_V = $(OBJ_SOC_RTL_V) $(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.v
OBJ_MAP_RTL_VHD = $(OBJ_SOC_RTL_VHD)

OBJ_MAP_SYN_FILES =
OBJ_MAP_SIM_FILES = $(OBJ_SOC_SIM_FILES)
OBJ_MAP_SIM_MACRO_FILES = $(TECHNOLOGY_VERILOG_FILES)
OBJ_MAP_MACROS = $(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros.json

# Macro compilers need to know the actual list of required macros, as it's
# unreasonable to expect that the entire output of something like a memory
# compiler should generate every possible output before running synthesis.
ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.mk
endif

# This has to come after the macro vars makefrags, since it uses them to build
# the simulator.
include $(MAP_SIMULATOR_ADDON)/map-vars.mk

# The synthesis step converts RTL to a netlist.  This only touches the
# synthesizable Verilog that comes out of the mapping step, but additionally
# requires a whole bunch of files so it knows what to do with the macros.
include $(SYNTHESIS_TOOL_ADDON)/vars.mk
include $(SYN_SIMULATOR_ADDON)/syn-vars.mk

ifeq ($(OBJ_SYN_MAPPED_V),)
$(error SYNTHESIS_TOOL needs to set OBJ_SYN_MAPPED_V)
endif

ifeq ($(SYN_TOP),)
$(error SYNTHESIS_TOOL needs to set SYN_TOP)
endif

ifeq ($(SYN_SIM_TOP),)
$(error SYNTHESIS_TOOLS needs to set SYN_SIM_TOP)
endif

# A formal verification tool for post-synthesis.
include $(SYN_FORMAL_ADDON)/syn-vars.mk

# The place and route step (par) places all the elements of a netlist and then
# routes the wires between them.  This can only touch the output of the
# synthesis step, but additionally requires all the synthesis macro description
# files and some extra floorplanning information.
include $(PAR_TOOL_ADDON)/vars.mk
include $(PAR_SIMULATOR_ADDON)/par-vars.mk

ifeq ($(OBJ_PAR_ROUTED_V),)
$(error PAR_TOOL needs to set OBJ_PAR_ROUTED_V)
endif

ifeq ($(PAR_TOP),)
$(error PAR_TOOL needs to set PAR_TOP)
endif

ifeq ($(PAR_SIM_TOP),)
$(error PAR_TOOL needs to set PAR_SIM_TOP)
endif

# Various signoff tools
include $(SYN_POWER_SIGNOFF_ADDON)/syn-vars.mk

# All the rules get sourced last.  We don't allow any variables to be set here,
# so the ordering isn't important.
include $(SOC_GENERATOR_ADDON)/rules.mk
include $(SOC_SIMULATOR_ADDON)/soc-rules.mk
-include $(OBJ_TECH_DIR)/makefrags/rules.mk
include $(MAP_SIMULATOR_ADDON)/map-rules.mk
include $(SYNTHESIS_TOOL_ADDON)/rules.mk
include $(SYN_SIMULATOR_ADDON)/syn-rules.mk
include $(SYN_FORMAL_ADDON)/syn-rules.mk
include $(PAR_TOOL_ADDON)/rules.mk
include $(PAR_SIMULATOR_ADDON)/par-rules.mk
include $(SYN_POWER_SIGNOFF_ADDON)/syn-rules.mk

##############################################################################
# User Targets
##############################################################################

# The targets in here are short names for some of the internal targets below.
# These are probably the commands you want to manually run.

# I'm not sure exactly what is going on here, but it looks like the makefrag
# generation breaks parallel builds.  This target doesn't do anything but
# generate the various makefrags and doesn't run any other commands.
.PHONY: makefrags
makefrags::

# Runs all the test cases.  Note that this _always_ passes, you need to run
# "make report" to see if the tests passed or not.
.PHONY: check
check: $(patsubst %,check-%,core soc map syn par)
ifneq ($(SYN_POWER_SIGNOFF_TOOL),none)
check: signoff-syn-power
endif

# A virtual target that reports on the status of the test cases, in addition to
# running them (if necessary).
.PHONY: report
report: $(CMD_PTEST) check
	@+$(CMD_PTEST)

# These various smaller test groups are all defined by the core generator!
.PHONY: check-core
check-core:

.PHONY: check-soc
check-soc:

.PHONY: check-map
check-map:

.PHONY: check-syn
check-syn:

.PHONY: check-par
check-par:

.PHONY: signoff-syn-power
signoff-syn-power:

# The various RTL targets
.PHONY: core-verilog
core-verilog: bin/core-$(CORE_GENERATOR)-$(CORE_CONFIG)/$(CORE_TOP).v
	$(info $@ availiable at $<)

.PHONY: soc-verilog
soc-verilog: bin/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP).v
	$(info $@ availiable at $<)

.PHONY: map-verilog
map-verilog: bin/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)/$(MAP_TOP).v
	$(info $@ availiable at $<)

.PHONY: syn-verilog
syn-verilog: bin/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP).v
	$(info $@ availiable at $<)

.PHONY: par-verilog
par-verilog: bin/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)/$(PAR_TOP).v
	$(info $@ availiable at $<)

# The various simulators
.PHONY: core-simulator
core-simulator: bin/core-$(CORE_GENERATOR)-$(CORE_CONFIG)/$(CORE_TOP)-simulator
.PHONY: soc-simulator
soc-simulator: bin/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP)-simulator
.PHONY: map-simulator
map-simulator: bin/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)/$(MAP_TOP)-simulator
.PHONY: syn-simulator
syn-simulator: bin/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP)-simulator
.PHONY: par-simulator
par-simulator: bin/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)/$(PAR_TOP)-simulator

# This just cleans everything
.PHONY: clean
clean::
	rm -rf $(OBJ_TOOLS_BIN_DIR) $(OBJ_TOOLS_SRC_DIR)
	rm -rf $(OBJ_CORE_DIR) $(CHECK_CORE_DIR)
	rm -rf $(OBJ_SOC_DIR) $(CHECK_SOC_DIR)
	rm -rf $(OBJ_SYN_DIR) $(CHECK_SYN_DIR)
	rm -rf $(OBJ_PAR_DIR) $(CHECK_PAR_DIR)

.PHONY: distclean
distclean: clean
	rm -rf bin/ obj/ check/

# Information for bug reporting
.PHONY: bugreport
bugreport::
	@echo "SCHEDULER_ADDON=$(SCHEDULER_ADDON)"
	@echo "CORE_GENERATOR_ADDON=$(CORE_GENERATOR_ADDON)"
	@echo "CORE_SIMULATOR_ADDON=$(CORE_SIMULATOR_ADDON)"
	@echo "SOC_GENERATOR_ADDON=$(SOC_GENERATOR_ADDON)"
	@echo "SOC_SIMULATOR_ADDON=$(SOC_SIMULATOR_ADDON)"
	@echo "SYNTHESIS_TOOL_ADDON=$(SYNTHESIS_TOOL_ADDON)"
	@echo "PAR_TOOL_ADDON=$(PAR_TOOL_ADDON)"
	@echo "TECHNOLOGY=$(TECHNOLOGY)"
	uname -a
	@echo "PKG_CONFIG_PATH=$$PKG_CONFIG_PATH"
	pkg-config tclap --cflags --libs
	@find $(PLSI_CACHE_DIR) -type f 2>/dev/null | xargs sha1sum /dev/null

##############################################################################
# Internal Tools Targets
##############################################################################

# These targets are internal to PLSI, you probably shouldn't even be building
# them directly from the command-line.  Use the nicely named targets above,
# they're easier to remember.

# Pretty much everything needs a newer GCC than will be availiable on any CAD
# tools machines.
$(CMD_GCC) $(CMD_GXX): $(OBJ_TOOLS_BIN_DIR)/gcc-$(GCC_VERSION)/stamp
	touch $@

$(OBJ_TOOLS_BIN_DIR)/gcc-$(GCC_VERSION)/stamp: $(OBJ_TOOLS_SRC_DIR)/gcc-$(GCC_VERSION)/build/Makefile
	+$(SCHEDULER_CMD) -- src/tools/build-gcc --srcdir $(dir $<) --bindir $(dir $@) --logfile $(dir $<)/build.log
	@date > $@

$(OBJ_TOOLS_SRC_DIR)/gcc-$(GCC_VERSION)/build/Makefile: $(OBJ_TOOLS_SRC_DIR)/gcc-$(GCC_VERSION)/configure
	@mkdir -p $(dir $@)
	cd $(dir $@); ../configure --prefix=$(abspath $(OBJ_TOOLS_BIN_DIR)/gcc-$(GCC_VERSION)) --enable-languages=c,c++ --disable-multilib --disable-checking

$(OBJ_TOOLS_SRC_DIR)/gcc-$(GCC_VERSION)/configure: $(PLSI_CACHE_DIR)/distfiles/gcc-$(GCC_VERSION).tar.gz
	@rm -rf $(dir $@)
	@mkdir -p $(dir $@)
	tar -xpf $< --strip-components=1 -C $(dir $@)
	touch $@

$(PLSI_CACHE_DIR)/distfiles/gcc-$(GCC_VERSION).tar.gz:
	@mkdir -p $(dir $@)
	wget https://ftp.gnu.org/gnu/gcc/gcc-$(GCC_VERSION)/gcc-$(GCC_VERSION).tar.gz -O $@

# Builds pconfigure and its related tools
$(CMD_PCONFIGURE) $(CMD_PTEST) $(CMD_PPKGCONFIG) $(CMD_PHC): \
		$(OBJ_TOOLS_BIN_DIR)/pconfigure/stamp
	touch $@

$(OBJ_TOOLS_BIN_DIR)/pconfigure/stamp: $(OBJ_TOOLS_SRC_DIR)/pconfigure/Makefile
	$(MAKE) -C $(OBJ_TOOLS_SRC_DIR)/pconfigure CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) install
	@date > $@

$(OBJ_TOOLS_SRC_DIR)/pconfigure/Makefile: $(OBJ_TOOLS_SRC_DIR)/pconfigure/stamp $(CMD_GXX)
	@mkdir -p $(dir $@)
	mkdir -p $(OBJ_TOOLS_SRC_DIR)/pconfigure/Configfiles
	rm -f $(OBJ_TOOLS_SRC_DIR)/pconfigure/Configfiles/local
	echo 'PREFIX = $(abspath $(OBJ_TOOLS_BIN_DIR))/pconfigure' >> $(OBJ_TOOLS_SRC_DIR)/pconfigure/Configfiles/local
	echo 'LANGUAGES += c++' >> $(OBJ_TOOLS_SRC_DIR)/pconfigure/Configfiles/local
	echo 'LINKOPTS += -L,$(abspath $(OBJ_TOOLS_BIN_DIR))/gcc-$(GCC_VERSION)/lib64' >> $(OBJ_TOOLS_SRC_DIR)/pconfigure/Configfiles/local
	echo 'LINKOPTS += -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR))/gcc-$(GCC_VERSION)/lib64' >> $(OBJ_TOOLS_SRC_DIR)/pconfigure/Configfiles/local
	+cd $(OBJ_TOOLS_SRC_DIR)/pconfigure; $(SCHEDULER_CMD) --max-threads=1 -- ./bootstrap.sh --cc $(abspath $(CMD_GCC)) --cxx $(abspath $(CMD_GXX)) --cxxflags "-L,$(abspath $(OBJ_TOOLS_BIN_DIR))/gcc-$(GCC_VERSION)/lib64 -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR))/gcc-$(GCC_VERSION)/lib64"
	cd $(OBJ_TOOLS_SRC_DIR)/pconfigure; PATH="$(OBJ_TOOLS_SRC_DIR)/pconfigure/bin:$(PATH)" ./bin/pconfigure --verbose --ppkg-config $(abspath $(OBJ_TOOLS_SRC_DIR)/pconfigure/bin/ppkg-config) --phc $(abspath $(OBJ_TOOLS_SRC_DIR)/pconfigure/bin/phc)
	+PATH="$(abspath $(OBJ_TOOLS_SRC_DIR)/pconfigure/bin/):$$PATH" $(SCHEDULER_CMD) --make -- $(MAKE) -C $(OBJ_TOOLS_SRC_DIR)/pconfigure -B CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX))

$(OBJ_TOOLS_SRC_DIR)/pconfigure/stamp: $(shell find src/tools/pconfigure -type f)
	mkdir -p $(dir $@)
	rsync -a --delete src/tools/pconfigure/ $(OBJ_TOOLS_SRC_DIR)/pconfigure
	touch $@

# Most of the CAD tools have some sort of TCL interface, and the open source
# ones require a TCL installation
$(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/stamp: $(OBJ_TOOLS_SRC_DIR)/tcl-$(TCL_VERSION)/unix/Makefile
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(dir $<) install
	@date > $@

$(OBJ_TOOLS_SRC_DIR)/tcl-$(TCL_VERSION)/unix/Makefile: $(OBJ_TOOLS_SRC_DIR)/tcl-$(TCL_VERSION)/stamp $(CMD_GCC)
	cd $(dir $@); ./configure --prefix=$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION))

$(OBJ_TOOLS_SRC_DIR)/tcl-$(TCL_VERSION)/stamp: $(PLSI_CACHE_DIR)/distfiles/tcl-$(TCL_VERSION).tar.gz
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	tar -xzpf $< --strip-components=1 -C $(dir $@)
	touch $@

$(PLSI_CACHE_DIR)/distfiles/tcl-$(TCL_VERSION).tar.gz:
	mkdir -p $(dir $@)
	wget http://prdownloads.sourceforge.net/tcl/tcl$(TCL_VERSION)-src.tar.gz -O $@

# TCLAP is a C++ command-line argument parser that's used by PCAD
$(OBJ_TOOLS_BIN_DIR)/tclap-$(TCLAP_VERSION)/stamp: $(OBJ_TOOLS_SRC_DIR)/tclap-$(TCLAP_VERSION)/Makefile
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(dir $<) install
	@date > $@

$(OBJ_TOOLS_SRC_DIR)/tclap-$(TCLAP_VERSION)/Makefile: $(OBJ_TOOLS_SRC_DIR)/tclap-$(TCLAP_VERSION)/configure $(CMD_GXX)
	cd $(OBJ_TOOLS_SRC_DIR)/tclap-$(TCLAP_VERSION); ./configure --prefix=$(abspath $(OBJ_TOOLS_BIN_DIR)/tclap-$(TCLAP_VERSION))

$(OBJ_TOOLS_SRC_DIR)/tclap-$(TCLAP_VERSION)/configure: $(PLSI_CACHE_DIR)/distfiles/tclap-$(TCLAP_VERSION).tar.gz
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	tar -xvzpf $< --strip-components=1 -C $(dir $@)
	touch $@

$(PLSI_CACHE_DIR)/distfiles/tclap-$(TCLAP_VERSION).tar.gz:
	mkdir -p $(dir $@)
	wget 'http://downloads.sourceforge.net/project/tclap/tclap-$(TCLAP_VERSION).tar.gz?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Ftclap%2Ffiles%2F&ts=1468971231&use_mirror=jaist' -O $@

# Builds PCAD, the heart of PLSI
$(CMD_PCAD_LIST_MACROS) \
$(CMD_PCAD_INFER_DECOUPLED) \
$(CMD_PCAD_MACRO_COMPILER): \
		$(OBJ_TOOLS_BIN_DIR)/pcad/stamp
	touch $@

$(OBJ_TOOLS_BIN_DIR)/pcad/stamp: $(OBJ_TOOLS_SRC_DIR)/pcad/Makefile $(CMD_GXX)
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(dir $<) install CXX=$(abspath $(CMD_GXX))
	@date > $@

$(OBJ_TOOLS_SRC_DIR)/pcad/Makefile: $(OBJ_TOOLS_SRC_DIR)/pcad/stamp \
				    $(OBJ_TOOLS_BIN_DIR)/tclap-$(TCLAP_VERSION)/stamp \
				    $(OBJ_TOOLS_BIN_DIR)/pson/stamp \
				    $(CMD_PCONFIGURE) $(CMD_PPKGCONFIG) $(CMD_PHC)
	mkdir -p $(dir $@)
	echo 'PREFIX = $(abspath $(OBJ_TOOLS_BIN_DIR))/pcad' >> $(dir $@)/Configfile.local
	echo 'LANGUAGES += c++' >> $(dir $@)/Configfile.local
	echo 'LINKOPTS += -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR))/gcc-$(GCC_VERSION)/lib64' >> $(dir $@)/Configfile.local
	echo 'COMPILEOPTS += -O3 -march=native -g' >> $(dir $@)/Configfile.local
	echo 'LINKOPTS += -O3 -march=native -g' >> $(dir $@)/Configfile.local
	cd $(dir $@); $(abspath $(CMD_PCONFIGURE)) --ppkg-config $(abspath $(CMD_PPKGCONFIG)) --phc $(abspath $(CMD_PHC))

$(OBJ_TOOLS_SRC_DIR)/pcad/stamp: $(shell find src/tools/pcad -type f)
	mkdir -p $(dir $@)
	rsync -a --delete src/tools/pcad/ $(OBJ_TOOLS_SRC_DIR)/pcad
	touch $@

# "builds" a SBT wrapper
$(CMD_SBT): src/tools/sbt/sbt
	mkdir -p $(dir $@)
	cat $^ | sed 's!@@SBT_SRC_DIR@@!$(abspath $(dir $^))!' > $@
	chmod +x $@

# PSON is a C++ JSON parsing library that also allows for JSON-like files that
# have extra trailing commas floating around.  Piping through this allows
# stateless JSON emission from various other parts of the code.
$(CMD_PSON2JSON): $(OBJ_TOOLS_BIN_DIR)/pson/stamp
	touch $@

$(OBJ_TOOLS_BIN_DIR)/pson/stamp: $(OBJ_TOOLS_SRC_DIR)/pson/Makefile $(CMD_GCC) $(CMD_GXX)
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(dir $<) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) install
	date > $@

$(OBJ_TOOLS_SRC_DIR)/pson/Makefile: \
		$(OBJ_TOOLS_SRC_DIR)/pson/Configfile \
		$(OBJ_TOOLS_BIN_DIR)/tclap-$(TCLAP_VERSION)/stamp \
		$(CMD_PCONFIGURE) $(CMD_GCC) $(CMD_GXX)
	@mkdir -p $(dir $@)
	echo 'PREFIX = $(abspath $(OBJ_TOOLS_BIN_DIR)/pson)' >> $(dir $@)/Configfile.local
	echo 'LANGUAGES += c++' >> $(dir $@)/Configfile.local
	echo 'LINKOPTS += -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR))/gcc-$(GCC_VERSION)/lib64' >> $(dir $@)/Configfile.local
	cd $(dir $<); $(abspath $(CMD_PCONFIGURE)) --ppkg-config $(abspath $(CMD_PPKGCONFIG)) --phc $(abspath $(CMD_PHC)) --verbose

$(OBJ_TOOLS_SRC_DIR)/pson/Configfile: $(shell find src/tools/pson -type f)
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	rsync -a --delete src/tools/pson/ $(dir $@)
	touch $@

# PFPMP is my collection of FIRRTL passes.
$(CMD_FIRRTL_GENERATE_TOP) $(CMD_FIRRTL_GENERATE_HARNESS): $(OBJ_TOOLS_BIN_DIR)/pfpmp/stamp $(CMD_SBT)
	touch $@

$(OBJ_TOOLS_BIN_DIR)/pfpmp/stamp: $(shell find src/tools/pfpmp/src -type f) $(shell find $(CORE_DIR)/firrtl/src -type f)
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	rsync -a --delete src/tools/pfpmp/ $(dir $@)
	$(SCHEDULER_CMD) --make -- $(MAKE) FIRRTL_HOME=$(abspath $(CORE_DIR)/firrtl) CMD_SBT=$(abspath $(CMD_SBT)) -C $(dir $@)
	date > $@

# Some machines don't have python3, but I want it everywhere.
$(CMD_PYTHON3): $(OBJ_TOOLS_BIN_DIR)/python3-$(PYTHON3_VERSION)/stamp
	touch $@

$(OBJ_TOOLS_BIN_DIR)/python3-$(PYTHON3_VERSION)/stamp: $(OBJ_TOOLS_SRC_DIR)/python3-$(PYTHON3_VERSION)/Makefile $(CMD_GCC) $(CMD_GXX)
	$(SCHEDULER_CMD) --make -- $(MAKE) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) -C $(dir $<) install
	date > $@

$(OBJ_TOOLS_SRC_DIR)/python3-$(PYTHON3_VERSION)/Makefile: $(OBJ_TOOLS_SRC_DIR)/python3-$(PYTHON3_VERSION)/configure $(CMD_GCC) $(CMD_GXX)
	cd $(dir $@); ./configure --prefix=$(abspath $(OBJ_TOOLS_BIN_DIR)/python3-$(PYTHON3_VERSION)) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX))
	touch $@

$(OBJ_TOOLS_SRC_DIR)/python3-$(PYTHON3_VERSION)/configure: $(PLSI_CACHE_DIR)/distfiles/python3-$(PYTHON3_VERSION).tar.gz
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	tar -C $(dir $@) -xpf $< --strip-components=1
	touch $@

$(PLSI_CACHE_DIR)/distfiles/python3-$(PYTHON3_VERSION).tar.gz:
	@mkdir -p $(dir $@)
	wget https://www.python.org/ftp/python/$(PYTHON3_VERSION)/Python-$(PYTHON3_VERSION).tgz -O $@

# Here are a bunch of pattern rules that will try to copy outputs.
bin/core-$(CORE_GENERATOR)-$(CORE_CONFIG)/$(CORE_TOP).v: $(OBJ_CORE_RTL_V)
	mkdir -p $(dir $@)
	cat $^ > $@

bin/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP).v: $(OBJ_SOC_RTL_V)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)/$(MAP_TOP).v: $(OBJ_MAP_RTL_V)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP).v: $(OBJ_SYN_MAPPED_V)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)/$(PAR_TOP).v: $(OBJ_PAR_ROUTED_V)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/core-$(CORE_GENERATOR)-$(CORE_CONFIG)/$(CORE_TOP)-simulator: $(OBJ_CORE_SIMULATOR)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/soc-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP)-simulator: $(OBJ_SOC_SIMULATOR)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/map-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)/$(MAP_TOP)-simulator: $(OBJ_MAP_SIMULATOR)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/syn-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP)-simulator: $(OBJ_SYN_SIMULATOR)
	mkdir -p $(dir > $@)
	cat $^ > $@

bin/par-$(CORE_GENERATOR)-$(CORE_CONFIG)-$(SOC_CONFIG)-$(TECHNOLOGY)-$(MAP_CONFIG)-$(SYN_CONFIG)-$(PAR_CONFIG)/$(PAR_TOP)-simulator: $(OBJ_PAR_SIMULATOR)
	mkdir -p $(dir > $@)
	cat $^ > $@

###############################################################################
# Internal Flow Targets
###############################################################################

# The targets in this section are part of the flow, but they're not things that
# can be customized using multiple variables because I don't think there should
# ever be more than one implementation of them.

# Generates a technology-specific makefrag from the technology's description
# file.

$(OBJ_TECH_DIR)/makefrags/vars.mk: src/tools/technology/generate-vars $(TECHNOLOGY_JSON) $(CMD_PYTHON3)
	@mkdir -p $(dir $@)
	PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $< -o $@ -i $(filter %.tech.json,$^)

$(OBJ_TECH_DIR)/makefrags/rules.mk: src/tools/technology/generate-rules $(TECHNOLOGY_JSON) $(CMD_PYTHON3)
	@mkdir -p $(dir $@)
	PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $< -o $@ -i $(filter %.tech.json,$^)

# FIXME: This is awkward: the technology-specific macro scripts might end up
# generating their own Verilog
$(OBJ_TECHNOLOGY_MACRO_LIBRARY): \
		src/tools/technology/generate-macros \
		$(TECHNOLOGY_JSON) \
		$(TECHNOLOGY_MARCO_PROVIDE_SCRIPTS) \
		$(TECHNOLOGY_VERILOG_FILES) \
		$(TECHNOLOGY_DOCUMENTATION_PDF_FILES) \
		$(CMD_PYTHON3)
	@mkdir -p $(dir $@)
	PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $< -o $@ -i $(filter %.tech.json,$^) --technology $(TECHNOLOGY)

# The implementation of the technology mapping stage.  This produces the
# verilog for synthesis that can later be used.  It's meant to be a single
# file, so the macros are actually generated seperately.
$(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.v: \
		$(CMD_PCAD_MACRO_COMPILER) \
		$(OBJ_SOC_MACROS) \
		$(OBJ_TECHNOLOGY_MACRO_LIBRARY)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -v $@ -m $(filter %.macros.json,$^) --syn-flops -l $(filter %.macro_library.json,$^) |& tee $(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.log | tail

$(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.mk: \
		src/tools/map/list-macros \
		$(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.v \
		$(OBJ_TECHNOLOGY_MACRO_LIBRARY)
	@mkdir -p $(dir $@)
	$< -o $@ --mode $(patsubst $(MAP_TOP).macros_for_%.mk,%,$(notdir $@)) $^
