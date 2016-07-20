# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

OBJ_CHIP_RTL_DECOUPLED_JSON = $(OBJ_CHIP_DIR)/$(CHIP_TOP).decoupled.json
OBJ_CHIP_RTL_CHISEL = $(OBJ_CHIP_DIR)/chisel/$(CHIP_TOP).scala
OBJ_CHIP_RTL_CHISEL_V = $(OBJ_CHIP_DIR)/chisel/generated-src/$(CHIP_TOP).v

# Generates some wrappers that make $(CHIP_TOP_FOR_SYNTHESIS) a suitable ASIC
# top-level design and $(CHIP_TOP) contain a wrapper 
$(OBJ_CHIP_RTL_V): $(OBJ_CHIP_RTL_CHISEL_V) $(OBJ_SYSTEM_RTL_V)
	cat $^ > $@

$(OBJ_CHIP_RTL_CHISEL_V): $(OBJ_CHIP_RTL_CHISEL)
	$(CHIP_GENERATOR_ADDON)/tools/run-chisel --top $(CHIP_TOP) --output $(abspath $(dir $@)) $(abspath $^)

$(OBJ_CHIP_RTL_CHISEL): $(OBJ_CHIP_RTL_DECOUPLED_JSON) $(CHIP_GENERATOR_ADDON)/tools/generate-asic-top
	mkdir -p $(dir $@)
	$(CHIP_GENERATOR_ADDON)/tools/generate-asic-top --system-top $(SYSTEM_TOP) --chip-top $(CHIP_TOP) --syn-top $(CHIP_TOP_FOR_SYNTHESIS) --decoupled $(filter %.decoupled.json,$^) --output $@

$(OBJ_CHIP_RTL_DECOUPLED_JSON): $(CMD_PCAD_INFER_DECOUPLED) $(OBJ_SYSTEM_RTL_V)
	mkdir -p $(dir $@)
	$(CMD_PCAD_INFER_DECOUPLED) -o $@ --top $(SYSTEM_TOP) -i $(filter %.v,$^)

# The test harnesses need to change because the name of the top-level module
# has changed.  This sed is dangerous, but I don't want to talk to upstream so
# I'm just going to live with it...
$(OBJ_CHIP_DIR)/csrc/%.cc: $(OBJ_SYSTEM_RTL_C) $(patsubst %,$(OBJ_CHIP_DIR)/csrc/%,$(notdir $(wildcard $(patsubst %,%/*.h,$(sort $(dir $(OBJ_SYSTEM_RTL_C)))))))
	mkdir -p $(dir $@)
	cat $(filter %/$(notdir $@),$^) | sed 's/$(SYSTEM_TOP)/$(CHIP_TOP)/g' > $@

# So this is a huge hack: essentially what happens is that loads of 
.SECONDARY: $(patsubst %,$(OBJ_CHIP_DIR)/csrc/%,$(notdir $(wildcard $(patsubst %,%/*.h,$(sort $(dir $(OBJ_SYSTEM_RTL_C)))))))
$(OBJ_CHIP_DIR)/csrc/%.h: $(wildcard $(patsubst %,%/*.h,$(sort $(dir $(OBJ_SYSTEM_RTL_C)))))
	mkdir -p $(dir $@)
	cp -f $(filter %/$(notdir $@),$^) $@
