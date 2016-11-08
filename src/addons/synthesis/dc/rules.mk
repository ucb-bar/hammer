# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# This rule is capable of producing all the various output files from DC after
# DC has successfully run.
$(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.ucli \
$(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.tab \
$(OBJ_SYN_MAPPED_V): $(OBJ_SYN_DIR)/synopsys-dc.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $(OBJ_SYN_DIR)/synopsys-dc-workdir/results/$(notdir $@) $@

# DC produces a lot of outputs, runs for a long time, and is kind of flaky
# about producing arbitrary outputs.  Rather than relying on DC's output files
# for dependency resolution we instead.
$(OBJ_SYN_DIR)/synopsys-dc.stamp: \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/run-synthesis) \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/find-regs.tcl) \
		$(OBJ_MAP_RTL_V) \
		$(OBJ_SYN_SYN_FILES) $(OBJ_SYN_DB_FILES) \
		$(TECHNOLOGY_MILKYWAY_LIB_IN_DIRS) \
		$(TECHNOLOGY_TLUPLUS_FILES) $(OBJ_SYN_TLUPLUS_FILES) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar \
		$(DC_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) -- $(abspath $<) --top $(SYN_TOP) --output_dir $(abspath $(dir $@))/synopsys-dc-workdir $(abspath $^)
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
