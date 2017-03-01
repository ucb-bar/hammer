# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

# e.g. /ecad/tools/xilinx/Vivado/2016.2
ifeq ($(VIVADO_HOME),)
$(error You must set VIVADO_HOME to be able to run Vivado synthesis)
endif

ifneq ($(TECHNOLOGY), vivado)
$(error You must set TECHNOLOGY to "vivado" to be able to run Vivado synthesis)
endif

VIVADO_BIN = $(VIVADO_HOME)/bin/vivado

VIVADO_FLAGS := \
	-nojournal -mode batch \
	-source script/board.tcl \
	-source script/prologue.tcl

# Vivado/Arty board files.
# TODO: (wishlist) make this parametrizable
VIVADO_BOARDS_REV = d987883f48a1bf629688743fd14cd372f3502b0b
OBJ_SYN_BOARD_FILES = $(OBJ_SYN_DIR)/board_files/extracted.stamp
OBJ_SYN_BOARD_FILES_DIR := $(dir $(OBJ_SYN_BOARD_FILES))

# A Verilog file containing the pre-synthesized Xilinx SRAM macros.
# TODO: FIXME: This is definitely not the right place for this.
# $(TECHNOLOGY_VERILOG_FILES) doesn't seem to be right,
# and $(OBJ_MAP_RTL_V) doesn't seem to have any other files...
# This is probably not the right approach but we have to get something
# working, so...
OBJ_SYN_MACRO_LIB_V = $(OBJ_SYN_DIR)/generated/xilinx-macros.v
OBJ_SYN_MACRO_LIB_DCP_DIR = $(OBJ_SYN_DIR)/generated/xilinx-macros-dcp

# The post_synth.dcp file from Vivado; used for place and route and beyond.
OBJ_SYN_POST_SYNTH_DCP = $(OBJ_SYN_DIR)/generated/post_synth.dcp

SYN_TOP = $(MAP_TOP)
SYN_SIM_TOP = $(MAP_SIM_TOP)
OBJ_SYN_MAPPED_V = $(OBJ_SYN_DIR)/generated/$(SYN_TOP).mapped.v
OBJ_SYN_SIM_FILES = $(OBJ_MAP_SIM_FILES) $(TECHNOLOGY_VERILOG_FILES)
