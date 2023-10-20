Introduction with Sky130 and OpenROAD
=====================================

The following directions will get a simple `pass` design from RTL-to-GDS using the OpenROAD tool flow in the Skywater 130 nm PDK.
These directions are meant to provide the minimal set of steps to do so, please reference the next section, :ref:`Hammer End-to-End Integration Tests<e2e>`, for more detailed descriptions of all files and commands.

Instructions
---------------------------

First, run the setup script to install the `OpenROAD tools <https://theopenroadproject.org/>`__ using Conda, and `Skywater 130nm PDK <https://github.com/google/skywater-pdk>` using the `Open-PDKs tool< https://github.com/RTimothyEdwards/open_pdks>`.
This step will take a long time due to the amount and size of required installs.

```shell
cd hammer/e2e
./scripts/setup-sky130-openroad.sh [<INSTALL_PREFIX>, default=~/]
```

You should now have a file `configs-env/my-env.yml` containing all required tool and technology paths for this tutorial, that should look like the following:
```yaml
# pdk
technology.sky130.sky130A: <INSTALL_PREFIX>/.conda-sky130/share/pdk/sky130A
technology.sky130.sram22_sky130_macros: <INSTALL_PREFIX>/sram22_sky130_macros

# tools
synthesis.yosys.yosys_bin: <INSTALL_PREFIX>/.conda-yosys/bin/yosys
par.openroad.openroad_bin: <INSTALL_PREFIX>/.conda-openroad/bin/openroad
par.openroad.klayout_bin: <INSTALL_PREFIX>/.conda-klayout/bin/klayout
drc.klayout.klayout_bin: <INSTALL_PREFIX>/.conda-klayout/bin/klayout
drc.magic.magic_bin: <INSTALL_PREFIX>/.conda-signoff/bin/magic
lvs.netgen.netgen_bin: <INSTALL_PREFIX>/.conda-signoff/bin/netgen
```

Next Steps
----------

Commercial flow
^^^^^^^^^^^^^^^
This flow may be run with commercial tools, with these tool plugins selected in `configs-tools/cm.yml`
As a minimum, you must specify the CAD tool licenses and versions or paths to the binary in your environment YAML,
see examples in `configs-env/`.

```yaml
# Commercial tool licenses/paths
mentor.mentor_home: "" # Base path to where Mentor tools are installed
mentor.MGLS_LICENSE_FILE: "" # Mentor license server/file

cadence.cadence_home: "" # Base path to where Cadence tools are installed
cadence.CDS_LIC_FILE: "" # Cadence license server/file

synopsys.synopsys_home: "" # Base path to where Synopsys tools are installed
synopsys.SNPSLMD_LICENSE_FILE: "" # Synopsys license server/files
synopsys.MGLS_LICENSE_FILE: ""

# Commercial tool versions/paths
sim.vcs.version: ""
synthesis.genus.version: "" # NOTE: for genus/innovus/joules, must specify binary path if version < 221
par.innovus.version: ""
power.joules.joules_bin: ""
```

Running DRC/LVS with commercial tools requires access to an NDA-version of the Skywater PDK.
We support running DRC/LVS with either Cadence Pegasus or Siemens Calibre.
See the :ref:`Sky130` documentation for how to point to the NDA PDKs and run DRC/LVS with their respective tools.

Chipyard flow
^^^^^^^^^^^^^
Follow `these directions in the Chipyard docs <https://chipyard.readthedocs.io/en/latest/VLSI/Sky130-OpenROAD-Tutorial.html>`__ to build your own design with OpenROAD and Sky130.