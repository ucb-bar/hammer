# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(PAR_SIMULATOR_ADDON)/_rules.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_PAR_DIR)/vcs-rules.mk
$(OBJ_PAR_DIR)/vcs-rules.mk: $(PAR_SIMULATOR_ADDON)/tools/generate-rules
	mkdir -p $(dir $@)
	$< --output $@ --upper PAR --lower par --vtype ROUTED
endif
