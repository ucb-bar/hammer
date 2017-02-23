# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
# TODO: take care of SRAMs
# TODO: implement simulation

# Generate the FIRRTL by elaborating the top-level module.
$(OBJ_CORE_RTL_FIR): \
		$(CORE_GENERATOR_ADDON)/tools/run-sbt \
		$(CMD_SBT)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $< --sbt $(abspath $(CMD_SBT)) --syn-top $(CORE_TOP) --sim-top $(CORE_SIM_TOP) --top-package $(CORE_CONFIG_TOP_PACKAGE) --srcdir $(abspath $(CORE_CONFIG_PROJ_DIR)) --outdir $(abspath $(dir $@))

# Generates a Verilog file from the FIRRTL representation.
$(OBJ_CORE_RTL_V): \
		$(CMD_FIRRTL_GENERATE_TOP) \
		$(OBJ_CORE_RTL_FIR)
	$(SCHEDULER_CMD) --max-threads=1 -- $< -i $(abspath $(filter %.fir,$^)) -o $(abspath $@) --syn-top $(CORE_TOP) --harness-top $(CORE_SIM_TOP)
