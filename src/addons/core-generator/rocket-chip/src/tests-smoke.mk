check-core: $(CHECK_CORE_DIR)/rv64ui-p-simple.out
trace-core: $(CHECK_CORE_DIR)/rv64ui-p-simple.trace-out
$(CHECK_CORE_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
$(CHECK_CORE_DIR)/rv64ui-p-simple.trace-out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple

check-soc: $(CHECK_SOC_DIR)/rv64ui-p-simple.out
trace-soc: $(CHECK_SOC_DIR)/rv64ui-p-simple.trace-out
$(CHECK_SOC_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
$(CHECK_SOC_DIR)/rv64ui-p-simple.trace-out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple

check-map: $(CHECK_MAP_DIR)/rv64ui-p-simple.out
trace-map: $(CHECK_MAP_DIR)/rv64ui-p-simple.trace-out
$(CHECK_MAP_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
$(CHECK_MAP_DIR)/rv64ui-p-simple.trace-out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple

check-syn: $(CHECK_SYN_DIR)/rv64ui-p-simple.out
trace-syn: $(CHECK_SYN_DIR)/rv64ui-p-simple.trace-out
$(CHECK_SYN_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
$(CHECK_SYN_DIR)/rv64ui-p-simple.trace-out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
