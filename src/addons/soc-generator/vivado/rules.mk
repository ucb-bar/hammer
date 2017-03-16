# Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
# Generate a top-level Verilog file for Vivado FPGA SoCs.

# Top-level system.v file.
$(OBJ_SOC_SYSTEM_TOP_V): \
	$(abspath $(SOC_GENERATOR_ADDON)/generate-system-v) \
	$(OBJ_SOC_PIN_MAP_DATABASE) \
	$(SOC_GENERATOR_ADDON)/src/system.template.v \
	$(CORE_CONFIG_VIVADO_PINMAP)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) -o $(abspath $@) --top $(SYN_TOP) --pinmap $(abspath $(CORE_CONFIG_VIVADO_PINMAP)) --database $(abspath $(OBJ_SOC_PIN_MAP_DATABASE)) --template $(abspath $(SOC_GENERATOR_ADDON)/src/system.template.v)
