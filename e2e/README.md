# Hammer End-to-End Integration Tests

This folder contains an end-to-end (RTL -> GDS) smoketest flow using Hammer, using the Cadence toolchain, and the ASAP7 or Skywater 130 PDKs.

## Setup

The integration tests use Hammer as a source dependency, so create the e2e poetry environment.

```shell
poetry install
poetry shell
```

## Overview


### Flow Selection

The following variables in the Makefile select the target flow to run:

- `design` - RTL name
    - {`pass`, `gcd`}
- `pdk` - PDK name
    - {`sky130`, `asap7`}
- `tools` - CAD tool flow
    - {`cm` (commercial), `or` (OpenROAD)}
- `env` - compute environment
    - {`bwrc` (BWRC), `a` (Millenium), `inst` (instructional machines)}

The outputs of the flow by default reside in `OBJ_DIR=build-<pdk>-<tools>/<design>/`

### Configs

The Hammer configuration files consist of environment (`ENV_YML`) and project (`PROJ_YMLS`) configurations.
The environment configs take precedence over ALL project configs.
The order of precedence for the project configs reads from right to left (i.e. each file overrides all files to its left).
All configuration files are summarized below.

```shell
#         lowest precedence -------------------------------------------> highest precendence
CONFS ?= $(PDK_CONF) $(TOOLS_CONF) $(DESIGN_CONF) $(DESIGN_PDK_CONF) $(SIM_CONF) $(POWER_CONF)
```

- `ENV_YML`- Environment configs that specify CAD tool license servers and paths are in `configs-env`.
  This will take precedence over any other config file
- `PDK_CONF` - PDK configs shared across all runs with this PDK are in `configs-pdk`
- `TOOLS_CONF` - Tool configs to select which CAD tool flow to use are in `configs-tools`
- Design-specific configs are located in `configs-design/<design>`, and are summarized below:
    - `DESIGN_CONF` - the common design config (design input files, anything else design-specific)
    - `DESIGN_PDK_CONF` - PDK-specific configs for this particular design (clock, placement, pin constraints)
    - `SIM_CONF` - Simulation configs for post-RTL, Synthesis, or PnR simulation
    - `POWER_CONF` - Power simulation configs for post-RTL, Synthesis, or PnR simulation
      (NOTE: The Makefile expects the power config filename for each simulation level + PDK to be in the format `power-{rtl,syn,par}-<pdk>.yml`,
      while the `joules.yml` and `voltus.yml` files serve as templates for the Cadence Joules/Voltus power tools)


## Run the Flow

First, use Hammer to construct a Makefile fragment with targets for all parts of the RTL -> GDS flow.
Specify the appropriate `env/tools/pdk/design` variables to select which configs will be used.

```shell
make build
# same as: `make env=bwrc tools=cm pdk=sky130 design=pass build`
```

Hammer will generate a Makefile fragment in `OBJ_DIR/hammer.d`.

Then run the rest of the flow, making sure to set the `env/tools/pdk/design` variables as needed:

```shell
make sim-rtl
make power-rtl

make syn
make sim-syn
make power-syn

make par
make sim-par
make power-par

make drc
make lvs
```

These actions are summarized in more detail:

- RTL simulation
    - `make sim-rtl`
    - Generated waveform in `OBJ_DIR/sim-rtl-rundir/output.fsdb`
- Post-RTL Power simulation
    - `make sim-rtl-to-power`
    - `make power-rtl`
    - Generated power reports in `OBJ_DIR/power-rtl-rundir/reports`
- Synthesis
    - `make syn`
    - Gate-level netlist in `OBJ_DIR/syn-rundir/<design>.mapped.v`
- Post-Synthesis simulation
    - `make syn-to-sim`
    - `make sim-syn`
    - Generated waveform and register forcing ucli script in `OBJ_DIR/sim-syn-rundir`
- Post-Synthesis Power simulation
    - `make syn-to-power`
    - `make sim-syn-to-power`
    - `make power-syn`
    - Generated power reports in `OBJ_DIR/power-syn-rundir/reports`
- PnR
    - `make syn-to-par`
    - `make par`
    - LVS netlist (`<design>.lvs.v`) and GDS (`<design>.gds`) in `OBJ_DIR/par-rundir`
- Post-PnR simulation
    - `make par-to-sim`
    - `make sim-par`
- Post-PnR Power simulation
    - `make par-to-power`
    - `make sim-par-to-power`
    - `make power-par`
    - Generated power reports in `OBJ_DIR/power-par-rundir`

### Flow Customization

If at any point you would like to use custom config files (that will override any previous configs), assign the `extra` Make variable to a space-separated list of these files.
For example, to run the `pass` design with `sky130` through the commercial flow, but run LVS with Cadence Pegasus instead of the default Siemens Calibre,
simply run the following:

```shell
make extra="configs-tool/pegasus.yml" build
```

To use the [Hammer step flow control](https://hammer-vlsi.readthedocs.io/en/stable/Hammer-Use/Flow-Control.html), prepend `redo-` to any VLSI flow action,
then assign the `args` Make variable to the appropriate Hammer command line args.
For example, to only run the `report_power` step of the `power-rtl` action (i.e. bypass synthesis), run the following:

```shell
make args="--only_step report_power" redo-power-rtl
```

## Custom Setups

If you're not using a Berkeley EECS compute node, you can create your own environment setup.

- Create an environment config similar to those in `configs-env` for your node to specify the CAD tool license servers and paths/versions of CAD tools and the PDK, and set the `ENV_YML` variable to this file.
- The rest of the flow should be identical

### ASAP7 Install

Clone the [asap7 repo](https://github.com/The-OpenROAD-Project/asap7) somewhere and reference the path in your `ENV_YML` config.

### Sky130 Install

Refer to the [Hammer Sky130 plugin README](https://hammer-vlsi.readthedocs.io/en/stable/Technology/Sky130.html)
to install the Sky130 PDK, then reference the path in your `ENV_YML` config (only the `technology.sky130.sky130A` key is required).
