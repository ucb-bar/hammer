# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

# Vivado/Arty board files.
$(PLSI_CACHE_DIR)/distfiles/vivado-boards-$(VIVADO_BOARDS_REV).tar.gz:
	@mkdir -p $(dir $@)
	wget https://github.com/Digilent/vivado-boards/archive/$(VIVADO_BOARDS_REV).tar.gz -O $@

$(OBJ_SYN_BOARD_FILES_DIR): $(OBJ_SYN_BOARD_FILES)

$(OBJ_SYN_BOARD_FILES): \
		$(PLSI_CACHE_DIR)/distfiles/vivado-boards-$(VIVADO_BOARDS_REV).tar.gz
	@mkdir -p $(dir $@)
	mkdir -p $(dir $@)/b_files_temp
	tar zxvf $(PLSI_CACHE_DIR)/distfiles/vivado-boards-$(VIVADO_BOARDS_REV).tar.gz -C $(dir $@)/b_files_temp/
	mv $(dir $@)/b_files_temp/vivado-boards-$(VIVADO_BOARDS_REV)/new/board_files/* $(dir $@)/
	rm -r $(dir $@)/b_files_temp

	touch $@

# See vars.mk for $(OBJ_SYN_MACRO_LIB_V)
$(OBJ_SYN_MACRO_LIB_V): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/generate-macros) \
		$(OBJ_SYN_BOARD_FILES) \
		$(VIVADO_BIN)
	@mkdir -p $(dir $@)
	@mkdir -p $(OBJ_SYN_MACRO_LIB_DCP_DIR)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --top $(SYN_TOP) -o $(abspath $@) --dcp $(abspath $(OBJ_SYN_MACRO_LIB_DCP_DIR)) --board_files $(abspath $(OBJ_SYN_BOARD_FILES_DIR)) $(abspath $(VIVADO_BIN))

# Runs a vivado synthesis job
$(OBJ_SYN_POST_SYNTH_DCP): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/run-synthesis) \
		$(OBJ_MAP_RTL_V) \
		$(OBJ_SYN_MACRO_LIB_V) \
		$(VIVADO_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --top $(SYN_TOP) -o $(abspath $(OBJ_SYN_MAPPED_V)) --dcp $(abspath $@) --dcp_macro_dir $(abspath $(OBJ_SYN_MACRO_LIB_DCP_DIR)) --board_files $(abspath $(OBJ_SYN_BOARD_FILES_DIR))  $(abspath $^)

# TODO: pick a better target for this
# TODO: move place and route to another stage in the flow!
$(OBJ_SYN_MAPPED_V): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/run-par) \
		$(OBJ_MAP_RTL_V) \
		$(OBJ_SYN_MACRO_LIB_V) \
		$(OBJ_SYN_POST_SYNTH_DCP) \
		$(VIVADO_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --top $(SYN_TOP) -o $(abspath $(OBJ_SYN_MAPPED_V)) --dcp $(abspath $(OBJ_SYN_POST_SYNTH_DCP)) --board_files $(abspath $(OBJ_SYN_BOARD_FILES_DIR))  $(abspath $^)
	@echo "// Dummy placeholder for the vivado synthesis tool. The real output of the tool is in the .dcp format for Vivado." > $@
