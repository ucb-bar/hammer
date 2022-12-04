# Hammer End-to-End Integration Tests

This folder contains an end-to-end (RTL -> GDS) smoketest flow using Hammer, using either of the OpenROAD or Cadence toolchains, and the ASAP7 or Skywater 130 PDKs.

## Setup

### Environment

This repo has environment configs (commercial CAD tool paths and license servers) for Berkeley EECS compute nodes (BWRC, Millennium, and instructional machines) in `env`.
Add a file for your specific environment in `env` modeled after the provided files.

### PDKs

#### ASAP7

If you're using a Berkeley EECS compute node, find the ASAP7 install configs in `pdks/asap7-{a,bwrc,inst}.yml`.

If you're using another environment:

1. Clone the [asap7 repo](https://github.com/The-OpenROAD-Project/asap7)
2. Create an ASAP7 install config modeled after the configs in `pdks/asap7{a,bwrc,inst}.yml`

### CAD Tools

### Designs

## Running Hammer

```shell
hammer-vlsi -e env/a-env.yml -p pdks/asap7-a.yml -p test.yml
```
