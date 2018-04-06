# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

SOC_TOP = TestTop
SOC_TOP_FOR_SYNTHESIS = ChipTop
SOC_SIM_TOP = $(CORE_SIM_TOP)

OBJ_SOC_RTL_V = $(OBJ_SOC_DIR)/$(SOC_TOP).v
OBJ_SOC_SIM_FILES = $(OBJ_CORE_SIM_FILES)

OBJ_SOC_RTL_C = $(patsubst %,$(OBJ_SOC_DIR)/csrc/%,$(notdir $(OBJ_CORE_RTL_C)))
