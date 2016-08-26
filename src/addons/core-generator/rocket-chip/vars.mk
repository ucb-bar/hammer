# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# The RTL generates a top-level Verilog file that contains both the core and
# the test harness.  In here, "CORE_TOP" is the name of the top-level of the
# Verilog for synthesis and "CORE_SIM_TOP" is the name of the top-level of the
# Verilog for simulation.
RC_CORE_TOP = Top
CORE_TOP ?= $(RC_CORE_TOP)

RC_CORE_SIM_TOP = TestHarness
CORE_SIM_TOP ?= $(RC_CORE_SIM_TOP)

# This contains the whole Rocket Chip along with all the test harness stuff.
RC_OBJ_CORE_RTL_V = $(OBJ_CORE_DIR)/$(CORE_SIM_TOP).$(CORE_CONFIG).v
OBJ_CORE_RTL_V ?= $(RC_OBJ_CORE_RTL_V)

# There are various simulation-only, non-Verilog files needed to make the
# Verilog simulate.  They're all defined here.
RC_OBJ_CORE_SIM_FILES = \
	$(CORE_DIR)/csrc/verilator.h \
	$(CORE_DIR)/csrc/emulator.cc \
	$(CORE_DIR)/csrc/SimDTM.cc \
	$(OBJ_TOOLS_DIR)/riscv-tools/include/plsi-include.stamp \
	$(OBJ_TOOLS_DIR)/riscv-tools/lib/libfesvr.so \
	$(CORE_DIR)/vsrc/SimDTM.v \
	$(CORE_DIR)/vsrc/TestDriver.v \
	$(CORE_DIR)/vsrc/DebugTransportModuleJtag.v \
	src/addons/core-generator/rocket-chip/src/clock.vh
OBJ_CORE_SIM_FILES = $(RC_OBJ_CORE_SIM_FILES)

# Rocket Chip generates a Makefrag for testing.  This isn't in the format I
# want (it doesn't have all my dependency stages) so I do some post-processing
# of this to produce my test list.
RC_OBJ_CORE_RTL_D = $(OBJ_CORE_DIR)/$(CORE_SIM_TOP).$(CORE_CONFIG).d
OBJ_CORE_RTL_D ?= $(RC_OBJ_CORE_RTL_D)

RC_OBJ_CORE_TESTS_MK = $(OBJ_CORE_DIR)/tests.mk
OBJ_CORE_TESTS_MK ?= $(RC_OBJ_CORE_TESTS_MK)

# Rocket Chip supports additional addons that it can support, if a user defines
# CORE_ADDON_DIR and then calls into this file then they'll end up with a
# Rocket Chip that has a few more bits added to it.
ifneq ($(CORE_ADDON_DIR),)
CORE_ADDON_FILES = \
	$(patsubst $(CORE_ADDON_DIR)/%,$(OBJ_CORE_DIR)/rocket-chip/src/main/scala/%,$(wildcard $(CORE_ADDON_DIR)/*.scala))
endif
