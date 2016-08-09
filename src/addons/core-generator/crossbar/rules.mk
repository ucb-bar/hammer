# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# The crossbar can't actually run any tests itself, so instead I'm 
$(OBJ_CORE_DIR)/core-crossbar/empty-tests.mk:
	@mkdir -p $(dir $@)
	touch $@

include src/addons/core-generator/rocket-chip/rules.mk
