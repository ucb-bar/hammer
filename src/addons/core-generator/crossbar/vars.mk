# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

CORE_TOP = AXI4XBar
CORE_ADDON_DIR = $(CORE_GENERATOR_ADDON)/src

OBJ_CORE_RTL_D =
OBJ_CORE_RTL_TB_CPP =
OBJ_CORE_RTL_PRM =
OBJ_CORE_RTL_H =
OBJ_CORE_RTL_C = $(CORE_GENERATOR_ADDON)/csrc/$(CORE_TOP).$(CORE_CONFIG).cc
OBJ_CORE_RTL_I =
OBJ_CORE_RTL_O =
OBJ_CORE_TESTS_MK = $(OBJ_CORE_DIR)/core-crossbar/empty-tests.mk

include src/addons/core-generator/rocket-chip/vars.mk
