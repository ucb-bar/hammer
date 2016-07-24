# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

CORE_TOP = Top

OBJ_CORE_RTL_V = $(OBJ_CORE_DIR)/$(CORE_TOP).$(CORE_CONFIG).v

OBJ_CORE_RTL_D = $(OBJ_CORE_DIR)/$(CORE_TOP).$(CORE_CONFIG).d

OBJ_CORE_RTL_TB_CPP = $(OBJ_CORE_DIR)/$(CORE_TOP).$(CORE_CONFIG).tb.cpp

OBJ_CORE_RTL_PRM = $(OBJ_CORE_DIR)/$(CORE_TOP).$(CORE_CONFIG).prm

OBJ_CORE_RTL_H = \
	$(OBJ_CORE_DIR)/$(CORE_TOP).$(CORE_CONFIG).define.h \
	$(CORE_DIR)/csrc/verilator.h

OBJ_CORE_RTL_C = \
	$(CORE_DIR)/csrc/emulator.cc \
	$(CORE_DIR)/csrc/mm.cc \
	$(CORE_DIR)/csrc/mm_dramsim2.cc

OBJ_CORE_RTL_I = \
	$(OBJ_TOOLS_DIR)/dramsim2/include/plsi-include.stamp \
	$(OBJ_TOOLS_DIR)/riscv-tools/include/plsi-include.stamp \
	$(OBJ_CORE_DIR)/$(CORE_TOP).$(CORE_CONFIG).prm.h

OBJ_CORE_RTL_O = \
	$(OBJ_TOOLS_DIR)/dramsim2/libdramsim.so \
	$(OBJ_TOOLS_DIR)/riscv-tools/lib/libfesvr.so
