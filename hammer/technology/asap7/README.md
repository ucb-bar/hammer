ASAP7 Technology Library
========================

Hammer's default demonstration PDK is [ASAP7](http://asap.asu.edu/asap/). There are some special setup and known issues with this open PDK.

Setup and Environment
---------------------

In addition to requirements for `hammer-vlsi`, using ASAP7 also requires:
- ASAP7 PDK version 1p7, available [here on GitHub](https://github.com/The-OpenROAD-Project/asap7). We recommend downloading an archive of or shallow cloning the repository.
- The Calibre deck tarball (downloaded separately from the website) must not be extracted. It should be placed in the directory specified by `technology.asap7.tarball_dir`. For ease, this can be same directory as the repository.
- Either the `gdstk` or `gdspy` GDS manipulation utility is required for 4x database downscaling. `gdstk` (available [here on GitHub](https://github.com/heitzmann/gdstk), version >0.6) is highly recommended; however, because it is more difficult to install, `gdspy` (available [here on Github](https://github.com/heitzmann/gdspy/releases), specifically version 1.4 can also be used instead, but it is much slower.
- Calibre must be the DRC/LVS tool.  The rule decks only support 2017-year Calibre versions.

\*At this moment, for BWRC affiliates, the environment needed for a `gdstk` or `gdspy` install is setup only on the LSF cluster machines. To install it, first enable the Python dev environment:
```
scl enable rh-python36 bash
```
`gdstk` must be built from source, with dependencies such as CMake, LAPACK, and ZLIB. All must be installed from source into your own environment. For the ZLIB build, make sure the `-fPIC` CFLAG is used. Then, in the `gdstk` source, add the following CMake flags at the top of `setup.py`: `-DZLIB_LIBRARY=/path/to/your/libz.a` and `-DZLIB_INCLUDE_DIR=/path/to/your/include`. Then, in the `gdstk` source folder:
```
python3 setup.py install --user
```
For `gdspy`, the installation is much easier, depending just on `pip` and `numpy`:
```
python -m pip install gdspy --user
```
Or, replace the pip installation with installation from source in the `hammer/src/tools/gdspy` submodule.

Dummy SRAMs
-----------

The ASAP7 plugin comes with a set of dummy SRAMs, which are **NOT** used by default (not included in the default tech.json).

They are **completely blank** (full obstructions on layers M1-M3, will not pass DRC & LVS).
All pins are on M4, with the signal all on the left side and the power stripes running across. The M5 power stripes are able to connect up.

**All SRAMs are scaled up by 4x, so they are subject to the scaling script.**

`sram-cache-gen.py` generates `sram-cache.json` using `srams.txt`, which contains a list of available SRAMs in Hammer IR. `sram-cache.json` memories is used by MacroCompiler to insert these memories into the design.

Finally, the SRAMCompiler in `sram_compiler/__init__.py` is used to generate the ExtraLibrarys (including .lib, .lef, .gds) needed by the particular design.

Known Issues
------------

1. `ICG*DC*` cells are set as don't use due to improper LEF width.

2. Many additional cells are not LVS clean, and are set as don't use.

3. Innovus tries to fix non-existent M3 and M5 enclosure violations, unfortunately lengthening violation fixing time. Ignore these when reviewing the violations in Innovus.

4. If you specify core margins in the placement constraints, they left and bottom margins should be a multiple of 0.384 to avoid DRC violations. Layer offsets for M4-M7 are adjusted manually to keep all wires on-grid.

5. Common expected DRC violations (at reasonable, <70% local density):
   - M(4,5,6,7).AUX.(1,2) only if the floorplan size requirement above is not satisfied
   - V7.M8.AUX.2 and V2.M2.EN.1 due to incomplete via defs for V2 and V7 in power grid
   - FIN.S.1 appears to be incorrect, standard cell fins are indeed on the right pitch
   - LVT.W.1 caused by 0.5-width isolated-VT filler cells due to lack of implant layer spacing rules
   - LISD.S.3, LIG.S.4 due to some combinations of adjacent cells
   - V0.S.1 in ASYNC\_DFFHx1
   - Various M4, GATE violations in/around dummy SRAMs
