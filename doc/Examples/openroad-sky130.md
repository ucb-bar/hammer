# Introduction with Sky130 and OpenROAD

The following directions will get a simple ``pass`` design from RTL to GDS using the [OpenROAD tools](https://theopenroadproject.org) and the [Skywater 130nm PDK](https://github.com/google/skywater-pdk). These directions are meant to provide the minimal set of steps to do so, please reference the next section, [Hammer End-to-End Integration Tests](https://hammer-vlsi.readthedocs.io/en/stable/Examples/e2e.html), for more detailed descriptions of all files and commands.

## Instructions

First, run the setup script to install the OpenROAD tools using Conda, and Skywater 130 nm PDK using the [Open-PDKs tool](https://github.com/RTimothyEdwards/open_pdks)
This step will take a long time due to the amount and size of the required installs.

```shell
git clone https://github.com/ucb-bar/hammer.git
cd hammer/e2e
./scripts/setup-sky130-openroad.sh [INSTALL_PREFIX]  # default = ~/
```

You should now have a file ``configs-env/my-env.yml`` containing all required tool and technology paths for this tutorial.
To point to your custom environment setup, set the Make variable ``env=my``.
Additionally, we set ``design``, ``pdk``, and ``tools`` to set the RTL design, PDK, and tool flow respecively.
Again, a detailed explanation of this setup is located in the [Hammer End-to-End Integration Tests](https://hammer-vlsi.readthedocs.io/en/stable/Examples/e2e.html).
Now simply run the VLSI flow:

```shell
make design=pass pdk=sky130 tools=or env=my build
make design=pass pdk=sky130 tools=or env=my syn
make design=pass pdk=sky130 tools=or env=my par
make design=pass pdk=sky130 tools=or env=my drc
make design=pass pdk=sky130 tools=or env=my lvs
```

## Next Steps

### Commercial flow

This flow may be run with commercial tools by setting the Make variable ``tools=cm``, which selects the tool plugins via ``configs-tools/cm.yml``.
You will need to create a custom environment YAML file with your environment configuration, in ``configs-env/<my_custom>-env.yml``.
As a minimum, you must specify YAML keys below for the CAD tool licenses and versions/paths of the tools you are using,
see examples in ``configs-env/``.

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

Now re-run a similar flow as before, but pointing to your environment and the commercial tool plugins:

```shell
make design=pass pdk=sky130 tools=cm env=<my_custom> build
```
    

Running DRC/LVS with commercial tools requires access to an NDA-version of the Skywater PDK.
We support running DRC/LVS with either Cadence Pegasus or Siemens Calibre.
See the [Sky130 documentation](https://hammer-vlsi.readthedocs.io/en/stable/Technology/Sky130.html) for how to point to the NDA PDKs and run DRC/LVS with their respective tools.

### Chipyard flow

Follow [these directions in the Chipyard docs](https://chipyard.readthedocs.io/en/latest/VLSI/Sky130-OpenROAD-Tutorial.html) to build your own Chisel SoC design with OpenROAD and Sky130.
