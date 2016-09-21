# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

YOSYS_VERSION ?= 0.6
ABC_VERSION ?= 20160717

YOSYS_BIN = $(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)-install/bin/yosys

SYN_TOP = $(SOC_TOP)
OBJ_SYN_MAPPED_V = $(OBJ_SYN_DIR)/generated/$(SYN_TOP).mapped.v
OBJ_SYN_SIM_FILES = $(OBJ_SOC_SIM_FILES) $(TECHNOLOGY_VERILOG_FILES)
