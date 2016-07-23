# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# When we run Rocket Chip all the outputs come from a single SBT run.  I'm
# abstracting all this away from the addon by running the Rocket Chip Makefile
# because upstream keeps changing how these outputs get generated.  In order to
# make sure I have proper dependencies for everything, I then go ahead and copy
# the files that are allowed to be used by the rest of the system out after
# running SBT (the .stamp file).
$(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).vsim.stamp: $(shell find $(SYSTEM_DIR) -iname "*.scala")
	+$(SCHODULER_CMD) $(MAKE) RISCV=unused SUITE=RocketSuite -C $(SYSTEM_DIR)/vsim verilog
	mkdir -p $(dir $@)
	touch $@

$(OBJ_SYSTEM_RTL_V) $(OBJ_SYSTEM_RTL_D) $(OBJ_SYSTEM_RTL_TB_CPP) $(OBJ_SYSTEM_RTL_PRM): $(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).vsim.stamp
	mkdir -p $(dir $@)
	cp -f $(SYSTEM_DIR)/vsim/generated-src/$(notdir $@) $@

# The actual list of tests is produced from Rocket Chip by some build process.
# This isn't quite in a format I can understand, so it gets post-processed by a
# little bash script.
include $(OBJ_SYSTEM_DIR)/tests.mk
$(OBJ_SYSTEM_DIR)/tests.mk: $(OBJ_SYSTEM_RTL_D) $(SYSTEM_GENERATOR_ADDON)/tools/d2mk
	+$(SYSTEM_GENERATOR_ADDON)/tools/d2mk $(filter $(OBJ_SYSTEM_DIR)/%,$^) -o $@

# Rocket Chip needs dramsim2 in order to actaully run tests
$(OBJ_TOOLS_DIR)/dramsim2/include/plsi-include.stamp: $(wildcard $(SYSTEM_DIR)/dramsim2/*.h)
	mkdir -p $(dir $@)
	cp $^ $(dir $@)
	touch $@

# We need to have built the RISC-V tools in order to build the simulator.
# There are two rules here: one to build the tools, and another to install the
# include stamp so the simulator can find the various directories.
$(OBJ_TOOLS_DIR)/riscv-tools/include/plsi-include.stamp: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp
	touch $@

$(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp: $(SYSTEM_GENERATOR_ADDON)/tools/build-toolchain $(find $(SYSTEM_DIR)/riscv-tools -iname "*.S" -or -iname "*.cc")
	+$(SCHEDULER_CMD) $(SYSTEM_GENERATOR_ADDON)/tools/build-toolchain -o $(abspath $@) --tools-dir $(SYSTEM_DIR)/riscv-tools

$(OBJ_TOOLS_DIR)/riscv-tools/lib/libfesvr.so: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp

$(OBJ_TOOLS_DIR)/riscv-tests/rv%: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_TOOLS_DIR)/riscv-tools/riscv64-unknown-elf/share/riscv-tests/isa/$(notdir $@) $@

$(OBJ_TOOLS_DIR)/riscv-tests/%.riscv: $(OBJ_TOOLS_DIR)/riscv-tools/plsi-build.stamp
	mkdir -p $(dir $@)
	cp -f $(OBJ_TOOLS_DIR)/riscv-tools/riscv64-unknown-elf/share/riscv-tests/benchmarks/$(notdir $@) $@

# Rather than passing a bunch of -D command-line arguments through the
# simulator build process (which is a huge hack), we instad just generate a
# header file that has those preprocessor macros defined.
$(OBJ_SYSTEM_DIR)/$(SYSTEM_TOP).$(SYSTEM_CONFIG).define.h: $(SYSTEM_GENERATOR_ADDON)/tools/generate-define-h $(OBJ_SYSTEM_RTL_TB_CPP)
	+$(SYSTEM_GENERATOR_ADDON)/tools/generate-define-h -o $(abspath $@) --tbfrag $(abspath $(OBJ_SYSTEM_RTL_TB_CPP))

# Rocket Chip generates something very similar to this, but it has two
# problems: TBFRAG is defined, and it requires running SBT twice.
%.prm.h: %.prm $(SYSTEM_GENERATOR_ADDON)/tools/prm2h
	+$(SYSTEM_GENERATOR_ADDON)/tools/prm2h $(filter %.prm,$^) -o $@

# Simulating Rocket Chip requires dramsim2, which is included as a submodule
# inside Rocket Chip
$(OBJ_TOOLS_DIR)/dramsim2/libdramsim.so: $(patsubst $(SYSTEM_DIR)/dramsim2/%.cpp,$(OBJ_TOOLS_DIR)/dramsim2/%.o,$(wildcard $(SYSTEM_DIR)/dramsim2/*.cpp))
	mkdir -p $(dir $@)
	$(CXX) -DNO_STORAGE -DNO_OUTPUT -o $@ -shared $(filter %.o,$^)

$(OBJ_TOOLS_DIR)/dramsim2/%.o: $(SYSTEM_DIR)/dramsim2/%.cpp $(wildcard $(SYSTEM_DIR)/dramsim2/*.h)
	mkdir -p $(dir $@)
	$(CXX) -fPIC -DNO_STORAGE -DNO_OUTPUT -c -o $@ $< -I$(SYSTEM_DIR)/dramsim2
