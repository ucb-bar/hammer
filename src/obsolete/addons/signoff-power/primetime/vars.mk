# See LICENSE for details

ifeq ($(SYNOPSYS_HOME),)
$(error Running Primetime requires SYNOPSYS_HOME to be set)
endif

ifeq ($(PRIMETIME_POWER_VERSION),)
$(error Specify a Primetime version as PRIMETIME_POWER_VERSION)
endif

define tb_help =
You must set PRIMETIME_PATH_TO_TESTBENCH.
This is necessary for setting STRIP_PATH in the PrimeTime script path from the top module to DUT, which is generally the testbench. Otherwise, PrimeTime fails in signal activity annotations.
Example: Set PRIMETIME_PATH_TO_TESTBENCH to "main/module1" if main.module1.testbench is the hierarchy of the testbench.

endef
ifeq ($(PRIMETIME_PATH_TO_TESTBENCH),)
$(error $(tb_help))
endif

PRIMETIME_POWER_HOME = $(SYNOPSYS_HOME)/pts/$(PRIMETIME_POWER_VERSION)
PRIMETIME_POWER_BIN = $(PRIMETIME_POWER_HOME)/bin/pt_shell

ifeq ($(wildcard $(PRIMETIME_POWER_BIN)),)
$(error Cannot find Primetime at $(PRIMETIME_POWER_BIN))
endif

VCD2SAIF_BIN = $(SYNOPSYS_HOME)/syn/$(DC_VERSION)/bin/vcd2saif
ifeq ($(wildcard $(VCD2SAIF_BIN)),)
$(error Cannot find vcd2saif at $(VCD2SAIF_BIN))
endif

VPD2VCD_BIN = $(SYNOPSYS_HOME)/vcs/$(VCS_VERSION)/bin/vpd2vcd
ifeq ($(wildcard $(VPD2VCD_BIN)),)
$(error Cannot find vpd2vcd at $(VPD2VCD_BIN))
endif

# Use rtl waveform?
PRIMETIME_RTL_TRACE ?=
