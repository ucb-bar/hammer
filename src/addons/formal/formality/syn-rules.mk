# See LICENSE for details

check-syn: $(CHECK_SYN_DIR)/formality-$(MAP_TOP)-$(SYN_TOP).out

$(CHECK_SYN_DIR)/formality-$(MAP_TOP)-$(SYN_TOP).out: \
		$(SYN_FORMAL_ADDON)/run-formality \
		$(OBJ_MAP_RTL_V) \
		$(OBJ_SYN_MAPPED_V) \
		$(TECHNOLOGY_VERILOG_FILES) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES)
	mkdir -p $(dir $@)
	$(SCHEDULER_CMD) -- $(CMD_PTEST) --test $(abspath $<) --out $(abspath $@) --args --reference-verilog $(abspath $(OBJ_MAP_RTL_V)) --implementation-verilog $(abspath $(OBJ_SYN_MAPPED_V)) --reference-top $(MAP_TOP) --implementation-top $(SYN_TOP) $(abspath $(FORMALITY_BIN)) $(abspath $(TECHNOLOGY_VERILOG_FILES)) $(abspath $(TECHNOLOGY_CCS_LIBRARY_FILES))
