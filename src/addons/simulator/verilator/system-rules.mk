# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(SYSTEM_SIMULATOR_ADDON)/_rules.mk

include $(OBJ_SYSTEM_DIR)/verilator-rules.mk
$(OBJ_SYSTEM_DIR)/verilator-rules.mk: $(SYSTEM_SIMULATOR_ADDON)/tools/generate-makefrag
	mkdir -p $(dir $@)
	$< --output $@ --upper SYSTEM --lower system
