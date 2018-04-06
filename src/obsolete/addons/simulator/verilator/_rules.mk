# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# This script will be sourced multiple times, so there's a guard here to avoid
# redefining the rules to build Verilator.
ifeq ($(VERILATOR_VERSION),)
VERILATOR_VERSION = 3.884
VERILATOR_PREFIX ?= $(abspath $(OBJ_TOOLS_BIN_DIR)/verilator-$(VERILATOR_VERSION)/)
VERILATOR_BIN = $(VERILATOR_PREFIX)/bin/verilator
VERILATOR_SRC = $(OBJ_TOOLS_SRC_DIR)/verilator-$(VERILATOR_VERSION)
VERILATOR_TAR = $(PLSI_CACHE_DIR)/distfiles/verilator-$(VERILATOR_VERSION).tar.gz

# Builds Verilator since we can't rely on whatever the core has installed.
$(VERILATOR_BIN): $(VERILATOR_SRC)/bin/verilator $(CMD_GCC) $(CMD_GXX)
	rm -rf $(VERILATOR_PREFIX)
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(VERILATOR_SRC) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) install
	# FIXME: Why do I have to do this?
	mkdir -p $(VERILATOR_PREFIX)/include
	cp -r $(VERILATOR_PREFIX)/share/verilator/include/* $(VERILATOR_PREFIX)/include
	mkdir -p $(VERILATOR_PREFIX)/bin
	cp -r $(VERILATOR_PREFIX)/share/verilator/bin/* $(VERILATOR_PREFIX)/bin

$(VERILATOR_SRC)/bin/verilator: $(VERILATOR_SRC)/Makefile $(CMD_GCC) $(CMD_GXX)
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(VERILATOR_SRC) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX))
	touch $@

$(VERILATOR_SRC)/Makefile: $(VERILATOR_SRC)/configure $(CMD_GCC) $(CMD_GXX)
	mkdir -p $(dir $@)
	cd $(dir $@) && CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) ./configure --prefix=$(abspath $(VERILATOR_PREFIX))

$(VERILATOR_SRC)/configure: $(VERILATOR_TAR)
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	cat $^ | tar -xz --strip-components=1 -C $(dir $@)
	touch $@

$(VERILATOR_TAR):
	mkdir -p $(dir $@)
	wget http://www.veripool.org/ftp/verilator-$(VERILATOR_VERSION).tgz -O $@
endif
