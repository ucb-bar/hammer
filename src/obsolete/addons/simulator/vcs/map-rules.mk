# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(MAP_SIMULATOR_ADDON)/_rules.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_MAP_DIR)/vcs-rules.mk
$(OBJ_MAP_DIR)/vcs-rules.mk: $(MAP_SIMULATOR_ADDON)/tools/generate-rules
	mkdir -p $(dir $@)
	$< --output $@ --upper MAP --lower map --vtype RTL
endif
