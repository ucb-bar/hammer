# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# The default target, which runs everything and tells you if it passed or not.
all: report

###############################################################################
# Default Variables
###############################################################################

# Don't change these variables here, instead override them with a
# "Makefile.project" in the directory above this one, or on the command line
# (if you want to do experiments).

# The directory in which the RTL lives
SYSTEM_DIR ?= src/rocket-chip

# The "system generator" generates top-level RTL, but doesn't include anything
# that's technology specific
SYSTEM_GENERATOR ?= rocket-chip

# The configuration to run when running various steps of the process
SYSTEM_CONFIG ?= DefaultConfig
RTL_CONFIG ?= default

# Defines the simulator used to run simulation at different levels
SYSTEM_SIMULATOR ?= verilator

# The scheduler to use when running large jobs.  Changing this doesn't have any
# effect on the generated files, just the manner in which they are generated.
SCHEDULER ?= local

# A cache directory for things that are, for some reason, difficult to create
# and never change.  This is suitable for installing as a read-only shared
# directory as long as someone writes to it first.
PLSI_CACHE_DIR ?= obj/cache

##############################################################################
# Internal Variables
##############################################################################

# These variables aren't meant to be overridden by users -- you probably
# shouldn't be changing them at all.

# OBJ_*_DIR are the directories in which outputs end up
OBJ_TOOLS_DIR = obj/tools
OBJ_SYSTEM_DIR = obj/system-$(SYSTEM_CONFIG)
OBJ_CHECK_RTL_DIR = obj/check/rtl-$(SYSTEM_CONFIG)-$(RTL_CONFIG)

# CHECK_* directories are where the output of tests go
CHECK_SYSTEM_DIR = check/system-$(SYSTEM_CONFIG)

# The outputs from the RTL generator
OBJ_SYSTEM_RTL_V = $(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).v

CMD_PTEST = $(OBJ_TOOLS_DIR)/pconfigure/bin/ptest

##############################################################################
# Addon Loading
##############################################################################

# This section loads the various PLSI addons.  You shouldn't be screwing with
# this, but if you're trying to add a new addon then you might want to look
# here to see what variables it's expected to set.

# Locates the various addons that will be used to setup 
SYSTEM_GENERATOR_ADDON = $(wildcard src/addons/system-generator/$(SYSTEM_GENERATOR)/ $(ADDONS_DIR)/system-generator/$(SYSTEM_GENERATOR)/)
ifneq ($(words $(SYSTEM_GENERATOR_ADDON)),1)
$(error Unable to resolve SYSTEM_GENERATOR=$(SYSTEM_GENERATOR): found "$(SYSTEM_GENERATOR_ADDON)")
endif

SYSTEM_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(SYSTEM_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(SYSTEM_SIMULATOR)/)
ifneq ($(words $(SYSTEM_SIMULATOR_ADDON)),1)
$(error Unable to resolve SYSTEM_GENERATOR=$(SYSTEM_GENERATOR): found "$(SYSTEM_GENERATOR_ADDON)")
endif

include $(SYSTEM_GENERATOR_ADDON)/vars.mk
include $(SYSTEM_SIMULATOR_ADDON)/system-vars.mk

# The name of the top-level RTL module that comes out of the system generator.
ifeq ($(SYSTEM_TOP),)
$(error SYSTEM_GENERATOR needs to set SYSTEM_TOP)
endif

include $(SYSTEM_GENERATOR_ADDON)/rules.mk
include $(SYSTEM_SIMULATOR_ADDON)/system-rules.mk

##############################################################################
# User Targets
##############################################################################

# The targets in here are short names for some of the internal targets below.
# These are probably the commands you want to manually run.

# Runs all the test cases.  Note that this _always_ passes, you need to run
# "make report" to see if the tests passed or not.
.PHONY: check
check: check-system

# A virtual target that reports on the status of the test cases, in addition to
# running them (if necessary).
.PHONY: report
report: $(CMD_PTEST) check
	+$(CMD_PTEST)

# Runs all the test cases at the RTL level.  The test list is actually defined
# by the system generator, so you won't really see anything here.
.PHONY: check-system
check-system:

# Generates the system-level RTL
system-verilog: bin/system-$(SYSTEM_CONFIG)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).v

# This just cleans everything
.PHONY: clean
clean::
	rm -rf $(OBJ_TOOLS_DIR) $(OBJ_SYSTEM_DIR) $(OBJ_CHECK_RTL_DIR)

##############################################################################
# Internal Targets
##############################################################################

# These targets are internal to PLSI, you probably shouldn't even be building
# them directly from the command-line.  Use the nicely named targets above,
# they're easier to remember.

# Builds pconfigure and its related tools
$(OBJ_TOOLS_DIR)/pconfigure/bin/%: $(OBJ_TOOLS_DIR)/pconfigure/Makefile
	$(MAKE) -C $(OBJ_TOOLS_DIR)/pconfigure bin/$(notdir $@)

$(OBJ_TOOLS_DIR)/pconfigure/Makefile: $(OBJ_TOOLS_DIR)/pconfigure/Configfile.local \
                                      src/tools/pconfigure/Configfiles/main \
                                      $(shell find src/tools/pconfigure/src -type f) \
                                      src/tools/pconfigure/bootstrap.sh
	mkdir -p $(dir $@)
	+cd $(dir $@); $(abspath src/tools/pconfigure/bootstrap.sh) $(abspath src/tools/pconfigure)/

$(OBJ_TOOLS_DIR)/pconfigure/Configfile.local:
	mkdir -p $(dir $@)
	echo "PREFIX = $(abspath $(OBJ_TOOLS_DIR)/pconfigure)" > $@

# Here are a bunch of pattern rules that will try
bin/system-$(SYSTEM_CONFIG)/%: $(OBJ_SYSTEM_DIR)/%
	mkdir -p $(dir $@)
	cp --reflink=auto $< $@
