# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

ifeq ($(ICC_VERSION),)
$(error You must set ICC_VERSION to be able to run Synopsys ICC)
endif

ifeq ($(SYNOPSYS_HOME),)
$(error You must set SYNOPSYS_HOME to be able to run Synopsys ICC)
endif

ICC_BIN = $(SYNOPSYS_HOME)/icc/$(ICC_VERSION)/bin/icc_shell
ifeq ($(wildcard $(ICC_BIN)),)
$(error Expected to find icc_shell at $(ICC_BIN))
endif

# We need StarRC in order to convert ITF files to TLU+ files, which ICC needs
# for accurate wire delays.  This is only necessary if the technology provides
# ITF files, and since lots of people don't run StarRC I shouldn't error out if
# they don't need it.
ifeq ($(TECHNOLOGY_TLUPLUS_FILES),)
ifneq ($(TECHNOLOGY_ITF_FILES),)

ifeq ($(STARRC_VERSION),)
$(error You must set STARRC_VERSION to be able to run Synopsys ICC)
endif

GRDGENXO_BIN = $(SYNOPSYS_HOME)/starrcxt/$(STARRC_VERSION)/bin/grdgenxo
ifeq ($(wildcard $(GRDGENXO_BIN)),)
$(error Expected to find grdgenxo at $(GRDGENXO_BIN))
endif

MILKYWAY_BIN = $(SYNOPSYS_HOME)/mw/$(MILKYWAY_VERSION)/bin/linux64/Milkyway
ifeq ($(wildcard $(MILKYWAY_BIN)),)
$(error Expected to find Milkyway at $(MILKYWAY_BIN))
endif

endif
endif

# We need "lc_shell" in order to convert .lib files to .db files, but for some
# reason that's not in some versions of ICC.  This allows users to specify it
# seperately.
ifneq ($(filter %.lib,$(OBJ_SYN_PAR_FILES)),)
LC_VERSION ?= $(ICC_VERSION)
LC_BIN = $(SYNOPSYS_HOME)/syn/$(LC_VERSION)/bin/lc_shell
ifeq ($(wildcard $(LC_BIN)),)
$(error Expected to find lc_shell at $(LC_BIN))
endif
endif

# ICC needs ICV to insert DRC metal fills.  The scripts say this is only
# necessary for 28nm and below, but I just have it everywhere.
ICV_BIN = $(SYNOPSYS_HOME)/icvalidator/$(ICV_VERSION)/bin/linux64/icv64
ifeq ($(wildcard $(ICV_BIN)),)
$(error Expected to find ICV at $(ICV_BIN))
endif

PAR_TOP = $(SYN_TOP)
PAR_SIM_TOP = $(SYN_SIM_TOP)
OBJ_PAR_ROUTED_V = $(OBJ_PAR_DIR)/generated/$(PAR_TOP).mapped.v
OBJ_PAR_SIM_FILES = $(OBJ_SYN_SIM_FILES) $(TECHNOLOGY_VERILOG_FILES) $(OBJ_PAR_DIR)/generated/$(PAR_TOP).force_regs.ucli $(OBJ_PAR_DIR)/generated/$(PAR_TOP).force_regs.tab
OBJ_PAR_SIM_MACRO_FILES = $(OBJ_SYN_SIM_MACRO_FILES)

# ICC flows are based on the reference methodology
ifneq ($(SYNOPSYS_RM_DIR),)
$(PLSI_CACHE_DIR)/synopsys/rm/ICC-RM_$(ICC_VERSION).tar: $(SYNOPSYS_RM_DIR)/ICC-RM_$(ICC_VERSION).tar
	@mkdir -p $(dir $@)
	cp --reflink=auto $^ $@
else
$(PLSI_CACHE_DIR)/synopsys/rm/ICC-RM_$(ICC_VERSION).tar:
	$(error Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a ICC reference methodology.  If these tarballs have been pre-downloaded, you can set SYNOPSYS_RM_DIR instead of generating them yourself.)
endif

# ICC requires TLU+ files, but some technologies only provide
# ITF files.  This rule just slurps up the ones DC converted.
# FIXME: Don't rely on DC here
OBJ_PAR_TLUPLUS_FILES = $(OBJ_SYN_TLUPLUS_FILES)
OBJ_PAR_DB_FILES = $(OBJ_SYN_DB_FILES)

# ICC requires LEF files to be converted to Milky Way databases in
# order to run place and route.
OBJ_PAR_MW_FILES = $(addsuffix /lib,$(addprefix $(OBJ_TECH_DIR)/plsi-generated/mw/,$(notdir $(filter %.lef,$(OBJ_SYN_SYN_FILES)))))

OBJ_PAR_PAR_FILES = $(filter-out %.lef,$(OBJ_SYN_SYN_FILES))

# ICC need SDC files.  There's probably a way around it, but I'm too lazy to
# deal with it for now...
ifeq ($(OBJ_SYN_MAPPED_SDC),)
$(error ICC needs a SDC file from the synthesis tool)
endif
