check-core: $(CHECK_CORE_DIR)/rv64ui-p-simple.out
check-core-vpd: $(CHECK_CORE_DIR)/rv64ui-p-simple.vpdout
$(CHECK_CORE_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple

check-soc: $(CHECK_SOC_DIR)/rv64ui-p-simple.out
check-soc-vpd: $(CHECK_SOC_DIR)/rv64ui-p-simple.vpdout
$(CHECK_SOC_DIR)/rv64ui-p-simple.out: $(OBJ_CORE_DIR)/riscv-tests/rv64ui-p-simple
