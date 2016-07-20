# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(CHIP_SIMULATOR_ADDON)/_rules.mk

include $(OBJ_CHIP_DIR)/verilator-rules.mk
$(OBJ_CHIP_DIR)/verilator-rules.mk: $(CHIP_SIMULATOR_ADDON)/tools/generate-makefrag
	mkdir -p $(dir $@)
	$< --output $@ --upper CHIP --lower chip
