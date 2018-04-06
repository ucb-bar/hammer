# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(PAR_SIMULATOR_ADDON)/_vars.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_PAR_DIR)/vcs-vars.mk
$(OBJ_PAR_DIR)/vcs-vars.mk: $(PAR_SIMULATOR_ADDON)/tools/generate-vars
	mkdir -p $(dir $@)
	$< --output $@ --upper PAR --lower par --vtype ROUTED
endif
