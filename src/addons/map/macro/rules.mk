# The implementation of the technology mapping stage.  This produces the
# verilog for synthesis that can later be used.  It's meant to be a single
# file, so the macros are actually generated seperately.
$(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.v: \
		$(CMD_FIRRTL_MACRO_COMPILER) \
		$(OBJ_SOC_MACROS) \
		$(OBJ_TECHNOLOGY_MACRO_LIBRARY)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -v $(abspath $@) -m $(abspath $(filter %.macros.json,$^)) --syn-flops -l $(abspath $(filter %.macro_library.json,$^)) |& tee $(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.log | tail

$(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.mk: \
		src/tools/map/list-macros \
		$(OBJ_MAP_DIR)/plsi-generated/$(MAP_TOP).macros_for_synthesis.v \
		$(OBJ_TECHNOLOGY_MACRO_LIBRARY)
	@mkdir -p $(dir $@)
	$< -o $@ --mode $(patsubst $(MAP_TOP).macros_for_%.mk,%,$(notdir $@)) $^
