# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# This rule is capable of producing all the various output files from DC after
# DC has successfully run.
$(OBJ_SYN_MAPPED_V): $(OBJ_SYN_DIR)/synopsys-dc.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $(OBJ_SYN_DIR)/synopsys-dc-workdir/results/$(notdir $@) $@

# DC produces a lot of outputs, runs for a long time, and is kind of flaky
# about producing arbitrary outputs.  Rather than relying on DC's output files
# for dependency resolution we instead.
$(OBJ_SYN_DIR)/synopsys-dc.stamp: \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/run-synthesis) \
		$(OBJ_SOC_RTL_V) \
		$(patsubst %,%/lib,$(TECHNOLOGY_MILKYWAY_DIRS)) \
		$(TECHNOLOGY_TLUPLUS_FILES) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar \
		$(DC_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --top $(SYN_TOP) --output_dir $(abspath $(dir $@))/synopsys-dc-workdir $(abspath $^)
	date > $@
