# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

SYSTEM_TOP = Top

OBJ_SYSTEM_RTL_D = $(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).d

OBJ_SYSTEM_RTL_TB_CPP = $(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).tb.cpp

OBJ_SYSTEM_RTL_PRM = $(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).prm

OBJ_SYSTEM_RTL_H = \
	$(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).define.h

OBJ_SYSTEM_RTL_C = \
	$(SYSTEM_DIR)/csrc/emulator.cc \
	$(SYSTEM_DIR)/csrc/mm.cc \
	$(SYSTEM_DIR)/csrc/mm_dramsim2.cc

OBJ_SYSTEM_RTL_I = \
	$(OBJ_TOOLS_DIR)/dramsim2/include/plsi-include.stamp \
	$(OBJ_TOOLS_DIR)/riscv-tools/include/plsi-include.stamp \
	$(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).prm.h

OBJ_SYSTEM_RTL_O = \
	$(OBJ_TOOLS_DIR)/dramsim2/libdramsim.so \
	$(OBJ_TOOLS_DIR)/riscv-tools/lib/libfesvr.so
