# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(CORE_SIMULATOR_ADDON)/_rules.mk

include $(OBJ_CORE_DIR)/verilator-rules.mk
$(OBJ_CORE_DIR)/verilator-rules.mk: $(CORE_SIMULATOR_ADDON)/tools/generate-makefrag
	mkdir -p $(dir $@)
	$< --output $@ --upper CORE --lower core
