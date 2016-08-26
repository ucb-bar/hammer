# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(CORE_SIMULATOR_ADDON)/_vars.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_CORE_DIR)/vcs-vars.mk
$(OBJ_CORE_DIR)/vcs-vars.mk: $(CORE_SIMULATOR_ADDON)/tools/generate-vars
	mkdir -p $(dir $@)
	$< --output $@ --upper CORE --lower core
endif
