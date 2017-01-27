# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

CORE_DIR ?= src/addons/core-generator/rocketchip/rocket-chip

# The RTL generates a top-level Verilog file that contains both the core and
# the test harness.  In here, "CORE_TOP" is the name of the top-level of the
# Verilog for synthesis and "CORE_SIM_TOP" is the name of the top-level of the
# Verilog for simulation.
RC_CORE_TOP = ExampleRocketTop
CORE_TOP ?= $(RC_CORE_TOP)

RC_CORE_SIM_TOP = TestHarness
CORE_SIM_TOP ?= $(RC_CORE_SIM_TOP)

# This contains the whole Rocket Chip along with all the test harness stuff.
RC_OBJ_CORE_RTL_V = \
	$(OBJ_CORE_DIR)/plsi-generated/$(CORE_TOP).$(CORE_CONFIG).v \
	$(CORE_DIR)/vsrc/DebugTransportModuleJtag.v \
	$(CORE_DIR)/vsrc/AsyncResetReg.v
OBJ_CORE_RTL_V ?= $(RC_OBJ_CORE_RTL_V)

# The other output of a core generator is a list of macros that need to be
# implemented in the technology.
RC_OBJ_CORE_MACROS = $(OBJ_CORE_DIR)/plsi-generated/$(CORE_TOP).$(CORE_CONFIG).macros.json
OBJ_CORE_MACROS = $(RC_OBJ_CORE_MACROS)

# I can't use upstream's FIRRTL invocation so I have to provide my own (to
# split the test harness out into two parts).
RC_OBJ_CORE_RTL_FIR = $(OBJ_CORE_DIR)/rocketchip-generated/rocketchip.$(CORE_CONFIG).fir
OBJ_CORE_RTL_FIRRTL ?= $(RC_OBJ_CORE_RTL_FIR)

OBJ_CORE_FIRRTL_TOP_CMD ?= $(OBJ_CORE_DIR)/firrtl-passes/GenerateTop/GenerateTop
OBJ_CORE_FIRRTL_HARNESS_CMD ?= $(OBJ_CORE_DIR)/firrtl-passes/GenerateHarness/GenerateHarness

# The SRAM configuration file that comes out of Rocket Chip isn't directly but
# instead needs to be merged into a macro file.
RC_OBJ_CORE_MEMORY_CONF = $(OBJ_CORE_DIR)/rocketchip-generated/rocketchip.$(CORE_CONFIG).conf

# There are various simulation-only, non-Verilog files needed to make the
# Verilog simulate.  They're all defined here.
RC_OBJ_CORE_SIM_FILES = \
	$(CORE_DIR)/csrc/verilator.h \
	$(CORE_DIR)/csrc/emulator.cc \
	$(CORE_DIR)/csrc/SimDTM.cc \
	$(OBJ_CORE_DIR)/riscv-tools-install/include/plsi-include.stamp \
	$(OBJ_CORE_DIR)/riscv-tools-install/lib/libfesvr.so \
	$(CORE_DIR)/vsrc/SimDTM.v \
	$(CORE_DIR)/vsrc/TestDriver.v \
	$(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).v \
	src/addons/core-generator/rocketchip/src/clock.vh \
	$(OBJ_CORE_DIR)/plsi-generated/model.vh \
	$(CORE_DIR)/vsrc/jtag_vpi.v \
	$(CORE_DIR)/vsrc/jtag_vpi.tab
OBJ_CORE_SIM_FILES = $(RC_OBJ_CORE_SIM_FILES)

# These files provide Verilog implementations of the macros, and might be
# replaced by the output of some other tool.
RC_OBJ_CORE_SIM_MACRO_FILES = \
	$(OBJ_CORE_DIR)/plsi-generated/$(CORE_TOP).$(CORE_CONFIG).macros.v
OBJ_CORE_SIM_MACRO_FILES = $(RC_OBJ_CORE_SIM_MACRO_FILES)

# Rocket Chip generates a Makefrag for testing.  This isn't in the format I
# want (it doesn't have all my dependency stages) so I do some post-processing
# of this to produce my test list.
RC_OBJ_CORE_RTL_D = $(OBJ_CORE_DIR)/rocketchip-generated/rocketchip.$(CORE_CONFIG).d
OBJ_CORE_RTL_D ?= $(RC_OBJ_CORE_RTL_D)

RC_OBJ_CORE_TESTS_MK = $(OBJ_CORE_DIR)/plsi-generated/tests-$(CORE_SIM_CONFIG).mk
OBJ_CORE_TESTS_MK ?= $(RC_OBJ_CORE_TESTS_MK)

# If you're extending Rocket Chip then you'll want to override this to the
# project that contains your configurations.
RC_CORE_CFG_PROJECT ?= rocketchip
