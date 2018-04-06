# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
# Generate a top-level Verilog file for Vivado FPGA SoCs.
# TODO: deal with simulation

SOC_TOP = $(CORE_TOP)
SOC_SIM_TOP = $(CORE_SIM_TOP)

# The top-level system (soc) file.
OBJ_SOC_PIN_MAP_DATABASE = $(SOC_GENERATOR_ADDON)/pins.csv
OBJ_SOC_SYSTEM_TOP_V = $(OBJ_SOC_DIR)/generated/system.v
ifeq ($(CORE_CONFIG_VIVADO_PINMAP),)
$(error You must set CORE_CONFIG_VIVADO_PINMAP to the pinmap for Vivado)
endif

OBJ_SOC_RTL_V = $(OBJ_SOC_SYSTEM_TOP_V) $(OBJ_CORE_RTL_V)
OBJ_SOC_SIM_FILES = $(OBJ_CORE_SIM_FILES)
OBJ_SOC_SIM_MACRO_FILES = $(OBJ_CORE_SIM_MACRO_FILES)
OBJ_SOC_MACROS = $(OBJ_CORE_MACROS)
