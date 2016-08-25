# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

$(OBJ_CORE_DIR)/rocketchip-files.stamp: $(shell find $(CORE_DIR) -iname "*.scala")
	mkdir -p $(OBJ_CORE_DIR)/rocket-chip
	rsync -a --delete $(CORE_DIR)/ $(OBJ_CORE_DIR)/rocket-chip/
	touch $@

$(OBJ_CORE_DIR)/rocket-chip/src/main/scala/%: $(CORE_ADDON_DIR)/% $(OBJ_CORE_DIR)/rocketchip-files.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $< $@

# When we run Rocket Chip all the outputs come from a single SBT run.  I'm
# abstracting all this away from the addon by running the Rocket Chip Makefile
# because upstream keeps changing how these outputs get generated.  In order to
# make sure I have proper dependencies for everything, I then go ahead and copy
# the files that are allowed to be used by the rest of the core out after
# running SBT (the .stamp file).
$(OBJ_CORE_DIR)/$(CORE_SIM_TOP).$(CORE_CONFIG).vsim.stamp: $(OBJ_CORE_DIR)/rocketchip-files.stamp $(CORE_ADDON_FILES)
	+$(SCHEDULER_CMD) --make -- $(MAKE) MODEL=$(CORE_SIM_TOP) CONFIG=$(CORE_CONFIG) RISCV=unused SUITE=RocketSuite -C $(OBJ_CORE_DIR)/rocket-chip/vsim verilog || (rm -rf $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(CORE_SIM_TOP).$(CORE_CONFIG).v && exit 1)
	mkdir -p $(dir $@)
	if [[ "$$(cat $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(CORE_SIM_TOP).$(CORE_CONFIG).v | wc -l)" == "0" ]]; then echo "empty Verilog from FIRRTL"; rm -rf $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/; exit 1; fi
	touch $@

$(RC_OBJ_CORE_RTL_V) $(RC_OBJ_CORE_RTL_D): $(OBJ_CORE_DIR)/$(CORE_SIM_TOP).$(CORE_CONFIG).vsim.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(notdir $@) $@

# The actual list of tests is produced from Rocket Chip by some build process.
# This isn't quite in a format I can understand, so it gets post-processed by a
# little bash script.
ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_CORE_TESTS_MK)
$(RC_OBJ_CORE_TESTS_MK): src/addons/core-generator/rocket-chip/tools/d2mk $(OBJ_CORE_RTL_D)
	+$< $(filter $(OBJ_CORE_DIR)/%,$^) -o $@
endif

# We need to have built the RISC-V tools in order to build the simulator.
# There are two rules here: one to build the tools, and another to install the
# include stamp so the simulator can find the various directories.
$(OBJ_TOOLS_DIR)/riscv-tools/include/plsi-include.stamp: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp
	touch $@

$(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp: src/addons/core-generator/rocket-chip/tools/build-toolchain $(find $(CORE_DIR)/riscv-tools -iname "*.S" -or -iname "*.cc")
	+$(SCHEDULER_CMD) -- $< -o $(abspath $@) --tools-dir $(OBJ_CORE_DIR)/rocket-chip/riscv-tools

$(OBJ_TOOLS_DIR)/riscv-tools/lib/libfesvr.so: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp

$(OBJ_TOOLS_DIR)/riscv-tests/rv%: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_TOOLS_DIR)/riscv-tools/riscv64-unknown-elf/share/riscv-tests/isa/$(notdir $@) $@

$(OBJ_TOOLS_DIR)/riscv-tests/%.riscv: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_TOOLS_DIR)/riscv-tools/riscv64-unknown-elf/share/riscv-tests/benchmarks/$(notdir $@) $@
