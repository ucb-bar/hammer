# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(SYN_SIMULATOR_ADDON)/_rules.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_SYN_DIR)/icarus-rules.mk
$(OBJ_SYN_DIR)/icarus-rules.mk: $(SYN_SIMULATOR_ADDON)/tools/generate-rules
	mkdir -p $(dir $@)
	$< --output $@ --upper SYN --lower syn --vtype MAPPED
endif
