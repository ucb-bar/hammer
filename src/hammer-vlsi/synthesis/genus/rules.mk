# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# This rule is capable of producing all the various output files from Genus after
# Genus has successfully run.
$(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.ucli \
$(OBJ_SYN_DIR)/generated/$(SYN_TOP).force_regs.tab \
$(OBJ_SYN_MAPPED_V): $(OBJ_SYN_DIR)/cadence-genus.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $(OBJ_SYN_DIR)/cadence-genus-workdir/results/$(notdir $@) $@

# Genus produces a lot of outputs, runs for a long time, and is kind of flaky
# about producing arbitrary outputs.  Rather than relying on GENUS's output files
# for dependency resolution we instead.
$(OBJ_SYN_DIR)/cadence-genus.stamp: \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/run-synthesis) \
		$(OBJ_MAP_RTL_V) \
		$(PLSI_CACHE_DIR)/cadence/rak/Genus_$(GENUS_VERSION)_CommonUI_MMMC_RAK.tar.gz \
		$(TECHNOLOGY_CCS_LIBERTY_FILES) \
		$(OBJ_SYN_TECHLEF_FILES) \
		$(TECHNOLOGY_LEF_FILES) \
		$(SYN_CONFIG_FILE) \
		$(OBJ_SYN_CAPTBL_FILES) \
		$(GENUS_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) -- $(abspath $<) --top $(SYN_TOP) --output_dir $(abspath $(dir $@))/cadence-genus-workdir $(abspath $^)
	date > $@

# Generates capTbl (capacatence files) for use in synthesis, which actually
# requires Innovus.  This is a two-step process: first the ITF files get
# converted to ICT files (for Cadence), then the ICT files get converted to
# capTbl (which takes a while).
ifneq ($(TECHNOLOGY_ITF_FILES),)
$(OBJ_SYN_CAPTBL_FILES): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/ict2capTbl) \
		$(INNOVUS_BIN) \
		$(OBJ_SYN_ICT_FILES)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< --innovus $(INNOVUS_BIN) --ict $(abspath $(filter %/$(patsubst %.capTbl,%.ict,$(notdir $@)),$^)) --output $(abspath $@)

$(OBJ_SYN_ICT_FILES): $(ITF2ICT_BIN) $(TECHNOLOGY_ITF_FILES)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- perl $< $(abspath $(filter %/$(patsubst %.ict,%,$(notdir $@)),$^)) $(abspath $@)
endif

# Cadence doesn't take .tf techfiles but instead wants them converted to .lef
# files instead.
$(OBJ_SYN_TECHLEF_FILES): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/tools/tf2lef) \
		$(INNOVUS_BIN) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< --innovus $(INNOVUS_BIN) --tf $(abspath $(filter %/$(patsubst %.tf.lef,%.tf,$(notdir $@)),$^)) --output $(abspath $@)

