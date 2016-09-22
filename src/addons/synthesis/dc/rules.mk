# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

$(OBJ_SYN_MAPPED_V): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/run-synthesis) \
		$(OBJ_SOC_RTL_V) \
		$(patsubst %,%/lib,$(TECHNOLOGY_MILKYWAY_DIRS)) \
		$(TECHNOLOGY_TLUPLUS_FILES) \
		$(TECHNOLOGY_MILKYWAY_TECHFILES) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/DC-RM_$(DC_VERSION).tar \
		$(DC_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --top $(SYN_TOP) -o $(abspath $@) $(abspath $^)
