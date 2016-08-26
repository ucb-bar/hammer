# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

include $(SOC_SIMULATOR_ADDON)/_rules.mk

ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_SOC_DIR)/vcs-rules.mk
$(OBJ_SOC_DIR)/vcs-rules.mk: $(SOC_SIMULATOR_ADDON)/tools/generate-rules
	mkdir -p $(dir $@)
	$< --output $@ --upper SOC --lower soc
endif
