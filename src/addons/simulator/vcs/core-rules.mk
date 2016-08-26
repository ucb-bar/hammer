# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(CORE_SIMULATOR_ADDON)/_rules.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_CORE_DIR)/vcs-rules.mk
$(OBJ_CORE_DIR)/vcs-rules.mk: $(CORE_SIMULATOR_ADDON)/tools/generate-rules
	mkdir -p $(dir $@)
	$< --output $@ --upper CORE --lower core
endif
