# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# Builds yosys from source
$(YOSYS_BIN): \
		$(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/Makefile \
		$(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/Makefile.conf \
		$(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/abc/Makefile \
		$(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)-install/include/tcl.h
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION) install TCL_VERSION=tcl$(TCL_LIBRARY_VERSION) TCL_INCLUDE=$(abspath $(OBJ_TOOLS_DIR)/tcl-$(TCL_VERSION)-install/include) ABCREV=default PREFIX=$(abspath $(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)-install)

$(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/Makefile.conf: $(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/Makefile
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION) config-gcc

$(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/Makefile: $(PLSI_CACHE_DIR)/distfiles/yosys-$(YOSYS_VERSION).tar.gz
	@rm -rf $(dir $@)
	@mkdir -p $(dir $@)
	tar -xzpf $< -C $(dir $@) --strip-components=1
	touch $@

$(PLSI_CACHE_DIR)/distfiles/yosys-$(YOSYS_VERSION).tar.gz:
	@mkdir -p $(dir $@)
	wget https://github.com/cliffordwolf/yosys/archive/yosys-$(YOSYS_VERSION).tar.gz -O $@

$(OBJ_TOOLS_DIR)/yosys-$(YOSYS_VERSION)/abc/Makefile: $(PLSI_CACHE_DIR)/distfiles/abc-$(ABC_VERSION).tar.gz
	@rm -rf $(dir $@)
	@mkdir -p $(dir $@)
	tar -xzpf $< -C $(dir $@) --strip-components=1
	touch $@

$(PLSI_CACHE_DIR)/distfiles/abc-$(ABC_VERSION).tar.gz:
	wget https://bitbucket.org/alanmi/abc/get/abc$(ABC_VERSION).tar.gz -O $@

# Runs a yosys synthesis job
$(OBJ_SYN_MAPPED_V): \
		$(abspath $(SYNTHESIS_TOOL_ADDON)/run-synthesis) \
		$(OBJ_SOC_RTL_V) \
		$(TECHNOLOGY_LIBERTY_FILES) \
		$(YOSYS_BIN)
	@mkdir -p $(dir $@)
	$(SCHEDULER_CMD) --max-threads=1 -- $(abspath $<) --top $(SYN_TOP) -o $(abspath $@) $(abspath $^)
