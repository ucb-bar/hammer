# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

OBJ_SOC_RTL_DECOUPLED_JSON = $(OBJ_SOC_DIR)/$(SOC_TOP).decoupled.json
OBJ_SOC_RTL_CHISEL = $(OBJ_SOC_DIR)/chisel/$(SOC_TOP).scala
OBJ_SOC_RTL_CHISEL_V = $(OBJ_SOC_DIR)/chisel/generated-src/$(SOC_TOP).v

# Generates some wrappers that make $(SOC_TOP_FOR_SYNTHESIS) a suitable ASIC
# top-level design and $(SOC_TOP) contain a wrapper 
$(OBJ_SOC_RTL_V): $(OBJ_SOC_RTL_CHISEL_V) $(OBJ_CORE_RTL_V)
	cat $^ > $@

$(OBJ_SOC_RTL_CHISEL_V): $(OBJ_SOC_RTL_CHISEL)
	$(SOC_GENERATOR_ADDON)/tools/run-chisel --top $(SOC_TOP) --output $(abspath $(dir $@)) $(abspath $^)

$(OBJ_SOC_RTL_CHISEL): $(OBJ_SOC_RTL_DECOUPLED_JSON) $(SOC_GENERATOR_ADDON)/tools/generate-asic-top
	mkdir -p $(dir $@)
	$(SOC_GENERATOR_ADDON)/tools/generate-asic-top --core-top $(CORE_TOP) --soc-top $(SOC_TOP) --syn-top $(SOC_TOP_FOR_SYNTHESIS) --decoupled $(filter %.decoupled.json,$^) --output $@

$(OBJ_SOC_RTL_DECOUPLED_JSON): $(CMD_PCAD_INFER_DECOUPLED) $(OBJ_CORE_RTL_V)
	mkdir -p $(dir $@)
	$(CMD_PCAD_INFER_DECOUPLED) -o $@ --top $(CORE_TOP) -i $(filter %.v,$^)

# The test harnesses need to change because the name of the top-level module
# has changed.  This sed is dangerous, but I don't want to talk to upstream so
# I'm just going to live with it...
$(OBJ_SOC_DIR)/csrc/%.cc: $(OBJ_CORE_RTL_C) $(patsubst %,$(OBJ_SOC_DIR)/csrc/%,$(notdir $(wildcard $(patsubst %,%/*.h,$(sort $(dir $(OBJ_CORE_RTL_C)))))))
	mkdir -p $(dir $@)
	cat $(filter %/$(notdir $@),$^) | sed 's/$(CORE_TOP)/$(SOC_TOP)/g' > $@

# So this is a huge hack: essentially what happens is that loads of 
.SECONDARY: $(patsubst %,$(OBJ_SOC_DIR)/csrc/%,$(notdir $(wildcard $(patsubst %,%/*.h,$(sort $(dir $(OBJ_CORE_RTL_C)))))))
$(OBJ_SOC_DIR)/csrc/%.h: $(wildcard $(patsubst %,%/*.h,$(sort $(dir $(OBJ_CORE_RTL_C)))))
	mkdir -p $(dir $@)
	cp -f $(filter %/$(notdir $@),$^) $@
