# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(SYN_SIMULATOR_ADDON)/_vars.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_SYN_DIR)/verilator-vars.mk
$(OBJ_SYN_DIR)/verilator-vars.mk: $(SYN_SIMULATOR_ADDON)/tools/generate-vars
	mkdir -p $(dir $@)
	$< --output $@ --upper SYN --lower syn --vtype MAPPED
endif
