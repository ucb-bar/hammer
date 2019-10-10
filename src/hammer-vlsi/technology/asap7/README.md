ASAP7 Technology Library
===========

HAMMER's default demonstration PDK is [ASAP7](http://asap.asu.edu/asap/). There are some special setup and known issues with this open PDK.

Setup and Environment
=====================

In addition to requirements for `hammer-vlsi`, using ASAP7 also requires:
- The PDK tarball must not be pre-extracted, i.e. must specify `technology.asap7.tarball_dir` only.
- `numpy` and `gdspy` must also be installed. This is needed to modify the GDS after place-and-route. \*
- Calibre must be the DRC/LVS tool.

\*At this moment, for BWRC affiliates, the environment needed for a `gdspy` install is setup only on the LSF cluster machines. To install it:
```
scl enable rh-python36 bash
python -m pip install gdspy --user
```
Or, replace the pip installation with installation from source in `hammer/src/tools/gdspy`.

Known DRC Issues
=================

Due to discrepancies between the technology LEF and DRC decks, these are the currently known DRC violations one can expect to encounter:
- V(n).M(n+1).AUX.2 and V(n).M(n).EN.1 due to limited selection of via cuts
- M(4,5,6,7).AUX.(2,3) off-grid due to incorrect technology LEF offset for these layers
- M1.S.(2,4,5,6) due to V1's being placed off-center from the M1 pin in the standard cells
