# See LICENSE for details

$(SIGNOFF_SYN_POWER_DIR)/%.out: \
		$(OBJ_SYN_DIR)/pt-power/%/stamp
	exit 1

$(OBJ_SYN_DIR)/pt-power/%/stamp: \
		$(SYN_POWER_SIGNOFF_ADDON)/tools/run-primetime \
		$(OBJ_SYN_MAPPED_V) \
		$(TRACE_SYN_DIR)/%.vpd \
		$(PRIMETIME_POWER_BIN) \
		$(VCD2SAIF_BIN) $(VPD2VCD_BIN) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/PT-RM_$(PRIMETIME_POWER_VERSION).tar \
		$(PLSI_CAD_CONFIG_FILE)
	mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --output $(abspath $@) --top $(SYN_TOP) --testbench $(TESTBENCH) $(abspath $^)

$(PLSI_CACHE_DIR)/synopsys/rm/PT-RM_$(PRIMETIME_POWER_VERSION).tar: $(SYNOPSYS_RM_DIR)/PT-RM_$(PRIMETIME_POWER_VERSION).tar
	cp --reflink=auto $< $@

ifeq ($(wildcard $(SYNOPSYS_RM_DIR)/PT-RM_$(PRIMETIME_POWER_VERSION).tar),)
$(error Expected to find PrimeTime RM at $(SYNOPSYS_RM_DIR)/PT-RM_$(PRIMETIME_POWER_VERSION).tar, downlad it)
endif
