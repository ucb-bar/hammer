# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

# This script will be sourced multiple times, so there's a guard here to avoid
# redefining the rules to build Icarus.
ifeq ($(ICARUS_VERSION),)
ICARUS_VERSION = 10.1.1
ICARUS_PREFIX ?= $(abspath $(OBJ_TOOLS_BIN_DIR)/icarus-$(ICARUS_VERSION)/)
ICARUS_BIN = $(ICARUS_PREFIX)/bin/iverilog
ICARUS_SRC = $(OBJ_TOOLS_SRC_DIR)/icarus-$(ICARUS_VERSION)
ICARUS_TAR = $(PLSI_CACHE_DIR)/distfiles/icarus-$(ICARUS_VERSION).tar.gz

# Builds Icarus since we can't rely on whatever the core has installed.
$(ICARUS_BIN): $(ICARUS_SRC)/ivl $(CMD_GCC) $(CMD_GXX)
	rm -rf $(ICARUS_PREFIX)
	@mkdir -p $(ICARUS_PREFIX)/lib/ivl
	@mkdir -p $(ICARUS_PREFIX)/bin
	@mkdir -p $(ICARUS_PREFIX)/include/iverilog
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(ICARUS_SRC) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) LDFLAGS="-L$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/lib) -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/lib)"  install

$(ICARUS_SRC)/ivl: $(ICARUS_SRC)/Makefile $(CMD_GCC) $(CMD_GXX)
	$(SCHEDULER_CMD) --make -- $(MAKE) -C $(ICARUS_SRC) CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) CFLAGS="-std=gnu11" LDFLAGS="-L$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/lib) -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/lib)"

$(ICARUS_SRC)/Makefile: $(ICARUS_SRC)/configure $(CMD_GCC) $(CMD_GXX)
	mkdir -p $(dir $@)
	cd $(dir $@) && CC=$(abspath $(CMD_GCC)) CXX=$(abspath $(CMD_GXX)) LDFLAGS="-L$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/lib) -Wl,-rpath,$(abspath $(OBJ_TOOLS_BIN_DIR)/tcl-$(TCL_VERSION)/lib)" ./configure --prefix=$(abspath $(ICARUS_PREFIX))

$(ICARUS_SRC)/configure: $(ICARUS_TAR)
	rm -rf $(dir $@)
	mkdir -p $(dir $@)
	cat $^ | tar -xz --strip-components=1 -C $(dir $@)
	touch $@

$(ICARUS_TAR):
	mkdir -p $(dir $@)
	wget ftp://icarus.com/pub/eda/verilog/v10/verilog-$(ICARUS_VERSION).tar.gz -O $@
endif
