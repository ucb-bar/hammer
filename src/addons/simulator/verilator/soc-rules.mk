# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(SOC_SIMULATOR_ADDON)/_rules.mk

include $(OBJ_SOC_DIR)/verilator-rules.mk
$(OBJ_SOC_DIR)/verilator-rules.mk: $(SOC_SIMULATOR_ADDON)/tools/generate-makefrag
	mkdir -p $(dir $@)
	$< --output $@ --upper SOC --lower soc
