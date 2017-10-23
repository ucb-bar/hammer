# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# This rule is capable of producing all the various output files from DC after
# DC has successfully run.
$(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.ucli \
$(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.tab \
$(OBJ_SYN_MAPPED_V) \
$(OBJ_SYN_MAPPED_SDC) \
: \
		$(OBJ_SYN_DIR)/synopsys-dc.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $(OBJ_SYN_DIR)/synopsys-dc-workdir/results/$(notdir $@) $@

# DC produces a lot of outputs, runs for a long time, and is kind of flaky
# about producing arbitrary outputs.  Rather than relying on DC's output files
# for dependency resolution we instead.
# TODO: autodetect and use CCS if present in place of NLDM.
# Note that often we can't have both since the file names are the same.
$(OBJ_SYN_DIR)/synopsys-dc.stamp: \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/run-synthesis) \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/find-regs.tcl) \
		$(OBJ_MAP_RTL_V) \
		$(OBJ_MAP_RTL_VHD) \
		$(OBJ_SYN_SYN_FILES) $(OBJ_SYN_DB_FILES) \
		$(TECHNOLOGY_MILKYWAY_LIB_IN_DIRS) \
		$(TECHNOLOGY_TLUPLUS_FILES) $(OBJ_SYN_TLUPLUS_FILES) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(TECHNOLOGY_NLDM_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar \
		$(PLSI_CAD_CONFIG_FILE) \
		$(TECHNOLOGY_JSON) \
		$(DC_BIN)
	@mkdir -p $(dir $@)
	PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $(SCHEDULER_CMD) --max-threads=16 -- $(abspath $<) --top $(SYN_TOP) --output_dir $(abspath $(dir $@))/synopsys-dc-workdir $(abspath $^) $(foreach arg, $(DC_COMPILE_ARGS), --compile_arg $(arg))
	date > $@

# FIXME: None of these are DC-specific, so they should probably live somewhere else.
ifneq ($(TECHNOLOGY_ITF_FILES),)
$(OBJ_SYN_TLUPLUS_FILES): $(TECHNOLOGY_ITF_FILES)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(GRDGENXO_BIN) -itf2TLUPlus -i $(realpath $(filter %/$(patsubst %.tluplus,%,$(notdir $@)),$^)) -o $(abspath $@)
endif

ifneq ($(OBJ_SYN_DB_FILES),)
$(OBJ_SYN_DB_FILES): $(SYNTHESIS_TOOL_ADDON)/tools/lib2db $(OBJ_MAP_SYN_FILES)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %/$(patsubst %.db,%,$(notdir $@)),$^)) -o $(abspath $@) --lc_shell $(abspath $(LC_BIN))
endif
