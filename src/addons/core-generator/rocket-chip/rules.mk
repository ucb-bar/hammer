# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

$(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp: $(shell find $(CORE_DIR) -iname "*.scala")
	@mkdir -p $(dir $@)
	mkdir -p $(OBJ_CORE_DIR)/rocket-chip
	rsync -a --delete $(CORE_DIR)/ $(OBJ_CORE_DIR)/rocket-chip/
	touch $@

$(OBJ_CORE_DIR)/rocket-chip/src/main/scala/%: $(CORE_ADDON_DIR)/% $(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp
	@mkdir -p $(dir $@)
	cp --reflink=auto $< $@

# When we run Rocket Chip all the outputs come from a single SBT run.  I'm
# abstracting all this away from the addon by running the Rocket Chip Makefile
# because upstream keeps changing how these outputs get generated.  In order to
# make sure I have proper dependencies for everything, I then go ahead and copy
# the files that are allowed to be used by the rest of the core out after
# running SBT (the .stamp file).
$(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).vsim.stamp: $(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp $(CORE_ADDON_FILES)
	@mkdir -p $(dir $@)
	+$(SCHEDULER_CMD) --make -- $(MAKE) MODEL=$(CORE_SIM_TOP) CONFIG=$(CORE_CONFIG) RISCV=unused SUITE=RocketSuite -C $(OBJ_CORE_DIR)/rocket-chip/vsim verilog || (rm -rf $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(CORE_SIM_TOP).$(CORE_CONFIG).v && exit 1)
	mkdir -p $(dir $@)
	touch $@

$(OBJ_CORE_FIRRTL_HARNESS_CMD) $(OBJ_CORE_FIRRTL_TOP_CMD): $(shell find $(CORE_DIR)/firrtl -type f) $(shell find src/addons/core-generator/rocket-chip/src/firrtl -type f) $(CMD_SBT)
	@mkdir -p $(dir $@)
	rsync -a --delete $(CORE_DIR)/firrtl $(dir $@)
	cp -a --reflink=auto src/addons/core-generator/rocket-chip/src/firrtl/* $(dir $@)
	sed 's/@@TOP_NAME_LOWER@@/$(shell echo $(notdir $@) | tr A-Z a-z)/g' -i $(dir $@)/project/build.scala
	sed 's/@@TOP_NAME_UPPER@@/$(shell echo $(notdir $@) | tr A-Z A-Z)/g' -i $(dir $@)/project/build.scala
	rm -f $@
	echo "cd $(dir $@)" >> $@
	echo "set -x" >> $@
	echo 'true | $(abspath $(CMD_SBT)) "run-main $(notdir $@) $$*"' >> $@
	chmod +x $@

$(OBJ_CORE_DIR)/plsi-generated/model.vh:
	@mkdir -p $(dir $@)
	echo '`define MODEL $(CORE_SIM_TOP)' > $@

$(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).v: $(OBJ_CORE_FIRRTL_HARNESS_CMD) $(RC_OBJ_CORE_RTL_FIR)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %.fir,$^)) -o $(abspath $@) --syn-top $(CORE_TOP) --harness-top $(CORE_SIM_TOP)

$(RC_OBJ_CORE_RTL_V): $(OBJ_CORE_FIRRTL_TOP_CMD) $(RC_OBJ_CORE_RTL_FIR)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %.fir,$^)) -o $(abspath $@) --syn-top $(CORE_TOP) --harness-top $(CORE_SIM_TOP)

$(RC_OBJ_CORE_RTL_FIR) $(RC_OBJ_CORE_RTL_D): $(OBJ_CORE_DIR)/plsi-generated/$(CORE_SIM_TOP).$(CORE_CONFIG).vsim.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/rocket-chip/vsim/generated-src/$(notdir $@) $@

# The actual list of tests is produced from Rocket Chip by some build process.
# This isn't quite in a format I can understand, so it gets post-processed by a
# little bash script.
ifeq ($(filter $(MAKECMDGOALS),clean distclean),)
-include $(OBJ_CORE_TESTS_MK)
$(OBJ_CORE_DIR)/plsi-generated/tests-default.mk: src/addons/core-generator/rocket-chip/tools/d2mk $(OBJ_CORE_RTL_D)
	+$< $(filter $(OBJ_CORE_DIR)/%,$^) -o $@
endif

$(OBJ_CORE_DIR)/plsi-generated/tests-%.mk: src/addons/core-generator/rocket-chip/src/tests-*.mk
	mkdir -p $(dir $@)
	cat $^ > $@

# We need to have built the RISC-V tools in order to build the simulator.
# There are two rules here: one to build the tools, and another to install the
# include stamp so the simulator can find the various directories.
$(OBJ_CORE_DIR)/riscv-tools/include/plsi-include.stamp: $(OBJ_CORE_DIR)/riscv-tools/plsi-build.stamp
	touch $@

$(OBJ_CORE_DIR)/riscv-tools/plsi-build.stamp: \
		src/addons/core-generator/rocket-chip/tools/build-toolchain \
		$(find $(OBJ_CORE_DIR)/rocket-chip/riscv-tools -iname "*.S" -or -iname "*.cc") \
		$(OBJ_CORE_DIR)/plsi-generated/rocket-chip.stamp \
		$(CMD_GCC) $(CMD_GXX)
	+$(SCHEDULER_CMD) -- $< -o $(abspath $@) --tools-dir $(OBJ_CORE_DIR)/rocket-chip/riscv-tools --cc $(abspath $(CMD_GCC)) --cxx $(abspath $(CMD_GXX))

$(OBJ_CORE_DIR)/riscv-tools/lib/libfesvr.so: $(OBJ_CORE_DIR)/riscv-tools/plsi-build.stamp

$(OBJ_CORE_DIR)/riscv-tests/rv%: $(OBJ_CORE_DIR)/riscv-tools/plsi-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/riscv-tools/riscv64-unknown-elf/share/riscv-tests/isa/$(notdir $@) $@

$(OBJ_CORE_DIR)/riscv-tests/%.riscv: $(OBJ_CORE_DIR)/riscv-tools/plsi-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_CORE_DIR)/riscv-tools/riscv64-unknown-elf/share/riscv-tests/benchmarks/$(notdir $@) $@
