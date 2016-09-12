check-core: $(CHECK_CORE_DIR)/rv64ui-p-simple.out
trace-core: $(CHECK_CORE_DIR)/rv64ui-p-simple.trace-out
$(CHECK_CORE_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple

check-soc: $(CHECK_SOC_DIR)/rv64ui-p-simple.out
trace-soc: $(CHECK_SOC_DIR)/rv64ui-p-simple.trace-out
$(CHECK_SOC_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
