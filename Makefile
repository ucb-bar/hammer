# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

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

# The directory in which the RTL lives
CORE_DIR ?= src/rocket-chip

# The "core generator" generates top-level RTL, but doesn't include anything
# that's technology specific
CORE_GENERATOR ?= rocket-chip

# The "soc generator" is used to add everything to a soc that isn't part of
# the core generator (maybe because it's a NDA or something).  This default
# soc generator doesn't actually do anything at all.
SOC_GENERATOR ?= nop

# The technology that will be used to implement this design.
TECHNOLOGY ?= tsmc180

# The synthesis tool to run.
SYNTHESIS_TOOL ?= yosys

# The configuration to run when running various steps of the process
CORE_CONFIG ?= DefaultConfig
CORE_SIM_CONFIG ?= default
SOC_CONFIG ?= default
SYN_CONFIG ?= default

# Defines the simulator used to run simulation at different levels
CORE_SIMULATOR ?= verilator
SOC_SIMULATOR ?= verilator
SYN_SIMULATOR ?= verilator

# The scheduler to use when running large jobs.  Changing this doesn't have any
# effect on the generated files, just the manner in which they are generated.
SCHEDULER ?= auto

# A cache directory for things that are, for some reason, difficult to create
# and never change.  This is suitable for installing as a read-only shared
# directory as long as someone writes to it first.
PLSI_CACHE_DIR ?= obj/cache

##############################################################################
# Internal Variables
##############################################################################

# These variables aren't meant to be overridden by users -- you probably
# shouldn't be changing them at all.

# Versions of externally developed programs to download
TCLAP_VERSION = 1.2.1
TCL_LIBRARY_VERSION = 8.6
TCL_VERSION = 8.6.6

# OBJ_*_DIR are the directories in which outputs end up
OBJ_TOOLS_DIR = obj/tools
OBJ_CORE_DIR = obj/core-$(CORE_CONFIG)
OBJ_SOC_DIR = obj/soc-$(CORE_CONFIG)-$(SOC_CONFIG)
OBJ_TECH_DIR = obj/technology/$(TECHNOLOGY)
OBJ_SYN_DIR = obj/syn-$(CORE_CONFIG)-$(SOC_CONFIG)-$(SYN_CONFIG)

# CHECK_* directories are where the output of tests go
CHECK_CORE_DIR = check/core-$(CORE_CONFIG)
CHECK_SOC_DIR = check/soc-$(CORE_CONFIG)-$(SOC_CONFIG)
CHECK_SYN_DIR = check/syn-$(CORE_CONFIG)-$(SOC_CONFIG)-$(SYN_CONFIG)

CMD_PTEST = $(OBJ_TOOLS_DIR)/pconfigure/bin/ptest
CMD_PCONFIGURE = $(OBJ_TOOLS_DIR)/pconfigure/bin/pconfigure
CMD_PPKGCONFIG = $(OBJ_TOOLS_DIR)/pconfigure/bin/ppkg-config
CMD_PHC = $(OBJ_TOOLS_DIR)/pconfigure/bin/phc
CMD_PCAD_INFER_DECOUPLED = $(OBJ_TOOLS_DIR)/pcad/bin/pcad-pipe-infer_decoupled
CMD_SBT = $(OBJ_TOOLS_DIR)/sbt/sbt

PKG_CONFIG_PATH=$(abspath $(OBJ_TOOLS_DIR)/install/lib/pkgconfig)
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
$(error Unable to resolve CORE_GENERATOR=$(CORE_GENERATOR): found "$(CORE_GENERATOR_ADDON)")
endif

SOC_GENERATOR_ADDON = $(wildcard src/addons/soc-generator/$(SOC_GENERATOR)/ $(ADDONS_DIR)/soc-generator/$(SOC_GENERATOR)/)
ifneq ($(words $(SOC_GENERATOR_ADDON)),1)
$(error Unable to resolve SOC_GENERATOR=$(SOC_GENERATOR): found "$(SOC_GENERATOR_ADDON)")
endif

SOC_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(SOC_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(SOC_SIMULATOR)/)
ifneq ($(words $(SOC_SIMULATOR_ADDON)),1)
$(error Unable to resolve SOC_GENERATOR=$(SOC_GENERATOR): found "$(SOC_GENERATOR_ADDON)")
endif

SYNTHESIS_TOOL_ADDON = $(wildcard src/addons/synthesis/$(SYNTHESIS_TOOL)/ $(ADDONS_DIR)/synthesis/$(SYNTHESIS_TOOL)/)
ifneq ($(words $(SYNTHESIS_TOOL_ADDON)),1)
$(error Unable to resolve SOC_GENERATOR=$(SOC_GENERATOR): found "$(SOC_GENERATOR_ADDON)")
endif

SYN_SIMULATOR_ADDON = $(wildcard src/addons/simulator/$(SYN_SIMULATOR)/ $(ADDONS_DIR)/simulator/$(SYN_SIMULATOR)/)
ifneq ($(words $(SYN_SIMULATOR_ADDON)),1)
$(error Unable to resolve SYN_GENERATOR=$(SYN_GENERATOR): found "$(SYN_GENERATOR_ADDON)")
endif

# In order to prevent EEs from seeing Makefiles, the technology description is
# a JSON file.  This simply checks to see that the file exists before
# continuing, in order to ensure there's no trickier errors.
TECHNOLOGY_JSON = $(wildcard src/technologies/$(TECHNOLOGY).tech.json)
ifeq ($(TECHNOLOGY_JSON),)
$(error "Unable to find technology $(TECHNOLOGY), expected a cooresponding .tech.json file")
endif

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

ifeq ($(CORE_TOP),)
# The name of the top-level RTL module that comes out of the core generator.
$(error CORE_GENERATOR needs to set CORE_TOP)
endif

ifeq ($(OBJ_CORE_RTL_V),)
# The name of the top-level RTL Verilog output by the core.
$(error CORE_GENERATOR needs to set OBJ_CORE_RTL_V)
endif

include $(SOC_GENERATOR_ADDON)/vars.mk
include $(SOC_SIMULATOR_ADDON)/soc-vars.mk

ifeq ($(OBJ_SOC_RTL_V),)
# The name of the top-level RTL Verilog output by the SOC generator.
$(error SOC_GENERATOR needs to set OBJ_SOC_RTL_V)
endif

-include $(OBJ_TECH_DIR)/makefrags/vars.mk

#ifeq ($(TECHNOLOGY_LIBERTY_FILES),)
#$(error TECHNOLOGY needs to set TECHNOLOGY_LIBERTY_FILES)
#endif

include $(SYNTHESIS_TOOL_ADDON)/vars.mk
include $(SOC_SIMULATOR_ADDON)/syn-vars.mk

ifeq ($(OBJ_SYN_MAPPED_V),)
$(error SYNTHESIS_TOOL needs to set OBJ_SYN_MAPPED_V)
endif

ifeq ($(SYN_TOP),)
$(error SYNTHESIS_TOOL needs to set SYN_TOP)
endif

# All the rules get sourced last.  We don't allow any variables to be set here,
# so the ordering isn't important.
include $(CORE_GENERATOR_ADDON)/rules.mk
include $(CORE_SIMULATOR_ADDON)/core-rules.mk
include $(SOC_GENERATOR_ADDON)/rules.mk
include $(SOC_SIMULATOR_ADDON)/soc-rules.mk
-include $(OBJ_TECH_DIR)/makefrags/rules.mk
include $(SYNTHESIS_TOOL_ADDON)/rules.mk
include $(SOC_SIMULATOR_ADDON)/syn-rules.mk

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
check: $(patsubst %,check-%,core soc syn)

# A virtual target that reports on the status of the test cases, in addition to
# running them (if necessary).
.PHONY: report
report: $(CMD_PTEST) check
	+$(CMD_PTEST)

# These various smaller test groups are all defined by the core generator!
.PHONY: check-core
check-core:

.PHONY: check-soc
check-soc:

# The various RTL targets
.PHONY: core-verilog
core-verilog: bin/core-$(CORE_CONFIG)/$(CORE_TOP).v
	$(info $@ availiable at $<)

.PHONY: soc-verilog
soc-verilog: bin/soc-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP).v
	$(info $@ availiable at $<)

.PHONY: syn-verilog
syn-verilog: bin/syn-$(CORE_CONFIG)-$(SOC_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP).v
	$(info $@ availiable at $<)

# The various simulators
.PHONY: core-simulator
core-simulator: bin/core-$(CORE_CONFIG)/$(CORE_TOP)-simulator
.PHONY: soc-simulator
soc-simulator: bin/soc-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP)-simulator

# This just cleans everything
.PHONY: clean
clean::
	rm -rf $(OBJ_TOOLS_DIR)
	rm -rf $(OBJ_CORE_DIR) $(CHECK_CORE_DIR)
	rm -rf $(OBJ_SOC_DIR) $(CHECK_SOC_DIR)
	rm -rf $(OBJ_SYN_DIR) $(CHECK_SYN_DIR)

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

# Builds pconfigure and its related tools
$(OBJ_TOOLS_DIR)/pconfigure/bin/%: $(OBJ_TOOLS_DIR)/pconfigure/Makefile
	$(MAKE) -C $(OBJ_TOOLS_DIR)/pconfigure bin/$(notdir $@)

$(OBJ_TOOLS_DIR)/pconfigure/Makefile: $(OBJ_TOOLS_DIR)/pconfigure/Configfile.local \
                                      src/tools/pconfigure/Configfiles/main \
                                      $(shell find src/tools/pconfigure/src -type f) \
                                      src/tools/pconfigure/bootstrap.sh
	mkdir -p $(dir $@)
	+cd $(dir $@); $(SCHEDULER_CMD) --max-threads=1 -- $(abspath src/tools/pconfigure/bootstrap.sh) $(abspath src/tools/pconfigure)/

$(OBJ_TOOLS_DIR)/pconfigure/Configfile.local:
	mkdir -p $(dir $@)
	echo "PREFIX = $(abspath $(OBJ_TOOLS_DIR)/pconfigure)" > $@

# Most of the CAD tools have some sort of TCL interface, and the open source
# ones require a TCL installation
$(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)-install/include/tcl.h: $(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)/unix/Makefile
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)/unix install

$(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)/unix/Makefile: $(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)/README
	cd $(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)/unix; ./configure --prefix=$(abspath $(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)-install)

$(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)/README: $(PLSI_CACHE_DIR)/distfiles/tcl-$(TCL_VERSION).tar.gz
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	tar -xzpf $< --strip-components=1 -C $(dir $@)
	touch $@

$(PLSI_CACHE_DIR)/distfiles/tcl-$(TCL_VERSION).tar.gz:
	mkdir -p $(dir $@)
	wget http://prdownloads.sourceforge.net/tcl/tcl$(TCL_VERSION)-src.tar.gz -O $@

# TCLAP is a C++ command-line argument parser that's used by PCAD
$(OBJ_TOOLS_DIR)/install/include/tclap/CmdLine.h: $(OBJ_TOOLS_DIR)/tclap-$(TCLAP_VERSION)/Makefile
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(OBJ_TOOLS_DIR)/tclap-$(TCLAP_VERSION) install

$(OBJ_TOOLS_DIR)/tclap-$(TCLAP_VERSION)/Makefile: $(OBJ_TOOLS_DIR)/tclap-$(TCLAP_VERSION)/configure
	cd $(OBJ_TOOLS_DIR)/tclap-$(TCLAP_VERSION); ./configure --prefix=$(abspath $(OBJ_TOOLS_DIR)/install)

$(OBJ_TOOLS_DIR)/tclap-$(TCLAP_VERSION)/configure: $(PLSI_CACHE_DIR)/distfiles/tclap-$(TCLAP_VERSION).tar.gz
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	tar -xvzpf $< --strip-components=1 -C $(dir $@)
	touch $@

$(PLSI_CACHE_DIR)/distfiles/tclap-$(TCLAP_VERSION).tar.gz:
	mkdir -p $(dir $@)
	wget 'http://downloads.sourceforge.net/project/tclap/tclap-$(TCLAP_VERSION).tar.gz?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Ftclap%2Ffiles%2F&ts=1468971231&use_mirror=jaist' -O $@

# Builds PCAD, the heart of PLSI
$(OBJ_TOOLS_DIR)/pcad/bin/%: $(OBJ_TOOLS_DIR)/pcad/Makefile
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(OBJ_TOOLS_DIR)/pcad bin/$(notdir $@)

$(OBJ_TOOLS_DIR)/pcad/Makefile: src/tools/pcad/Configfile \
				$(shell find src/tools/pcad/src -type f) \
				$(OBJ_TOOLS_DIR)/install/include/tclap/CmdLine.h \
				$(CMD_PCONFIGURE) $(CMD_PPKGCONFIG) $(CMD_PHC)
	mkdir -p $(dir $@)
	cd $(dir $@); $(abspath $(CMD_PCONFIGURE)) --ppkg-config $(abspath $(CMD_PPKGCONFIG)) --phc $(abspath $(CMD_PHC)) --srcpath $(abspath src/tools/pcad)

# "builds" a SBT wrapper
$(CMD_SBT): src/tools/sbt/sbt
	mkdir -p $(dir $@)
	cat $^ | sed 's!@@SBT_SRC_DIR@@!$(abspath $(dir $^))!' > $@
	chmod +x $@

# Here are a bunch of pattern rules that will try to copy outputs.
bin/core-$(CORE_CONFIG)/$(CORE_TOP).v: $(OBJ_CORE_RTL_V)
	mkdir -p $(dir $@)
	cp --reflink=auto $^ $@

bin/soc-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP).v: $(OBJ_SOC_RTL_V)
	mkdir -p $(dir $@)
	cp --reflink=auto $^ $@

bin/syn-$(CORE_CONFIG)-$(SOC_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP).v: $(OBJ_SYN_MAPPED_V)
	mkdir -p $(dir $@)
	cp --reflink=auto $^ $@

bin/core-$(CORE_CONFIG)/$(CORE_TOP)-simulator: $(OBJ_CORE_SIMULATOR)
	mkdir -p $(dir $@)
	cp --reflink=auto $^ $@

bin/soc-$(CORE_CONFIG)-$(SOC_CONFIG)/$(SOC_TOP)-simulator: $(OBJ_SOC_SIMULATOR)
	mkdir -p $(dir $@)
	cp --reflink=auto $^ $@

bin/syn-$(CORE_CONFIG)-$(SOC_CONFIG)-$(SYN_CONFIG)/$(SYN_TOP)-simulator: $(OBJ_SYN_SIMULATOR)
	mkdir -p $(dir $@)
	cp --reflink=auto $^ $@

###############################################################################
# Internal Flow Targets
###############################################################################

# The targets in this section are part of the flow, but they're not things that
# can be customized using multiple variables because I don't think there should
# ever be more than one implementation of them.

# Generates a technology-specific makefrag from the technology's description
# file.

$(OBJ_TECH_DIR)/makefrags/vars.mk: src/tools/technology/generate-vars $(TECHNOLOGY_JSON)
	@mkdir -p $(dir $@)
	$< -o $@ -i $(filter %.tech.json,$^)

$(OBJ_TECH_DIR)/makefrags/rules.mk: src/tools/technology/generate-rules $(TECHNOLOGY_JSON)
	@mkdir -p $(dir $@)
	$< -o $@ -i $(filter %.tech.json,$^)
