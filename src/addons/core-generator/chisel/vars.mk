# Generic Chisel design core generator.
# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

ifeq ($(CORE_TOP),)
$(error You must set CORE_TOP to the top-level module of your Chisel design)
endif
ifeq ($(CORE_SIM_TOP),)
$(warning You should set CORE_SIM_TOP to the top-level simulation harness of your Chisel design)
endif
CORE_SIM_TOP ?= $(CORE_TOP)

ifeq ($(CORE_CONFIG_TOP_PACKAGE),)
$(error You must set CORE_CONFIG_TOP_PACKAGE as the package for the top-level module of your Chisel design.)
endif

ifeq ($(CORE_CONFIG_PROJ_DIR),)
$(error You must set CORE_CONFIG_PROJ_DIR as the path to your Chisel design which includes build.sbt)
endif

# The format for the pin mappings for Vivado FPGA synthesis.
# Optional unless Vivado is being used.
# See pinmap.format.json for the format.
CORE_CONFIG_VIVADO_PINMAP ?= $(CORE_CONFIG_PROJ_DIR)/pinmap.json

# TODO: fix SIM files and macros, decide on filenames, etc.
# Maybe also add checks for existence here for debugging.
OBJ_CORE_SIM_FILES = $(CORE_CONFIG_PROJ_DIR)/src/$(CORE_TOP)Harness.v
OBJ_CORE_SIM_MACRO_FILES = $(CORE_CONFIG_PROJ_DIR)/src/$(CORE_TOP).simulation_macros.v
OBJ_CORE_MACROS = $(CORE_CONFIG_PROJ_DIR)/src/$(CORE_TOP).macros.json
ifeq (,$(wildcard $(OBJ_CORE_SIM_FILES)))
    $(error Verilog test harness does not exist! If it is not required, run "touch $(OBJ_CORE_SIM_FILES)" to create a blank file)
endif
ifeq (,$(wildcard $(OBJ_CORE_SIM_MACRO_FILES)))
    $(error Verilog sim macro file does not exist! If it is not required, run "touch $(OBJ_CORE_SIM_MACRO_FILES)" to create a blank file)
endif
ifeq (,$(wildcard $(OBJ_CORE_MACROS)))
    $(error Verilog sim macros file does not exist! If it is not required, run "echo "[]" > $(OBJ_CORE_MACROS)" to create a blank file)
endif

OBJ_CORE_RTL_FIR = $(OBJ_CORE_DIR)/generated/$(CORE_TOP).fir
OBJ_CORE_RTL_V = $(OBJ_CORE_DIR)/generated/$(CORE_TOP).v

# If you don't define something here then there won't be any test cases that
# can actually run.
check-core: $(CHECK_CORE_DIR)/random.out
trace-core: $(CHECK_CORE_DIR)/random.trace-out
check-soc: $(CHECK_SOC_DIR)/random.out
trace-soc: $(CHECK_SOC_DIR)/random.trace-out
check-map: $(CHECK_MAP_DIR)/random.out
trace-map: $(CHECK_MAP_DIR)/random.trace-out
check-syn: $(CHECK_SYN_DIR)/random.out
trace-syn: $(CHECK_SYN_DIR)/random.trace-out
