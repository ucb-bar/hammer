# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

VERILATOR_VERSION = 3.884
VERILATOR_PREFIX ?= $(abspath $(OBJ_TOOLS_DIR)/verilator-$(VERILATOR_VERSION).install/)
VERILATOR_BIN = $(VERILATOR_PREFIX)/bin/verilator
VERILATOR_SRC = $(OBJ_TOOLS_DIR)/verilator-$(VERILATOR_VERSION)
VERILATOR_TAR = $(PLSI_CACHE_DIR)/distfiles/verilator-$(VERILATOR_VERSION).tar.gz

# These rules actually run the simulations.
$(CHECK_SYSTEM_DIR)/%.out: $(SYSTEM_SIMULATOR_ADDON)/tools/run-simulator $(OBJ_SYSTEM_DIR)/simulator-ndebug $(CMD_PTEST)
	mkdir -p $(dir $@)
	$(CMD_PTEST) --test $(abspath $(SYSTEM_SIMULATOR_ADDON)/tools/run-simulator) --out $@ --args $(abspath $^)

# Verilator requires a simulation object to be built.
$(patsubst %,$(OBJ_SYSTEM_DIR)/simulator-%,ndebug debug): \
		$(OBJ_SYSTEM_RTL_V) \
		$(OBJ_SYSTEM_RTL_C) \
		$(OBJ_SYSTEM_RTL_H) \
		$(OBJ_SYSTEM_RTL_O) \
		$(OBJ_SYSTEM_RTL_I) \
		$(VERILATOR_BIN) \
		$(SYSTEM_SIMULATOR_ADDON)/tools/build-simulator
	+$(abspath $(SYSTEM_SIMULATOR_ADDON)/tools/build-simulator) -o $(abspath $@) --top $(SYSTEM_TOP) --level system --mode $(patsubst simulator-%,%,$(notdir $@)) $(abspath $^)

# Builds Verilator since we can't rely on whatever the system has installed.
$(VERILATOR_BIN): $(VERILATOR_SRC)/bin/verilator
	rm -rf $(VERILATOR_PREFIX)
	$(MAKE) -C $(VERILATOR_SRC) install
	# FIXME: Why do I have to do this?
	mkdir -p $(VERILATOR_PREFIX)/include
	cp -r $(VERILATOR_PREFIX)/share/verilator/include/* $(VERILATOR_PREFIX)/include
	mkdir -p $(VERILATOR_PREFIX)/bin
	cp -r $(VERILATOR_PREFIX)/share/verilator/bin/* $(VERILATOR_PREFIX)/bin

$(VERILATOR_SRC)/bin/verilator: $(VERILATOR_SRC)/Makefile
	$(MAKE) -C $(VERILATOR_SRC)
	touch $@

$(VERILATOR_SRC)/Makefile: $(VERILATOR_SRC)/configure
	mkdir -p $(dir $@)
	cd $(dir $@) && ./configure --prefix=$(abspath $(VERILATOR_PREFIX))

$(VERILATOR_SRC)/configure: $(VERILATOR_TAR)
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	cat $^ | tar -xz --strip-components=1 -C $(dir $@)
	touch $@

$(VERILATOR_TAR):
	mkdir -p $(dir $@)
	wget http://www.veripool.org/ftp/verilator-$(VERILATOR_VERSION).tgz -O $@
