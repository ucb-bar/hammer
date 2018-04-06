# See LICENSE for details

ifeq ($(SYNOPSYS_HOME),)
$(error Running Formality requires SYNOPSYS_HOME to be set)
endif

ifeq ($(FORMALITY_VERSION),)
$(error Specify a Formality version as FORMALITY_VERSION)
endif

FORMALITY_HOME = $(SYNOPSYS_HOME)/fm/$(FORMALITY_VERSION)
FORMALITY_BIN = $(FORMALITY_HOME)/bin/fm_shell

ifeq ($(wildcard $(FORMALITY_BIN)),)
$(error Cannot find formality at $(FORMALITY_BIN))
endif

ifneq ($(SYNTHESIS_TOOL),dc)
$(error Formality needs to run with SYNTHESIS_TOOL=dc)
endif
