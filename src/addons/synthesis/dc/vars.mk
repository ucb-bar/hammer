# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

ifeq ($(DC_VERSION),)
$(error You must set DC_VERSION to be able to run Synopsys DC)
endif

ifeq ($(SYNOPSYS_HOME),)
$(error You must set SYNOPSYS_HOME to be able to run Synopsys DC)
endif

DC_BIN = $(SYNOPSYS_HOME)/syn/$(DC_VERSION)/bin/dc_shell
ifeq ($(wildcard $(DC_BIN)),)
$(error Expected to find dc_shell at $(DC_BIN))
endif

SYN_TOP = $(MAP_TOP)
SYN_SIM_TOP = $(MAP_SIM_TOP)
OBJ_SYN_MAPPED_V = $(OBJ_SYN_DIR)/generated/$(SYN_TOP).mapped.v
OBJ_SYN_SIM_FILES = $(OBJ_MAP_SIM_FILES) $(TECHNOLOGY_VERILOG_FILES) $(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.ucli $(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.tab

# DC flows are based on the reference methodology
ifneq ($(SYNOPSYS_RM_DIR),)
$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar: $(SYNOPSYS_RM_DIR)/DC-RM_$(DC_VERSION).tar
	@mkdir -p $(dir $@)
	cp --reflink=auto $^ $@
else
$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar:
	$(error Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a DC reference methodology.  If these tarballs have been pre-downloaded, you can set SYNOPSYS_RM_DIR instead of generating them yourself.)
endif
