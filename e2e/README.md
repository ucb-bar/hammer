# Hammer End-to-End Integration Tests

This folder contains an end-to-end (RTL -> GDS) smoketest flow using Hammer, using the Cadence toolchain, and the ASAP7 or Skywater 130 PDKs.

## Setup

The integration tests use Hammer as a source dependency, so create the e2e poetry environment.

```shell
poetry install
poetry shell
```

## Overview

We provide configs for Berkeley EECS compute nodes: BWRC (`bwrc`), Millennium (`a`), and instructional machines (`inst`).

- Environment configs (commercial CAD tool paths and license servers) are in `configs-env`
- PDK configs for ASAP7 and sky130 (pointers to PDK paths and CAD tool versions) are in `configs-pdk`
- Tool configs to select which CAD tool flow to use are in `configs-tool`
- Design-specific configs are found in `configs-design/<design_name>`. The configs are described below, in ascending order of precendence:
    - `common.yml` - The common design config (design input files, anything else design-specific)
    - `<pdk>.yml` - PDK-specific configs for this particular design (clock, placement, pin constraints)
    - `sim-{rtl,syn,par}.yml` - Simulation configs for post-RTL, Synthesis, and PnR simulation, respectively
    - `power-{rtl,syn,par}-<pdk>.yml` - Power simulation configs for post-RTL, Synthesis, and PnR simulation, respectively.
      The Makefile expects the power configs for each simulation level + PDK to reside in a file named in this format,
      while the `joules.yml` and `voltus.yml` files serve as templates for the Cadence Joules/Voltus power tools.

First, use Hammer to construct a Makefile fragment with targets for all parts of the RTL -> GDS flow.
Specify the configs according to which PDK and environment you are using.

```shell
hammer-vlsi -e env/a-env.yml -p pdks/asap7-a.yml -p configs/common.yml -p configs/asap7.yml build
```

Hammer will generate a Makefile fragment in `obj_dir/hammer.d`.

## Run the Flow

- RTL simulation
    - `make sim-rtl HAMMER_EXTRA_ARGS="-p configs/sim.yml"`
    - Generated waveform in `obj_dir/sim-rtl-rundir/output.fsdb`
- Synthesis
    - `make syn`
    - Gate-level netlist in `obj_dir/syn-rundir/pass.mapped.v`
- Post-Synthesis simulation
    - `make syn-to-sim HAMMER_EXTRA_ARGS="-p configs/syn-sim.yml"`
    - `make sim-syn HAMMER_EXTRA_ARGS="-p configs/syn-sim.yml"`
    - Generated waveform and register forcing ucli script in `obj_dir/sim-syn-rundir`
- PnR
    - `make syn-to-par`
    - `make par`
    - LVS netlist (`pass.lvs.v`) and GDS (`pass.gds`) in `obj_dir/par-rundir`
- Post-PnR simulation
    - `make par-to-sim HAMMER_EXTRA_ARGS="-p configs/par-sim.yml"`
    - `make sim-par HAMMER_EXTRA_ARGS="-p configs/par-sim.yml"`

## Custom Setups

If you're not using a Berkeley EECS compute node, you can create your own environment setup.

- Create an environment config for your node to specify the location of the CAD tools, modeled after the yaml files in `env`
- Create a PDK config for your node to specify the PDK paths and versions, modeled after the yaml files in `pdks`
- Point to your custom configs when running `hammer-vlsi`. The rest of the flow should be identical

### ASAP7 Install

Clone the [asap7 repo](https://github.com/The-OpenROAD-Project/asap7) somewhere and reference the path in your PDK yaml config.
