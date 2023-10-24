# Introduction with Sky130 and OpenROAD

The following directions will get a simple ``pass`` design from RTL to GDS using the [OpenROAD tools](https://theopenroadproject.org) and the [Skywater 130nm PDK](https://github.com/google/skywater-pdk). These directions are meant to provide the minimal set of steps to do so, please reference the next section, [Hammer End-to-End Integration Tests](https://hammer-vlsi.readthedocs.io/en/stable/Examples/e2e.html), for more detailed descriptions of all files and commands.

## Instructions

First, follow the [Hammer Developer Setup](https://hammer-vlsi.readthedocs.io/en/stable/Hammer-Basics/Hammer-Setup.html#developer-setup) to clone Hammer and install/activate the poetry virtual environment.

Next, run the setup script to install the OpenROAD tools using Conda, and Skywater 130nm PDK using the [Open-PDKs tool](https://github.com/RTimothyEdwards/open_pdks).
This step will take a long time due to the amount and size of the required installs.
You should supply a ``PREFIX`` path to a directory that will serve as the root of all PDK files and supporting tools (total size of all files is ~42GB).

```shell
cd hammer/e2e
./scripts/setup-sky130-openroad.sh [PREFIX]  # default = ~/
```

You should now have a file ``configs-env/my-env.yml`` containing all required tool and technology paths for this tutorial.
To point to your custom environment setup, set the Make variable ``env=my``.
Additionally, we set the ``design``, ``pdk``, and ``tools`` Make variables to the appropriate RTL design, PDK, and tools flow, respecively.
Now simply run the VLSI flow:

```shell
make design=pass pdk=sky130 tools=or env=my build
make design=pass pdk=sky130 tools=or env=my syn
make design=pass pdk=sky130 tools=or env=my par
make design=pass pdk=sky130 tools=or env=my drc
make design=pass pdk=sky130 tools=or env=my lvs
```

After Place-and-Route completes, the final database can be opened in an interactive OpenROAD session. Hammer generates a convenient script to launch these sessions:
```shell
cd ./build-sky130-or/pass/par-rundir
./generated-scripts/open_chip
```

After DRC and LVS complete, the final results may be viewed with the following scripts:

```shell
# View DRC results:
cd ./build-sky130-or/pass/drc-rundir
./generated-scripts/view_drc

# View LVS results:
cd ./build-sky130-or/pass/lvs-rundir
./generated-scripts/open_chip
```

Congrats, you've just run your ``pass`` design from RTL to GDS with Hammer!

## Next Steps

At this point, you should go through the [Hammer End-to-End Integration Tests](https://hammer-vlsi.readthedocs.io/en/stable/Examples/e2e.html) documentation to learn how to configure Hammer further. We've also outlined some common next steps below.


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
