# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(MAP_SIMULATOR_ADDON)/_vars.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_MAP_DIR)/icarus-vars.mk
$(OBJ_MAP_DIR)/icarus-vars.mk: $(MAP_SIMULATOR_ADDON)/tools/generate-vars
	mkdir -p $(dir $@)
	$< --output $@ --upper MAP --lower map --vtype RTL
endif
