# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

SOC_TOP = TestTop
SOC_TOP_FOR_SYNTHESIS = ChipTop

OBJ_SOC_RTL_V = $(OBJ_SOC_DIR)/$(SOC_TOP).v
OBJ_SOC_RTL_H = $(OBJ_CORE_RTL_H)
OBJ_SOC_RTL_O = $(OBJ_CORE_RTL_O)
OBJ_SOC_RTL_I = $(OBJ_CORE_RTL_I)

OBJ_SOC_RTL_C = $(patsubst %,$(OBJ_SOC_DIR)/csrc/%,$(notdir $(OBJ_CORE_RTL_C)))
