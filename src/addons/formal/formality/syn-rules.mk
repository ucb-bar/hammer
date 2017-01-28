# See LICENSE for details

check-syn: $(CHECK_SYN_DIR)/formality-$(MAP_TOP)-$(SYN_TOP).out

$(CHECK_SYN_DIR)/formality-$(MAP_TOP)-$(SYN_TOP).out: \
		$(SYN_FORMAL_ADDON)/run-formality \
		$(OBJ_MAP_RTL_V) \
		$(OBJ_SYN_MAPPED_V) \
		$(TECHNOLOGY_VERILOG_FILES) \
		$(TECHNOLOGY_CCS_LIBRARY_FILES)
	mkdir -p $(dir $@)
	$(SCHEDULER_CMD) -- $(CMD_PTEST) --test $(abspath $<) --out $(abspath $@) --args $(abspath $(FORMALITY_BIN)) --dc-dir $(abspath $(OBJ_SYN_DIR)/synopsys-dc-workdir) $(if $(FORMALITY_NO_VERIFY),--no-verify)
