# See LICENSE for details

# Every variable in here is the result of a top-level Makefile error from
# checking variables.
CORE_TOP = Multiplier
CORE_SIM_TOP = MultiplierHarness

OBJ_CORE_SIM_FILES = $(CORE_GENERATOR_ADDON)/src/MultiplierHarness.v
OBJ_CORE_SIM_MACRO_FILES = $(CORE_GENERATOR_ADDON)/src/Multiplier.simulation_macros.v
OBJ_CORE_MACROS = $(CORE_GENERATOR_ADDON)/src/Multiplier.macros.json
OBJ_CORE_RTL_FIR = $(OBJ_CORE_DIR)/chisel-generated/Multiplier.fir
OBJ_CORE_RTL_V = $(OBJ_CORE_DIR)/chisel-generated/Multiplier.v

# If you don't define something here then there won't be any test cases that
# can actually run.
check-core: $(CHECK_CORE_DIR)/random.out
trace-core: $(CHECK_CORE_DIR)/random.trace-out
check-soc: $(CHECK_SOC_DIR)/random.out
trace-soc: $(CHECK_SOC_DIR)/random.trace-out
check-map: $(CHECK_MAP_DIR)/random.out
trace-map: $(CHECK_MAP_DIR)/random.trace-out
check-syn: $(CHECK_SYN_DIR)/random.out
trace-syn: $(CHECK_SYN_DIR)/random.trace-out
