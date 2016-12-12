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

# We need StarRC in order to convert ITF files to TLU+ files, which DC needs
# for accurate wire delays.  This is only necessary if the technology provides
# ITF files, and since lots of people don't run StarRC I shouldn't error out if
# they don't need it.
ifeq ($(TECHNOLOGY_TLUPLUS_FILES),)
ifneq ($(TECHNOLOGY_ITF_FILES),)

ifeq ($(STARRC_VERSION),)
$(error You must set STARRC_VERSION to be able to run Synopsys DC)
endif

GRDGENXO_BIN = $(SYNOPSYS_HOME)/starrcxt/$(STARRC_VERSION)/bin/grdgenxo
ifeq ($(wildcard $(GRDGENXO_BIN)),)
$(error Expected to find grdgenxo at $(GRDGENXO_BIN))
endif

endif
endif

# We need "lc_shell" in order to convert .lib files to .db files, but for some
# reason that's not in some versions of DC.  This allows users to specify it
# seperately.
ifneq ($(filter %.lib,$(OBJ_MAP_SYN_FILES)),)
LC_VERSION ?= $(DC_VERSION)
LC_BIN = $(SYNOPSYS_HOME)/syn/$(LC_VERSION)/bin/lc_shell
ifeq ($(wildcard $(LC_BIN)),)
$(error Expected to find lc_shell at $(LC_BIN))
endif
endif

SYN_TOP = $(MAP_TOP)
SYN_SIM_TOP = $(MAP_SIM_TOP)
OBJ_SYN_MAPPED_V = $(OBJ_SYN_DIR)/generated/$(SYN_TOP).mapped.v
OBJ_SYN_SIM_FILES = $(OBJ_MAP_SIM_FILES) $(TECHNOLOGY_VERILOG_FILES) $(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.ucli $(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.tab
OBJ_SYN_SIM_MACRO_FILES = $(OBJ_MAP_SIM_MACRO_FILES)

# DC flows are based on the reference methodology
ifneq ($(SYNOPSYS_RM_DIR),)
$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar: $(SYNOPSYS_RM_DIR)/DC-RM_$(DC_VERSION).tar
	@mkdir -p $(dir $@)
	cp --reflink=auto $^ $@
else
$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar:
	$(error Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a DC reference methodology.  If these tarballs have been pre-downloaded, you can set SYNOPSYS_RM_DIR instead of generating them yourself.)
endif

# DC requires TLU+ files, but some technologies only provide
# ITF files.  This rule converts them.
# FIXME: This shouldn't be DC specific, it'll use ICC as well.
ifeq ($(TECHNOLOGY_TLUPLUS_FILES),)
OBJ_SYN_TLUPLUS_FILES = $(addsuffix .tluplus,$(addprefix $(OBJ_TECH_DIR)/plsi-generated/tluplus/,$(notdir $(TECHNOLOGY_ITF_FILES))))
endif

# DC can't handle raw .lib files, but instead expected them to be converted to
# .db files.
OBJ_SYN_DB_FILES = $(addsuffix .db,$(addprefix $(OBJ_TECH_DIR)/plsi-generetad/db/,$(notdir $(filter %.lib,$(OBJ_MAP_SYN_FILES)))))

OBJ_SYN_SYN_FILES = $(filter-out %.lib,$(OBJ_MAP_SYN_FILES))
