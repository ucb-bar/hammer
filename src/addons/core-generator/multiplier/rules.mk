# Runs Chisel on the Scala code via a simple bash wrapper for SBT, since SBT
# itself can't change working directories with a command-line option and has a
# tendency to take over the terminal.
$(OBJ_CORE_RTL_FIR): \
		$(CORE_GENERATOR_ADDON)/tools/run-sbt \
		$(CMD_SBT) \
		$(shell find $(abspath $(CORE_GENERATOR_ADDON)) -type f)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< --sbt $(abspath $(CMD_SBT)) --srcdir $(abspath $(CORE_GENERATOR_ADDON)) --outdir $(abspath $(dir $@))

# Generates a Verilog file from the FIRRTL that implements this multiplier
# circuit.
$(OBJ_CORE_RTL_V): \
		$(CMD_FIRRTL_GENERATE_TOP) \
		$(OBJ_CORE_RTL_FIR)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %.fir,$^)) -o $(abspath $@) --syn-top $(CORE_TOP) --harness-top $(CORE_SIM_TOP)
