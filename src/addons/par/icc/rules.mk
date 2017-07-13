# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# Copy force_regs from DC
$(OBJ_PAR_DIR)/generated/$(PAR_TOP).force_regs.ucli \
$(OBJ_PAR_DIR)/generated/$(PAR_TOP).force_regs.tab: \
$(OBJ_PAR_DIR)/%: $(OBJ_SYN_DIR)/%
	@mkdir -p $(dir $@)
	cp --reflink=auto $< $@

# This rule is capable of producing all the various output files from ICC after
# ICC has successfully run.
$(OBJ_PAR_ROUTED_V): $(OBJ_PAR_DIR)/synopsys-icc.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $(OBJ_PAR_DIR)/synopsys-icc-workdir/results/$(notdir $@) $@

# ICC produces a lot of outputs, runs for a long time, and is kind of flaky
# about producing arbitrary outputs.  Rather than relying on ICC's output files
# for dependency resolution we instead.
$(OBJ_PAR_DIR)/synopsys-icc.stamp: \
		$(abspath $(PAR_TOOL_ADDON)/tools/run-par) \
		$(abspath $(PAR_TOOL_ADDON)/tools/find-regs.tcl) \
		$(OBJ_PAR_DIR)/generated/$(PAR_TOP).floorplan.json \
		$(OBJ_SYN_MAPPED_V) \
		$(OBJ_SYN_MAPPED_SDC) \
		$(OBJ_PAR_PAR_FILES) \
		$(OBJ_PAR_DB_FILES) \
		$(OBJ_PAR_MW_FILES) \
		$(TECHNOLOGY_MILKYWAY_LIB_IN_DIRS) \
		$(TECHNOLOGY_TLUPLUS_FILES) $(OBJ_PAR_TLUPLUS_FILES) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(TECHNOLOGY_NLDM_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/ICC-RM_$(ICC_VERSION).tar \
		$(PLSI_CAD_CONFIG_FILE) \
		$(TECHNOLOGY_JSON) \
		$(PLSI_CMD_GET_CONFIG) \
		$(OBJ_CONFIG_DB) \
		$(TECHNOLOGY_ICV_DRC_METAL_FILL_RULESET) \
		$(TECHNOLOGY_ICV_SIGNOFF_DRC_RULESET) \
		$(OBJ_TECHNOLOGY_MACRO_LIBRARY) \
		$(CMD_PCAD_LIST_MACROS) \
		$(ICV_BIN) \
		$(ICC_BIN)
	@mkdir -p $(dir $@)
	PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $(SCHEDULER_CMD) -- $(abspath $<) --top $(PAR_TOP) --output_dir $(abspath $(dir $@))/synopsys-icc-workdir $(abspath $^)
	date > $@

# Convert LEF files to Milky Way databases for ICC
$(OBJ_PAR_MW_FILES): \
		$(PAR_TOOL_ADDON)/tools/lef2mw \
		$(filter %.lef,$(OBJ_SYN_SYN_FILES)) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(MILKYWAY_BIN)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) $(abspath $(filter %/$(notdir $(patsubst %/lib,%,$@)),$^)) -o $(abspath $@) $(abspath $(filter-out %.lef,$^))

# FIXME: All this floorplan stuff is garbage, I really need to be doing it
# inside PCAD instead.  I'm too lazy right now...
$(OBJ_PAR_DIR)/synopsys-icc-macros.stamp: \
		$(abspath $(PAR_TOOL_ADDON)/tools/list-macros-to-floorplan) \
		$(abspath $(PAR_TOOL_ADDON)/tools/find-regs.tcl) \
		$(OBJ_SYN_MAPPED_V) \
		$(OBJ_SYN_MAPPED_SDC) \
		$(OBJ_PAR_PAR_FILES) \
		$(OBJ_PAR_DB_FILES) \
		$(OBJ_PAR_MW_FILES) \
		$(TECHNOLOGY_MILKYWAY_LIB_IN_DIRS) \
		$(TECHNOLOGY_TLUPLUS_FILES) $(OBJ_PAR_TLUPLUS_FILES) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(TECHNOLOGY_NLDM_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/ICC-RM_$(ICC_VERSION).tar \
		$(PLSI_CAD_CONFIG_FILE) \
		$(TECHNOLOGY_JSON) \
		$(PLSI_CMD_GET_CONFIG) \
		$(OBJ_CONFIG_DB) \
		$(ICV_BIN) \
		$(ICC_BIN)
	@mkdir -p $(dir $@)
	PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $(SCHEDULER_CMD) -- $(abspath $<) --top $(PAR_TOP) --output_dir $(abspath $(dir $@))/synopsys-icc-macros-workdir $(abspath $^)
	date > $@

$(OBJ_PAR_DIR)/generated/$(PAR_TOP).macros.out: $(OBJ_PAR_DIR)/synopsys-icc-macros.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $(OBJ_PAR_DIR)/synopsys-icc-macros-workdir/results/$(notdir $@) $@

$(OBJ_PAR_DIR)/generated/$(PAR_TOP).floorplan.json: \
		$(PAR_TOOL_ADDON)/tools/generate-floorplan-json \
		$(OBJ_PAR_DIR)/generated/$(PAR_TOP).macros.out
	# Don't let the rule fail if we are not using the oldplsi floorplan_mode
	if [ ! "$(shell $(PLSI_CMD_GET_CONFIG) -e $(OBJ_CONFIG_DB) par.icc.floorplan_mode)" == "oldplsi" ]; then \
		echo "{}" > $@; \
	else \
		PATH="$(abspath $(dir $(CMD_PYTHON3))):$(PATH)" $(abspath $<) --macros $(filter %.macros.out,$^) --rtl_top $(SYN_TOP) --config $(PAR_CONFIG) -o $@; \
	fi
