# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# A PLSI addon for generating RTL for Rocket Chip based projects.

# These variables are used by PLSI
SYSTEM_TOP = Top

# When we run Rocket Chip all the outputs come from a single SBT run.  I'm
# abstracting all this away from the addon by running the Rocket Chip Makefile
# because upstream keeps changing how these outputs get generated.  In order to
# make sure I have proper dependencies for everything, I then go ahead and copy
# the files that are allowed to be used by the rest of the system out after
# running SBT (the .stamp file).
$(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).stamp: $(shell find $(SYSTEM_DIR) -iname "*.scala")
	$(MAKE) RISCV=unused -C $(SYSTEM_DIR)/vsim verilog
	mkdir -p $(dir $@)
	touch $@

$(OBJ_SYSTEM_RTL_V): $(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).stamp
	mkdir -p $(dir $@)
	cp -f $(SYSTEM_DIR)/vsim/generated-src/$(notdir $@) $@
