# See LICENSE for details

$(SIGNOFF_PAR_POWER_DIR)/%.out: \
		$(OBJ_PAR_DIR)/pt-power/%/stamp
	exit 1

$(OBJ_PAR_DIR)/pt-power/%/stamp: \
		$(SYN_POWER_SIGNOFF_ADDON)/tools/run-primetime \
		$(OBJ_PAR_ROUTED_V) \
		$(TRACE_PAR_DIR)/%.vpd \
		$(PRIMETIME_POWER_BIN) \
		$(VCD2SAIF_BIN) $(VPD2VCD_BIN) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES) \
		$(PLSI_CACHE_DIR)/synopsys/rm/PT-RM_$(PRIMETIME_POWER_VERSION).tar \
		$(PLSI_CAD_CONFIG_FILE)
	mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --output $(abspath $@) --top $(PAR_TOP) --testbench $(PRIMETIME_PATH_TO_TESTBENCH) $(if $(PRIMETIME_RTL_TRACE),--rtl-trace,) $(abspath $^)
