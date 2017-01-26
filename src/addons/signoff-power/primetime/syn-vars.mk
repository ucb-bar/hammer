# See LICENSE for details

ifeq ($(SYNOPSYS_HOME),)
$(error Running Formality requires SYNOPSYS_HOME to be set)
endif

ifeq ($(PRIMETIME_POWER_VERSION),)
$(error Specify a Formality version as PRIMETIME_POWER_VERSION)
endif

PRIMETIME_POWER_HOME = $(SYNOPSYS_HOME)/pts/$(PRIMETIME_POWER_VERSION)
PRIMETIME_POWER_BIN = $(PRIMETIME_POWER_HOME)/bin/pt_shell

ifeq ($(wildcard $(PRIMETIME_POWER_BIN)),)
$(error Cannot find formality at $(PRIMETIME_POWER_BIN))
endif

VCD2SAIF_BIN = $(SYNOPSYS_HOME)/syn/$(DC_VERSION)/bin/vcd2saif
ifeq ($(wildcard $(VCD2SAIF_BIN)),)
$(error Cannot find vcd2saif at $(VCD2SAIF_BIN))
endif

VPD2VCD_BIN = $(SYNOPSYS_HOME)/vcs/$(VCS_VERSION)/bin/vpd2vcd
ifeq ($(wildcard $(VPD2VCD_BIN)),)
$(error Cannot find vpd2vcd at $(VPD2VCD_BIN))
endif
