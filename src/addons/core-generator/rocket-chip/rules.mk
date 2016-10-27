# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

$(OBJ_CORE_DIR)/plsi-generated/rocket-chip-base.stamp: \
		$(shell find $(CORE_DIR) -iname "*.scala")
	@mkdir -p $(dir $@)
	mkdir -p $(OBJ_CORE_DIR)/rocket-chip
	rsync -a --delete $(CORE_DIR)/ $(OBJ_CORE_DIR)/rocket-chip/
	mkdir -p $(OBJ_CORE_DIR)/rocket-chip/src/main/scala/
	date > $@

# If you add directories to this variable, they'll be copied to rocket-chip/
# and added to ROCKETCHIP_ADDONS
ifneq ($(RC_CORE_ADDON_DIRS),)
$(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp: $(shell find $(RC_CORE_ADDON_DIRS) -type f)
endif

# If you add directories to this variable, they'll be copied to rocket-chip/
# but won't be added to ROCKETCHIP_ADDONS
ifneq ($(RC_CORE_OVERLAY_DIR),)
$(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp: $(shell find $(RC_CORE_OVERLAY_DIR) -type f)
endif

$(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp: $(OBJ_CORE_DIR)/plsi-generated/rocket-chip-base.stamp
	@mkdir -p $(dir $@)
ifneq ($(RC_CORE_ADDON_DIRS),)
	cp --reflink=auto -r $(RC_CORE_ADDON_DIRS) $(OBJ_CORE_DIR)/rocket-chip/
endif
ifneq ($(RC_CORE_OVERLAY_DIR),)
	cp --reflink=auto -r $(RC_CORE_OVERLAY_DIR)/* $(OBJ_CORE_DIR)/rocket-chip/
endif
	date > $@

# When we run Rocket Chip all the outputs come from a single SBT run.  I'm
# abstracting all this away from the addon by running the Rocket Chip Makefile
# because upstream keeps changing how these outputs get generated.  In order to
# make sure I have proper dependencies for everything, I then go ahead and copy
# the files that are allowed to be used by the rest of the core out after
# running SBT (the .stamp file).
$(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).vsim.stamp: $(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp
	@mkdir -p $(dir $@)
	+$(SCHEDULER_CMD) --make -- $(MAKE) ROCKETCHIP_ADDONS="$(RC_CORE_ADDONS) $(notdir $(RC_CORE_ADDON_DIRS))" MODEL=$(CORE_SIM_TOP) CONFIG=$(CORE_CONFIG) RISCV=unused SUITE=RocketSuite -C $(OBJ_CORE_DIR)/rocket-chip/vsim verilog || (rm -rf $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(CORE_SIM_TOP).$(CORE_CONFIG).v && exit 1)
	mkdir -p $(dir $@)
	touch $@

$(OBJ_CORE_DIR)/plsi-generated/model.vh:
	@mkdir -p $(dir $@)
	echo '`define MODEL $(CORE_SIM_TOP)' > $@

$(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).v: $(CMD_FIRRTL_GENERATE_HARNESS) $(RC_OBJ_CORE_RTL_FIR)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %.fir,$^)) -o $(abspath $@) --syn-top $(CORE_TOP) --harness-top $(CORE_SIM_TOP)

$(OBJ_CORE_DIR)/plsi-generated/$(CORE_TOP).$(CORE_CONFIG).%: $(CMD_FIRRTL_GENERATE_TOP) $(RC_OBJ_CORE_RTL_FIR)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %.fir,$^)) -o $(abspath $@) --syn-top $(CORE_TOP) --harness-top $(CORE_SIM_TOP)

$(RC_OBJ_CORE_RTL_FIR) \
$(RC_OBJ_CORE_RTL_D) \
$(RC_OBJ_CORE_MEMORY_CONF) : \
		$(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).vsim.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(notdir $@) $@

# The Rocket Chip SRAM .conf file is funky and implicitly encodes a lot of
# information.  To avoid having this propogate the the rest of the tools I
# convert it into a saner macro configuration file, which has the advantage of
# also containing information for non-SRAM macro types.
$(RC_OBJ_CORE_MACROS): \
		src/addons/core-generator/rocket-chip/tools/generate-macros \
		$(RC_OBJ_CORE_MEMORY_CONF) \
		$(CMD_PSON2JSON)
	@mkdir -p $(dir $@)
	$< -o $@ $^

$(RC_OBJ_CORE_SIM_MACRO_FILES): $(CMD_PCAD_MACRO_COMPILER) $(RC_OBJ_CORE_MACROS)
	$< -m $(filter %.macros.json,$^) -v $@

# The actual list of tests is produced from Rocket Chip by some build process.
# This isn't quite in a format I can understand, so it gets post-processed by a
# little bash script.
ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_CORE_TESTS_MK)
$(OBJ_CORE_DIR)/plsi-generated/tests-$(CORE_SIM_CONFIG).mk: src/addons/core-generator/rocket-chip/tools/d2mk $(OBJ_CORE_RTL_D)
	+$< $(filter $(OBJ_CORE_DIR)/%,$^) -o $@ --config $(CORE_SIM_CONFIG)
endif

$(OBJ_CORE_DIR)/plsi-generated/tests-%.mk: src/addons/core-generator/rocket-chip/src/tests-*.mk
	mkdir -p $(dir $@)
	cat $^ > $@

# We need to have built the RISC-V tools in order to build the simulator.
# There are two rules here: one to build the tools, and another to install the
# include stamp so the simulator can find the various directories.
$(OBJ_CORE_DIR)/plsi-generated/tools-copy.stamp: \
		$(shell find $(CORE_DIR)/riscv-tools -iname "*.S" -or -iname "*.cc")
	@mkdir -p $(dir $@)
	mkdir -p $(OBJ_CORE_DIR)/riscv-tools
	rsync -a --delete $(CORE_DIR)/riscv-tools/ $(OBJ_CORE_DIR)/riscv-tools/
	date > $@

$(OBJ_CORE_DIR)/riscv-tools-install/include/plsi-include.stamp: $(OBJ_CORE_DIR)/plsi-generated/tools-build.stamp
	@mkdir -p $(dir $@)
	date > $@

.PHONY: riscv-tools
riscv-tools: $(OBJ_CORE_DIR)/plsi-generated/tools-build.stamp

$(OBJ_CORE_DIR)/plsi-generated/tools-build.stamp: \
		src/addons/core-generator/rocket-chip/tools/build-toolchain \
		$(OBJ_CORE_DIR)/plsi-generated/tools-copy.stamp \
		$(CMD_GCC) $(CMD_GXX)
	@mkdir -p $(dir $@)
	+$(SCHEDULER_CMD) -- $< --output-dir $(abspath $(OBJ_CORE_DIR)/riscv-tools-install) --tools-dir $(abspath $(OBJ_CORE_DIR)/riscv-tools) --cc $(abspath $(CMD_GCC)) --cxx $(abspath $(CMD_GXX))
	date > $@

$(OBJ_CORE_DIR)/riscv-tools-install/lib/libfesvr.so: $(OBJ_CORE_DIR)/plsi-generated/tools-build.stamp
	touch $@

$(OBJ_CORE_DIR)/riscv-tests/rv%: $(OBJ_CORE_DIR)/plsi-generated/tools-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/riscv-tools-install/riscv64-unknown-elf/share/riscv-tests/isa/$(notdir $@) $@

$(OBJ_CORE_DIR)/riscv-tests/%.riscv: $(OBJ_CORE_DIR)/plsi-generated/tools-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/riscv-tools-install/riscv64-unknown-elf/share/riscv-tests/benchmarks/$(notdir $@) $@
