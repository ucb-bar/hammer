# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

CORE_TOP = AXI4XBar
CORE_ADDON_DIR = $(CORE_GENERATOR_ADDON)/src

OBJ_CORE_RTL_TB_CPP = $(CORE_GENERATOR_ADDON)/csrc/$(CORE_TOP).$(CORE_CONFIG).tb.cpp
OBJ_CORE_RTL_C =

include src/addons/core-generator/rocket-chip/vars.mk
