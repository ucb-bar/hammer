# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

ifeq ($(GENUS_VERSION),)
$(error You must set GENUS_VERSION to be able to run Cadence GENUS)
endif

ifeq ($(CADENCE_HOME),)
$(error You must set CADENCE_HOME to be able to run Synopsys DC)
endif

GENUS_BIN = $(CADENCE_HOME)/GENUS/GENUS$(GENUS_VERSION)/bin/genus
ifeq ($(wildcard $(GENUS_BIN)),)
$(error Expected to find dc_shell at $(GENUS_BIN))
endif

ITF2ICT_BIN = $(CADENCE_HOME)/ETS/ETS$(ETS_VERSION)/share/anls/gift/bin/itf_to_ict
ifeq ($(wildcard $(ITF2ICT_BIN)),)
$(error Expected to find itf_to_ict at $(ITF2ICT_BIN))
endif

INNOVUS_BIN = $(CADENCE_HOME)/INNOVUS/INNOVUS$(INNOVUS_VERSION)/bin/innovus
ifeq ($(wildcard $(INNOVUS_BIN)),)
$(error Expected to find innovus at $(INNOVUS_BIN))
endif

SYN_TOP = $(MAP_TOP)
SYN_SIM_TOP = $(MAP_SIM_TOP)
OBJ_SYN_MAPPED_V = $(OBJ_SYN_DIR)/generated/$(SYN_TOP).mapped.v
OBJ_SYN_SIM_FILES = $(OBJ_MAP_SIM_FILES) $(TECHNOLOGY_VERILOG_FILES)

# DC flows are based on the reference methodology
ifneq ($(CADENCE_RAK_DIR),)
$(PLSI_CACHE_DIR)/cadence/rak/%: $(CADENCE_RAK_DIR)/%
	@mkdir -p $(dir $@)
	cp --reflink=auto $^ $@
else
$(PLSI_CACHE_DIR)/cadence/rak/%:
	$(error Download a Cadence RAK from <http://support.cadence.com/> and place it at $@)
endif

OBJ_SYN_CAPTBL_FILES = $(addsuffix .capTbl,$(addprefix $(OBJ_TECH_DIR)/plsi-generated/cap_table/,$(notdir $(TECHNOLOGY_ITF_FILES))))
OBJ_SYN_ICT_FILES = $(addsuffix .ict,$(addprefix $(OBJ_TECH_DIR)/plsi-generated/cap_table/,$(notdir $(TECHNOLOGY_ITF_FILES))))

OBJ_SYN_SYN_FILES = $(OBJ_MAP_SYN_FILES)
