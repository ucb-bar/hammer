# Copyright 2016 Palmer Dabbelt <palmer@dabbelt.com>

ifeq ($(SYNOPSYS_HOME),)
$(error Running VCS requires SYNOPSYS_HOME to be set)
endif

ifeq ($(VCS_VERSION),)
$(error Specify a VCS version as VCS_VERSION)
endif

ifeq ($(SNPSLMD_LICENSE_FILE),)
$(error SNPSLMD_LICENSE_FILE needs to be exported for VCS to run)
endif

VCS_HOME = $(SYNOPSYS_HOME)/vcs/$(VCS_VERSION)
VCS_BIN = $(VCS_HOME)/bin/vcs

ifeq ($(wildcard $(VCS_BIN)),)
$(error Cannot find VCS at $(VCS_BIN))
endif
