#  SKY130 plugin for Hammer.
#
#  See LICENSE for licence details.

import sys
import re
import os
import shutil
from pathlib import Path
from typing import NamedTuple, List, Optional, Tuple, Dict, Set, Any
import importlib
import json
import functools

from hammer.tech import *
from hammer.vlsi import (
    HammerTool,
    HammerPlaceAndRouteTool,
    TCLTool,
    HammerDRCTool,
    HammerLVSTool,
    HammerToolHookAction,
    HierarchicalMode,
)
from hammer.utils import LEFUtils
from hammer.vlsi.hammer_vlsi_impl import HammerSimTool

import hammer.tech.specialcells as specialcells
from hammer.tech.specialcells import CellType, SpecialCell

class SKY130Tech(HammerTechnology):
    """
    Override the HammerTechnology used in `hammer_tech.py`
    This class is loaded by function `load_from_json`, and will pass the `try` in `importlib`.
    """

    def gen_config(self) -> None:
        """Generate the tech config, based on the library type selected"""
        slib = self.get_setting("technology.sky130.stdcell_library")
        SKY130A = self.get_setting("technology.sky130.sky130A")
        SKY130_CDS = self.get_setting("technology.sky130.sky130_cds")
        SKY130_CDS_LIB = self.get_setting("technology.sky130.sky130_scl")

        # Common tech LEF and IO cell spice netlists
        libs = []
        if slib == "sky130_fd_sc_hd":
            libs += [
                Library(
                    spice_file="$SKY130A/libs.ref/sky130_fd_io/spice/sky130_ef_io.spice",
                    provides=[Provide(lib_type="IO library")],
                ),
                Library(
                    lef_file="cache/sky130_fd_sc_hd__nom.tlef",
                    verilog_sim="cache/primitives.v",
                    provides=[Provide(lib_type="technology")],
                ),
            ]
        elif slib == "sky130_scl":
            # Since the cadence (v0.0.3) tlef doesn't have nwell/pwell/li1, we can't use the sky130A IO libs.
            # TODO: should we just take those layers out of the IO tlef? they shouldn't be necessary since we don't route on those layers
            libs += [
                Library(
                    lef_file="cache/sky130_scl_9T.tlef",
                    # lef_file="$SKY130_SCL/lef/sky130_scl_9T.tlef",
                    verilog_sim="$SKY130_SCL/verilog/sky130_scl_9T.v",
                    provides=[Provide(lib_type="technology")],
                ),
            ]
        else:
            raise ValueError(f"Incorrect standard cell library selection: {slib}")
        # Generate IO cells unless we're using the Cadence stdcell lib (see above comment about missing layers in tlef)
        # nvm we need to do this 
        if True: # slib != "sky130_scl":
            library = "sky130_fd_io"
            SKYWATER_LIBS = os.path.join("$SKY130A", "libs.ref", library)
            LIBRARY_PATH = os.path.join(SKY130A, "libs.ref", library, "lib")
            lib_corner_files = os.listdir(LIBRARY_PATH)
            lib_corner_files.sort()
            for cornerfilename in lib_corner_files:
                # Skip versions with no internal power
                if "nointpwr" in cornerfilename:
                    continue

                tmp = cornerfilename.replace(".lib", "")
                # Split into cell, and corner strings
                # Resulting list if only one ff/ss/tt in name: [<cell_name>, <match 'ff'?>, <match 'ss'?>, <match 'tt'?>, <temp & voltages>]
                # Resulting list if ff_ff/ss_ss/tt_tt in name: [<cell_name>, <match 'ff'?>, <match 'ss'?>, <match 'tt'?>, '', <match 'ff'?>, <match 'ss'?>, <match 'tt'?>, <temp & voltages>]
                split_cell_corner = re.split("_(ff)|_(ss)|_(tt)", tmp)
                cell_name = split_cell_corner[0]
                process = split_cell_corner[1:-1]
                temp_volt = split_cell_corner[-1].split("_")[1:]

                # Filter out cross corners (e.g ff_ss or ss_ff)
                if len(process) > 3:
                    if not functools.reduce(
                        lambda x, y: x and y,
                        map(lambda p, q: p == q, process[0:3], process[4:]),
                        True,
                    ):
                        continue
                # Determine actual corner
                speed = next(c for c in process if c is not None).replace("_", "")
                if speed == "ff":
                    speed = "fast"
                if speed == "tt":
                    speed = "typical"
                if speed == "ss":
                    speed = "slow"

                temp = temp_volt[0]
                temp = temp.replace("n", "-")
                temp = temp.split("C")[0] + " C"

                vdd = (".").join(temp_volt[1].split("v")) + " V"
                # Filter out IO/analog voltages that are not high voltage
                if temp_volt[2].startswith("1"):
                    continue
                if len(temp_volt) == 4:
                    if temp_volt[3].startswith("1"):
                        continue

                # gpiov2_pad_wrapped has separate GDS
                if cell_name == "sky130_ef_io__gpiov2_pad_wrapped":

                    file_lib = "sky130_ef_io"
                    gds_file = cell_name + ".gds"
                    lef_file = os.path.join(
                        SKY130A, "libs.ref", library, "lef", "sky130_ef_io.lef"
                    )
                    if self.get_setting("vlsi.core.lvs_tool")   == "hammer.lvs.pegasus" and slib == "sky130_scl":
                        spice_file = None
                    else:
                        spice_file = os.path.join(SKYWATER_LIBS, "cdl", file_lib + ".cdl")
                elif "sky130_ef_io" in cell_name:
                    file_lib = "sky130_ef_io"
                    gds_file = file_lib + ".gds"
                    lef_file = os.path.join(
                        SKY130A, "libs.ref", library, "lef", "sky130_ef_io.lef"
                    )
                    if self.get_setting("vlsi.core.lvs_tool")   == "hammer.lvs.pegasus" and slib == "sky130_scl":
                        spice_file = None
                    else:
                        spice_file = os.path.join(SKYWATER_LIBS, "cdl", file_lib + ".cdl")
                else:
                    if "sky130_fd_io" in cell_name and self.get_setting("vlsi.core.lvs_tool")   == "hammer.lvs.pegasus" :
                    # going to blackbox these
                        spice_file = None
                    else:
                        spice_file = os.path.join(
                            SKYWATER_LIBS, "spice", file_lib + ".spice"
                        )
                    file_lib = library
                    gds_file = file_lib + ".gds"
                    lef_file = os.path.join(SKYWATER_LIBS, "lef", file_lib + ".lef")

                lib_entry = Library(
                    nldm_liberty_file=os.path.join(
                        SKYWATER_LIBS, "lib", cornerfilename
                    ),
                    verilog_sim=os.path.join(SKYWATER_LIBS, "verilog", file_lib + ".v"),
                    lef_file=lef_file,
                    spice_file=spice_file,
                    gds_file=os.path.join(SKYWATER_LIBS, "gds", gds_file),
                    corner=Corner(nmos=speed, pmos=speed, temperature=temp),
                    supplies=Supplies(VDD=vdd, GND="0 V"),
                    provides=[Provide(lib_type=cell_name, vt="RVT")],
                )
                libs.append(lib_entry)

        # Stdcell library-dependent lists
        stackups = []  # type: List[Stackup]
        phys_only = []  # type: List[Cell]
        dont_use = []  # type: List[Cell]
        spcl_cells = []  # type: List[SpecialCell]

        # Select standard cell libraries
        if slib == "sky130_fd_sc_hd":

            phys_only = [
                "sky130_fd_sc_hd__tap_1",
                "sky130_fd_sc_hd__tap_2",
                "sky130_fd_sc_hd__tapvgnd_1",
                "sky130_fd_sc_hd__tapvpwrvgnd_1",
                "sky130_fd_sc_hd__fill_1",
                "sky130_fd_sc_hd__fill_2",
                "sky130_fd_sc_hd__fill_4",
                "sky130_fd_sc_hd__fill_8",
                "sky130_fd_sc_hd__diode_2",
            ]
            dont_use = [
                "*sdf*",
                "sky130_fd_sc_hd__probe_p_*",
                "sky130_fd_sc_hd__probec_p_*",
            ]
            spcl_cells = [
                # for now, skipping the tiecell step. I think the extracted verilog netlist is ignoring the tiecells which is causing lvs issues
                SpecialCell(
                    cell_type=CellType("tiehilocell"), name=["sky130_fd_sc_hd__conb_1"]
                ),
                SpecialCell(
                    cell_type=CellType("tiehicell"),
                    name=["sky130_fd_sc_hd__conb_1"],
                    output_ports=["HI"],
                ),
                SpecialCell(
                    cell_type=CellType("tielocell"),
                    name=["sky130_fd_sc_hd__conb_1"],
                    output_ports=["LO"],
                ),
                SpecialCell(
                    cell_type=CellType("endcap"), name=["sky130_fd_sc_hd__tap_1"]
                ),
                SpecialCell(
                    cell_type=CellType("tapcell"),
                    name=["sky130_fd_sc_hd__tapvpwrvgnd_1"],
                ),
                SpecialCell(
                    cell_type=CellType("stdfiller"),
                    name=[
                        "sky130_fd_sc_hd__fill_1",
                        "sky130_fd_sc_hd__fill_2",
                        "sky130_fd_sc_hd__fill_4",
                        "sky130_fd_sc_hd__fill_8",
                    ],
                ),
                SpecialCell(
                    cell_type=CellType("decap"),
                    name=[
                        "sky130_fd_sc_hd__decap_3",
                        "sky130_fd_sc_hd__decap_4",
                        "sky130_fd_sc_hd__decap_6",
                        "sky130_fd_sc_hd__decap_8",
                        "sky130_fd_sc_hd__decap_12",
                    ],
                ),
                SpecialCell(
                    cell_type=CellType("driver"),
                    name=["sky130_fd_sc_hd__buf_4"],
                    input_ports=["A"],
                    output_ports=["X"],
                ),
                # this breaks synthesis with a complaint about "Cannot perform synthesis because libraries do not have usable inverters." from Genus.
                # note that innovus still recognizes and uses this cell as a buffer 
                #SpecialCell(
                    #cell_type=CellType("ctsbuffer"), name=["sky130_fd_sc_hd__clkbuf_1"]
                    #),
            ]

            # Generate standard cell library
            library = slib

            # scl vs 130a have different site names
            sites = None

            SKYWATER_LIBS = os.path.join("$SKY130A", "libs.ref", library)
            LIBRARY_PATH = os.path.join(SKY130A, "libs.ref", library, "lib")
            lib_corner_files = os.listdir(LIBRARY_PATH)
            lib_corner_files.sort()
            for cornerfilename in lib_corner_files:
                if not (
                    "sky130" in cornerfilename
                ):  # cadence doesn't use the lib name in their corner libs
                    continue
                if "ccsnoise" in cornerfilename:
                    continue  # ignore duplicate corner.lib/corner_ccsnoise.lib files

                tmp = cornerfilename.replace(".lib", "")
                if tmp + "_ccsnoise.lib" in lib_corner_files:
                    cornerfilename = (
                        tmp + "_ccsnoise.lib"
                    )  # use ccsnoise version of lib file

                cornername = tmp.split("__")[1]
                cornerparts = cornername.split("_")

                speed = cornerparts[0]
                if speed == "ff":
                    speed = "fast"
                if speed == "tt":
                    speed = "typical"
                if speed == "ss":
                    speed = "slow"

                temp = cornerparts[1]
                temp = temp.replace("n", "-")
                temp = temp.split("C")[0] + " C"

                vdd = cornerparts[2]
                vdd = vdd.split("v")[0] + "." + vdd.split("v")[1] + " V"

                lib_entry = Library(
                    nldm_liberty_file=os.path.join(
                        SKYWATER_LIBS, "lib", cornerfilename
                    ),
                    verilog_sim=os.path.join("cache", library + ".v"),
                    lef_file=os.path.join(SKYWATER_LIBS, "lef", library + ".lef"),
                    spice_file=os.path.join("cache", library + ".cdl"),
                    gds_file=os.path.join(SKYWATER_LIBS, "gds", library + ".gds"),
                    corner=Corner(nmos=speed, pmos=speed, temperature=temp),
                    supplies=Supplies(VDD=vdd, GND="0 V"),
                    provides=[Provide(lib_type="stdcell", vt="RVT")],
                )

                libs.append(lib_entry)

            # Generate stackup
            tlef_path = os.path.join(
                SKY130A, "libs.ref", library, "techlef", f"{library}__min.tlef"
            )
            metals = list(
                map(lambda m: Metal.model_validate(m), LEFUtils.get_metals(tlef_path))
            )
            stackups.append(
                Stackup(name=slib, grid_unit=Decimal("0.001"), metals=metals)
            )

            sites = [
                Site(name="unithd", x=Decimal("0.46"), y=Decimal("2.72")),
                Site(name="unithddbl", x=Decimal("0.46"), y=Decimal("5.44")),
            ]
            lvs_decks = [
                LVSDeck(
                    tool_name="calibre",
                    deck_name="calibre_lvs",
                    path="$SKY130_NDA/s8/V2.0.1/LVS/Calibre/lvsRules_s8",
                ),
                LVSDeck(
                    tool_name="pegasus",
                    deck_name="pegasus_lvs",
                    path="$SKY130_CDS/Sky130_LVS/sky130.lvs.pvl",
                ),
            ]
            drc_decks = (
                [
                    DRCDeck(
                        tool_name="calibre",
                        deck_name="calibre_drc",
                        path="$SKY130_NDA/s8/V2.0.1/DRC/Calibre/s8_drcRules",
                    ),
                    DRCDeck(
                        tool_name="klayout",
                        deck_name="klayout_drc",
                        path="$SKY130A/libs.tech/klayout/drc/sky130A.lydrc",
                    ),
                    DRCDeck(
                        tool_name="pegasus",
                        deck_name="pegasus_drc",
                        path="$SKY130_CDS/Sky130_DRC/sky130_rev_0.0_1.0.drc.pvl",
                    ),
                ]
            )

        elif slib == "sky130_scl":

            # The cadence PDK (as of version 0.0.3) doesn't seem to have tap nor decap cells, so par won't run (and if we forced it to, lvs would fail)
            spcl_cells = [
                SpecialCell(
                    cell_type="stdfiller", name=[f"FILL{i**2}" for i in range(7)]
                ),
                SpecialCell(
                    cell_type="driver",
                    name=["TBUFX1", "TBUFX4",  "TBUFX8"],
                    input_ports=["A"],
                    output_ports=["Y"],
                ),
                SpecialCell(cell_type="ctsbuffer", name=["CLKBUFX2","CLKBUFX4", "CLKBUFX8" ]),
                SpecialCell(cell_type=CellType("ctsgate"), name=["ICGX1"]),
                SpecialCell(
                    cell_type=CellType("tiehicell"), name=["TIEHI"], input_ports=["Y"]
                ),
                SpecialCell(
                    cell_type=CellType("tielocell"), name=["TIELO"], input_ports=["Y"]
                ),
            ]

            # Generate standard cell library
            library = slib

            LIBRARY_PATH = os.path.join(SKY130_CDS_LIB, "lib")
            lib_corner_files = os.listdir(LIBRARY_PATH)
            lib_corner_files.sort()
            for cornerfilename in lib_corner_files:
                if not (
                    "sky130" in cornerfilename
                ):  # cadence doesn't use the lib name in their corner libs
                    continue
                if "ccsnoise" in cornerfilename:
                    continue  # ignore duplicate corner.lib/corner_ccsnoise.lib files

                tmp = cornerfilename.replace(".lib", "")
                if tmp + "_ccsnoise.lib" in lib_corner_files:
                    cornerfilename = (
                        tmp + "_ccsnoise.lib"
                    )  # use ccsnoise version of lib file

                cornername = tmp.replace("sky130_", "")
                cornerparts = cornername.split("_")

                # Hardcode corner annotations since they don't exactly match the sky130a
                speed = cornerparts[0]
                vdd = ""
                temp = ""
                if speed == "ff":
                    temp = "-40 C"
                    vdd = "1.95 V"
                    speed = "fast"
                if speed == "tt":
                    vdd = "1.80 V"
                    temp = "25 C"
                    speed = "typical"
                if speed == "ss":
                    vdd = "1.60 V"
                    speed = "slow"
                    temp = "100 C"

                lib_entry = Library(
                    nldm_liberty_file=os.path.join(
                        SKY130_CDS_LIB, "lib", cornerfilename
                    ),
                    verilog_sim=os.path.join(
                        SKY130_CDS_LIB, "verilog", library + "_9T.v"
                    ),
                    lef_file=os.path.join(SKY130_CDS_LIB, "lef", library + "_9T.lef"),
                    spice_file=os.path.join(SKY130_CDS_LIB, "cdl", library + "_9T.cdl"),
                    gds_file=os.path.join(SKY130_CDS_LIB, "gds", library + "_9T.gds"),
                    corner=Corner(nmos=speed, pmos=speed, temperature=temp),
                    supplies=Supplies(VDD=vdd, GND="0 V"),
                    provides=[Provide(lib_type="stdcell", vt="RVT")],
                )

                libs.append(lib_entry)

            # Generate stackup
            metals = []  # type: List[Metal]

            tlef_path = os.path.join(SKY130_CDS_LIB, "lef", f"{slib}_9T.tlef")
            metals = list(
                map(lambda m: Metal.model_validate(m), LEFUtils.get_metals(tlef_path))
            )
            stackups.append(
                Stackup(name=slib, grid_unit=Decimal("0.001"), metals=metals)
            )

            sites = [
                Site(name="CoreSite", x=Decimal("0.46"), y=Decimal("4.14")),
                Site(name="IOSite", x=Decimal("1.0"), y=Decimal("240.0")),
                Site(name="CornerSite", x=Decimal("240.0"), y=Decimal("240.0")),
            ]

            lvs_decks = [
                # LVSDeck(tool_name="calibre", deck_name="calibre_lvs",
                # path="$SKY130_NDA/s8/V2.0.1/LVS/Calibre/lvsRules_s8"),
                # seems like cadence just hasthis hardcoded lvs deck name?
                LVSDeck(
                    tool_name="pegasus",
                    deck_name="pegasus_lvs",
                    path=os.path.join(SKY130_CDS, "Sky130_LVS", "sky130.lvs.pvl"),
                )
            ]
            drc_decks = [
                DRCDeck(
                    tool_name="pegasus",
                    deck_name="pegasus_drc",
                    path=os.path.join(
                        SKY130_CDS, "Sky130_DRC", "sky130_rev_0.0_1.0.drc.pvl"
                    ),
                )
            ]

        else:
            raise ValueError(f"Incorrect standard cell library selection: {slib}")

        self.config = TechJSON(
            name="Skywater 130nm Library",
            grid_unit="0.001",
            shrink_factor=None,
            installs=[
                PathPrefix(id="$SKY130_NDA", path="technology.sky130.sky130_nda"),
                PathPrefix(id="$SKY130A", path="technology.sky130.sky130A"),
                PathPrefix(id="$SKY130_CDS", path="technology.sky130.sky130_cds"),
                PathPrefix(id="$SKY130_SCL", path="technology.sky130.sky130_scl"),
            ],
            libraries=libs,
            gds_map_file="sky130_lefpin.map",
            physical_only_cells_list=phys_only,
            dont_use_list=dont_use,
            additional_drc_text="",
            lvs_decks=lvs_decks,
            drc_decks=drc_decks,
            additional_lvs_text="",
            tarballs=None,
            sites=sites,
            stackups=stackups,
            special_cells=spcl_cells,
            extra_prefixes=None,
        )

    def post_install_script(self) -> None:
        self.library_name = "sky130_fd_sc_hd"
        # check whether variables were overriden to point to a valid path
        self.use_sram22 = os.path.exists(
            self.get_setting("technology.sky130.sram22_sky130_macros")
        )
        if self.get_setting("technology.sky130.stdcell_library") == "sky130_fd_sc_hd":
            self.setup_cdl()
            self.setup_verilog()
        self.setup_techlef()
        #self.setup_io_lefs()
        print('Loaded Sky130 Tech')


    def setup_cdl(self) -> None:
        """Copy and hack the cdl, replacing pfet_01v8_hvt/nfet_01v8 with
        respective names in LVS deck
        """
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)
        source_path = (
            setting_dir
            / "libs.ref"
            / self.library_name
            / "cdl"
            / f"{self.library_name}.cdl"
        )
        if not source_path.exists():
            raise FileNotFoundError(f"CDL not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / f"{self.library_name}.cdl"

        # device names expected in LVS decks
        if self.get_setting("vlsi.core.lvs_tool") == "hammer.lvs.calibre":
            pmos = "phighvt"
            nmos = "nshort"
        elif self.get_setting("vlsi.core.lvs_tool") == "hammer.lvs.netgen":
            pmos = "sky130_fd_pr__pfet_01v8_hvt"
            nmos = "sky130_fd_pr__nfet_01v8"
        else:
            shutil.copy2(source_path, dest_path)
            return

        with open(source_path, "r") as sf:
            with open(dest_path, "w") as df:
                self.logger.info(
                    "Modifying CDL netlist: {} -> {}".format(source_path, dest_path)
                )
                df.write("*.SCALE MICRON\n")
                for line in sf:
                    line = line.replace("pfet_01v8_hvt", pmos)
                    line = line.replace("nfet_01v8", nmos)
                    df.write(line)

    # Copy and hack the verilog
    #   - <library_name>.v: remove 'wire 1' and one endif line to fix syntax errors
    #   - primitives.v: set default nettype to 'wire' instead of 'none'
    #           (the open-source RTL sim tools don't treat undeclared signals as errors)
    #   - Deal with numerous inconsistencies in timing specify blocks.
    def setup_verilog(self) -> None:
        setting_dir = self.get_setting("technology.sky130.sky130A")
        setting_dir = Path(setting_dir)

        # <library_name>.v
        source_path = (
            setting_dir
            / "libs.ref"
            / self.library_name
            / "verilog"
            / f"{self.library_name}.v"
        )
        if not source_path.exists():
            raise FileNotFoundError(f"Verilog not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / f"{self.library_name}.v"

        with open(source_path, "r") as sf:
            with open(dest_path, "w") as df:
                self.logger.info(
                    "Modifying Verilog netlist: {} -> {}".format(source_path, dest_path)
                )
                for line in sf:
                    line = line.replace("wire 1", "// wire 1")
                    line = line.replace(
                        "`endif SKY130_FD_SC_HD__LPFLOW_BLEEDER_FUNCTIONAL_V",
                        "`endif // SKY130_FD_SC_HD__LPFLOW_BLEEDER_FUNCTIONAL_V",
                    )
                    df.write(line)

# TODO(elamdf): check if this is still required
        # # Additionally hack out the specifies
        # sl = []
        # with open(dest_path, "r") as sf:
        #     sl = sf.readlines()

        #     # Find timing declaration
        #     start_idx = [
        #         idx
        #         for idx, line in enumerate(sl)
        #         if "`ifndef SKY130_FD_SC_HD__LPFLOW_BLEEDER_1_TIMING_V" in line
        #     ][0]

        #     # Search for the broken statement
        #     search_range = range(start_idx + 1, len(sl))
        #     broken_specify_idx = len(sl) - 1
        #     broken_substr = "(SHORT => VPWR) = (0:0:0,0:0:0,0:0:0,0:0:0,0:0:0,0:0:0);"

        #     broken_specify_idx = [
        #         idx for idx in search_range if broken_substr in sl[idx]
        #     ][0]
        #     endif_idx = [idx for idx in search_range if "`endif" in sl[idx]][0]

        #     # Now, delete all the specify statements if specify exists before an endif.
        #     if broken_specify_idx < endif_idx:
        #         self.logger.info("Removing incorrectly formed specify block.")
        #         cell_def_range = range(start_idx + 1, endif_idx)
        #         start_specify_idx = [
        #             idx for idx in cell_def_range if "specify" in sl[idx]
        #         ][0]
        #         end_specify_idx = [
        #             idx for idx in cell_def_range if "endspecify" in sl[idx]
        #         ][0]
        #         sl[start_specify_idx : end_specify_idx + 1] = []  # Dice

        # # Deal with the nonexistent net tactfully (don't code in brittle replacements)
        # self.logger.info("Fixing broken net references with select specify blocks.")
        # pattern = r"^\s*wire SLEEP.*B.*delayed;"
        # capture_pattern = r".*(SLEEP.*?B.*?delayed).*"
        # pattern_idx = [
        #     (idx, re.findall(capture_pattern, value)[0])
        #     for idx, value in enumerate(sl)
        #     if re.search(pattern, value)
        # ]
        # for list_idx, pattern_tuple in enumerate(pattern_idx):
        #     if list_idx != len(pattern_idx) - 1:
        #         search_range = range(pattern_tuple[0] + 1, pattern_idx[list_idx + 1][0])
        #     else:
        #         search_range = range(pattern_tuple[0] + 1, len(sl))
        #     for idx in search_range:
        #         list = re.findall(capture_pattern, sl[idx])
        #         for elem in list:
        #             if elem != pattern_tuple[1]:
        #                 sl[idx] = sl[idx].replace(elem, pattern_tuple[1])
        #                 self.logger.info(
        #                     f"Incorrect reference `{elem}` to be replaced with: `{pattern_tuple[1]}` on raw line {idx}."
        #                 )

        # # Write back into destination
        # with open(dest_path, "w") as df:
        #     df.writelines(sl)

        # primitives.v
        source_path = (
            setting_dir / "libs.ref" / self.library_name / "verilog" / "primitives.v"
        )
        if not source_path.exists():
            raise FileNotFoundError(f"Verilog not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / "primitives.v"

        with open(source_path, "r") as sf:
            with open(dest_path, "w") as df:
                self.logger.info(
                    "Modifying Verilog netlist: {} -> {}".format(source_path, dest_path)
                )
                for line in sf:
                    line = line.replace(
                        "`default_nettype none", "`default_nettype wire"
                    )
                    df.write(line)

    # Copy and hack the tech-lef, adding this very important `licon` section
    def setup_techlef(self) -> None:
        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        if self.get_setting("technology.sky130.stdcell_library") == "sky130_fd_sc_hd":
            setting_dir = self.get_setting("technology.sky130.sky130A")
            setting_dir = Path(setting_dir)
            source_path = (
                setting_dir
                / "libs.ref"
                / self.library_name
                / "techlef"
                / f"{self.library_name}__nom.tlef"
            )
            dest_path = cache_tech_dir_path / f"{self.library_name}__nom.tlef"
        else: 
            setting_dir = self.get_setting("technology.sky130.sky130_scl")
            setting_dir = Path(setting_dir)
            source_path = (
                setting_dir
                / "lef"
                / "sky130_scl_9T.tlef"
            )
            dest_path = cache_tech_dir_path / "sky130_scl_9T.tlef"
        if not source_path.exists():
            raise FileNotFoundError(f"Tech-LEF not found: {source_path}")


        with open(source_path, "r") as sf:
            with open(dest_path, "w") as df:
                self.logger.info(
                    "Modifying Technology LEF: {} -> {}".format(source_path, dest_path)
                )
                for line in sf:
                    df.write(line)
                    if self.get_setting("technology.sky130.stdcell_library") == "sky130_scl":
                        if line.strip() == "END poly":
                            df.write(_the_tlef_edit + _additional_tlef_edit_for_scl)
                    else:
                        if line.strip() == "END pwell":
                            df.write(_the_tlef_edit)

    # syn_power seems to not take hooks from `get_tech_syn_hooks`
    # also, syn_power is called from joules so we need to add the hook to joules
    # TODO: clean this up, there should be a way to always include this hook whenever genus will be invoked
    def get_tech_power_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {}

        def enable_scl_clk_gating_cell_hook(ht: HammerTool) -> bool:
            ht.append(
                "set_db [get_db lib_cells -if {.base_name == ICGX1}] .avoid false"
            )
            return True

        # The clock gating cell is set to don't touch/use in the cadence pdk (as of v0.0.3), work around that
        if self.get_setting("technology.sky130.stdcell_library") == "sky130_scl":
            hooks["joules"] = [
                HammerTool.make_pre_insertion_hook(
                    "synthesize_design", enable_scl_clk_gating_cell_hook
                )
            ]

        return hooks.get(tool_name, [])

    def get_tech_syn_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {}

        def enable_scl_clk_gating_cell_hook(ht: HammerTool) -> bool:
            ht.append(
                "set_db [get_db lib_cells -if {.base_name == ICGX1}] .avoid false"
            )
            return True

        # The clock gating cell is set to don't touch/use in the cadence pdk (as of v0.0.3), work around that
        if self.get_setting("technology.sky130.stdcell_library") == "sky130_scl":
            hooks["genus"] = [
                HammerTool.make_pre_insertion_hook(
                    "syn_generic", enable_scl_clk_gating_cell_hook
                )
            ]

            # seems to mess up lvs for now
        # hooks['genus'].append(HammerTool.make_removal_hook("add_tieoffs"))
        return hooks.get(tool_name, [])

    # Power pins for clamps must be CLASS CORE
    def setup_io_lefs(self) -> None:
        sky130A_path = Path(self.get_setting('technology.sky130.sky130A'))
        source_path = sky130A_path / 'libs.ref' / 'sky130_fd_io' / 'lef' / 'sky130_ef_io.lef'
        if not source_path.exists():
            raise FileNotFoundError(f"IO LEF not found: {source_path}")

        cache_tech_dir_path = Path(self.cache_dir)
        os.makedirs(cache_tech_dir_path, exist_ok=True)
        dest_path = cache_tech_dir_path / 'sky130_ef_io.lef'

        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying IO LEF: {} -> {}".format
                    (source_path, dest_path))
                sl = sf.readlines()
                for net in ['VCCD1', 'VSSD1', 'VDDA', 'VSSA', 'VSSIO']:
                    start = [idx for idx,line in enumerate(sl) if 'PIN ' + net in line]
                    end = [idx for idx,line in enumerate(sl) if 'END ' + net in line]
                    intervals = zip(start, end)
                    for intv in intervals:
                        port_idx = [idx for idx,line in enumerate(sl[intv[0]:intv[1]]) if 'PORT' in line and "met3" in sl[intv[0] + idx + 1]]
                        for idx in port_idx:
                            sl[intv[0]+idx]=sl[intv[0]+idx].replace('PORT', 'PORT\n      CLASS CORE ;')
                # force class to spacer
                # TODO: the disconnect_* slices are also broken like this, but we're not using them
                start = [idx for idx, line in enumerate(sl) if 'MACRO sky130_ef_io__connect_vcchib_vccd_and_vswitch_vddio_slice_20um' in line]
                sl[start[0] + 1] = sl[start[0] + 1].replace('AREAIO', 'SPACER')

                for idx, line in enumerate(sl):
                    if "PIN OUT" in line:
                        sl[idx+1].replace("DIRECTION INPUT ;", "DIRECTION INPUT ;\n    ANTENNAGATEAREA 1.529 LAYER met3 ;")

                df.writelines(sl)

    def get_tech_par_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        hooks = {
            "innovus": [
                HammerTool.make_post_insertion_hook(
                    "init_design", sky130_innovus_settings
                ),
                HammerTool.make_pre_insertion_hook("power_straps", sky130_connect_nets),
                HammerTool.make_pre_insertion_hook(
                    "write_design", sky130_connect_nets2
                ),
            ]
        }
        # there are no cap/decap cells in the cadence stdcell library as of version 0.0.3, so we can't do things that reference them
        if self.get_setting("technology.sky130.stdcell_library") == "sky130_scl":

            hooks["innovus"].append(
                HammerTool.make_replacement_hook(
                    "power_straps", power_rail_straps_no_tapcells
                )
            )
        else:
            hooks["innovus"].append(
                HammerTool.make_pre_insertion_hook(
                    "place_tap_cells", sky130_add_endcaps
                )
            )

        return hooks.get(tool_name, [])

    def get_tech_drc_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        calibre_hooks = []
        pegasus_hooks = []
        if self.get_setting("technology.sky130.drc_blackbox_srams"):
            calibre_hooks.append(
                HammerTool.make_post_insertion_hook(
                    "generate_drc_run_file", calibre_drc_blackbox_srams
                )
            )
            pegasus_hooks.append(
                HammerTool.make_post_insertion_hook(
                    "generate_drc_ctl_file", pegasus_drc_blackbox_srams
                )
            )
        hooks = {"calibre": calibre_hooks, "pegasus": pegasus_hooks}
        return hooks.get(tool_name, [])

    def get_tech_lvs_hooks(self, tool_name: str) -> List[HammerToolHookAction]:
        calibre_hooks = [
            HammerTool.make_post_insertion_hook(
                "generate_lvs_run_file", setup_calibre_lvs_deck
            )
        ]
        pegasus_hooks = []
        if self.use_sram22:
            calibre_hooks.append(
                HammerTool.make_post_insertion_hook(
                    "generate_lvs_run_file", sram22_lvs_recognize_gates_all
                )
            )
        if self.get_setting("technology.sky130.lvs_blackbox_srams"):
            calibre_hooks.append(
                HammerTool.make_post_insertion_hook(
                    "generate_lvs_run_file", calibre_lvs_blackbox_srams
                )
            )
            pegasus_hooks.append(
                HammerTool.make_post_insertion_hook(
                    "generate_lvs_ctl_file", pegasus_lvs_blackbox_srams
                )
            )

        if self.get_setting("technology.sky130.stdcell_library") == "sky130_scl":
            pegasus_hooks.append(
                HammerTool.make_post_insertion_hook(
                    "generate_lvs_ctl_file", pegasus_lvs_add_130a_primitives
                )
            )
        hooks = {"calibre": calibre_hooks, "pegasus": pegasus_hooks}
        return hooks.get(tool_name, [])

    @staticmethod
    def openram_sram_names() -> List[str]:
        """Return a list of cell-names of the OpenRAM SRAMs (that we'll use)."""
        return [
            "sky130_sram_1kbyte_1rw1r_32x256_8",
            "sky130_sram_1kbyte_1rw1r_8x1024_8",
            "sky130_sram_2kbyte_1rw1r_32x512_8",
        ]

    @staticmethod
    def sky130_sram_primitive_names() -> List[str]:
        spice_filenames = [
            "sky130_fd_pr__pfet_01v8",
            "sky130_fd_pr__nfet_01v8",
            "sky130_fd_pr__pfet_01v8_hvt",
            "sky130_fd_pr__special_nfet_latch",
            "sky130_fd_pr__special_nfet_pass",
        ]  # "sky130_fd_pr__special_pfet_latch", ]
        paths = []
        for fname in spice_filenames:
            paths.append(
                f"/tools/commercial/skywater/local/sky130A/libs.ref/sky130_fd_pr/spice/{fname}.pm3.spice"
            )
        # TODO: this is bc line 535 in the bwrc one causes a syntax error
        paths.append(
            "/tools/C/elamdf/chipyard_dev/vlsi/sky130_fd_pr__special_pfet_latch.pm3.spice"
        )
        return paths

    @staticmethod
    def sky130_sram_names() -> List[str]:
        sky130_sram_names = []
        sram_cache_json = (
            importlib.resources.files("hammer.technology.sky130")
            .joinpath("sram-cache.json")
            .read_text()
        )
        dl = json.loads(sram_cache_json)
        for d in dl:
            sky130_sram_names.append(d["name"])
        return sky130_sram_names


## string constants
# the io libs (sky130a)
_the_tlef_edit = """
LAYER AREAIDLD
  TYPE MASTERSLICE ;
END AREAIDLD

LAYER licon
  TYPE CUT ;
END licon
"""
_additional_tlef_edit_for_scl = """"
LAYER nwell
  TYPE MASTERSLICE ;
END nwell
LAYER pwell
  TYPE MASTERSLICE ;
END pwell
LAYER li1
  TYPE MASTERSLICE ;
END li1
"""

LVS_DECK_INSERT_LINES = """
LVS FILTER D  OPEN  SOURCE
LVS FILTER D  OPEN  LAYOUT
"""

LVS_DECK_SCRUB_LINES = [
    "VIRTUAL CONNECT REPORT",
    "SOURCE PRIMARY",
    "SOURCE SYSTEM SPICE",
    "SOURCE PATH",
    "ERC",
    "LVS REPORT",
]

# various Innovus database settings
def sky130_innovus_settings(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "Innovus settings only for par"
    assert isinstance(ht, TCLTool), "innovus settings can only run on TCL tools"
    """Settings for every tool invocation"""
    ht.append(
        f"""

##########################################################
# Placement attributes  [get_db -category place]
##########################################################
#-------------------------------------------------------------------------------
set_db place_global_place_io_pins  true

set_db opt_honor_fences true
set_db place_detail_dpt_flow true
set_db place_detail_color_aware_legal true
set_db place_global_solver_effort high
set_db place_detail_check_cut_spacing true
set_db place_global_cong_effort high

##########################################################
# Optimization attributes  [get_db -category opt]
##########################################################
#-------------------------------------------------------------------------------

set_db opt_fix_fanout_load true
set_db opt_clock_gate_aware false
set_db opt_area_recovery true
set_db opt_post_route_area_reclaim setup_aware
set_db opt_fix_hold_verbose true

##########################################################
# Clock attributes  [get_db -category cts]
##########################################################
#-------------------------------------------------------------------------------
set_db cts_target_skew 0.03
set_db cts_max_fanout 10
#set_db cts_target_max_transition_time .3
set_db opt_setup_target_slack 0.10
set_db opt_hold_target_slack 0.10

##########################################################
# Routing attributes  [get_db -category route]
##########################################################
#-------------------------------------------------------------------------------
set_db route_design_antenna_diode_insertion 1
set_db route_design_antenna_cell_name "{"sky130_fd_sc_hd__diode_2" if ht.get_setting("technology.sky130.stdcell_library") == "sky130_fd_sc_hd" else "ANTENNA"}"

set_db route_design_high_freq_search_repair true
set_db route_design_detail_post_route_spread_wire true
set_db route_design_with_si_driven true
set_db route_design_with_timing_driven true
set_db route_design_concurrent_minimize_via_count_effort high
set_db opt_consider_routing_congestion true
set_db route_design_detail_use_multi_cut_via_effort medium
    """
    )
    if ht.hierarchical_mode in {HierarchicalMode.Top, HierarchicalMode.Flat}:
        ht.append(
            """
# For top module: snap die to manufacturing grid, not placement grid
set_db floorplan_snap_die_grid manufacturing
        """
        )

    return True


def sky130_connect_nets(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "connect global nets only for par"
    assert isinstance(ht, TCLTool), "connect global nets can only run on TCL tools"
    for pwr_gnd_net in ht.get_all_power_nets() + ht.get_all_ground_nets():
        if pwr_gnd_net.tie is not None:
            ht.append(
                "connect_global_net {tie} -type pg_pin -pin_base_name {net} -all -auto_tie -netlist_override".format(
                    tie=pwr_gnd_net.tie, net=pwr_gnd_net.name
                )
            )
            ht.append(
                "connect_global_net {tie} -type net    -net_base_name {net} -all -netlist_override".format(
                    tie=pwr_gnd_net.tie, net=pwr_gnd_net.name
                )
            )
    return True


# Pair VDD/VPWR and VSS/VGND nets
#   these commands are already added in Innovus.write_netlist,
#   but must also occur before power straps are placed
def sky130_connect_nets2(ht: HammerTool) -> bool:
    sky130_connect_nets(ht)
    return True


def sky130_add_endcaps(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "endcap insertion only for par"
    assert isinstance(ht, TCLTool), "endcap insertion can only run on TCL tools"
    endcap_cells = ht.technology.get_special_cell_by_type(CellType.EndCap)
    endcap_cell = endcap_cells[0].name[0]
    ht.append(
        f"""
set_db add_endcaps_boundary_tap     true
set_db add_endcaps_left_edge        {endcap_cell}
set_db add_endcaps_right_edge       {endcap_cell}
add_endcaps
    """
    )
    return True


# TODO(elamdf): port this from hammer-driver once rebase is done
# def efabless_ring_io(ht: HammerTool) -> bool:
#     assert isinstance(ht, HammerPlaceAndRouteTool), "IO ring instantiation only for par"
#     assert isinstance(ht, TCLTool), "IO ring instantiation can only run on TCL tools"
#     io_file = ht.get_setting("technology.sky130.io_file")
#     ht.append(f"read_io_file {io_file} -no_die_size_adjust")
#     p_nets = list(map(lambda s: s.name, ht.get_independent_power_nets()))
#     g_nets = list(map(lambda s: s.name, ht.get_independent_ground_nets()))
#     ht.append(
#         f"""
# # Global net connections
# connect_global_net VDDA -type pg_pin -pin_base_name VDDA -verbose
# connect_global_net VDDIO -type pg_pin -pin_base_name VDDIO* -verbose
# connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VCCD* -verbose
# connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VCCHIB -verbose
# connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VSWITCH -verbose
# connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSA -verbose
# connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSIO* -verbose
# connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSD* -verbose
#     """
#     )
#     ht.append(
#         """
# # IO fillers
# set io_fillers {sky130_ef_io__connect_vcchib_vccd_and_vswitch_vddio_slice_20um sky130_ef_io__com_bus_slice_10um sky130_ef_io__com_bus_slice_5um sky130_ef_io__com_bus_slice_1um}
# add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side top -filler_orient r0
# add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side right -filler_orient r270
# add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side bottom -filler_orient r180
# add_io_fillers -prefix IO_FILLER -io_ring 1 -cells $io_fillers -side left -filler_orient r90
# # Fix placement
# set io_filler_insts [get_db insts IO_FILLER_*]
# set_db $io_filler_insts .place_status fixed
#     """
#     )
#     # An offset of 40um is used to place the core ring inside the core area. It
#     # can be decreased down to 5um as desired, but will require additional
#     # routing / settings to connect the core power stripes to the ring.
#     ht.append(
#         f"""
# # Core ring
# add_rings -follow io -layer met5 -nets {{ {p_nets[0]} {g_nets[0]} }} -offset 40 -width 13 -spacing 3
# route_special -connect pad_pin -nets {{ {p_nets[0]} {g_nets[0]} }} -detailed_log
#     """
#     )
#     ht.append(
#         """
# # Prevent buffering on TIE_LO_ESD and TIE_HI_ESD
# set_dont_touch [get_db [get_db pins -if {.name == *TIE*ESD}] .net]
#     """
#     )
#     return True


def power_rail_straps_no_tapcells(ht: HammerTool) -> bool:
    #  We do this since there are no explicit tapcells in sky130_scl

    # just need the rail ones, others are placed as usual.
    ht.append(
        """
# --------------------------------------------------------------------------------
# This script was written and developed by HAMMER at UC Berkeley; however, the
# underlying commands and reports are copyrighted by Cadence. We thank Cadence for
# granting permission to share our research to help promote and foster the next
# generation of innovators.
# --------------------------------------------------------------------------------

# Power strap definition for layer met1 (rails):

# should be .14
set_db add_stripes_stacked_via_top_layer met1
set_db add_stripes_stacked_via_bottom_layer met1
set_db add_stripes_spacing_from_block 4.000
#add_stripes -over_physical_pins 1 -nets {VDD VSS} -width .14 -direction horizontal -pin_layer met1 -layer met1
#add_stripes -layer met1 -over_pins 1 -number_of_sets 1 -spacing 3.74 -direction horizontal -width .4 -nets { VSS VDD } -number_of_sets 1
#add_stripes -pin_layer met1 -layer met1 -over_pins 1 -spacing .2 -direction horizontal -width .4 -nets { VSS VDD }
#add_stripes -master "FILL*" -over_pins 1 -block_ring_bottom_layer_limit met1 -block_ring_top_layer_limit met1 -direction horizontal -layer met1 -nets {VSS VDD} -pad_core_ring_bottom_layer_limit met1 -width pin_width
#add_stripes -nets {VDD VSS} -layer met1 -direction horizontal -width .4 -spacing 4.54 -set_to_set_distance 9.08 -start_from bottom -pin_offset -2.46
#add_stripes -nets {VDD VSS} -layer met1 -direction horizontal -width .4 -spacing 3.74 -number_of_sets 1 -start_from left -switch_layer_over_obs false -max_same_layer_jog_length 2 -pad_core_ring_top_layer_limit met5 -pad_core_ring_bottom_layer_limit met1 -block_ring_top_layer_limit met5 -block_ring_bottom_layer_limit met1 -use_wire_group 0 -snap_wire_center_to_grid none
add_stripes -nets {VDD VSS} -layer met1 -direction horizontal -start_offset -.2 -width .4 -spacing 3.74 -set_to_set_distance 8.28 -start_from bottom -switch_layer_over_obs false -max_same_layer_jog_length 2 -pad_core_ring_top_layer_limit met5 -pad_core_ring_bottom_layer_limit met1 -block_ring_top_layer_limit met5 -block_ring_bottom_layer_limit met1 -use_wire_group 0 -snap_wire_center_to_grid none

# Power strap definition for layer met2:

#set_db add_stripes_stacked_via_top_layer met2
#set_db add_stripes_stacked_via_bottom_layer met1
#set_db add_stripes_trim_antenna_back_to_shape {stripe}
##set_db add_stripes_spacing_from_block 4.000
##add_stripes -create_pins 0 -block_ring_bottom_layer_limit met2 -block_ring_top_layer_limit met1 -direction vertical -layer met2 -nets {VSS VDD} -pad_core_ring_bottom_layer_limit met1 -set_to_set_distance 101.20 -spacing 2.26 -switch_layer_over_obs 0 -width 1.42 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 4.81]
#add_stripes -nets {VDD VSS} -layer met2 -direction vertical -width .2 -spacing 0.14 -number_of_sets 1 -extend_to all_domains -start_from left -switch_layer_over_obs false -max_same_layer_jog_length 2 -pad_core_ring_top_layer_limit met5 -pad_core_ring_bottom_layer_limit met1 -block_ring_top_layer_limit met5 -block_ring_bottom_layer_limit met1 -use_wire_group 0 -snap_wire_center_to_grid none

## Power strap definition for layer met3:

#set_db add_stripes_stacked_via_top_layer met3
#set_db add_stripes_stacked_via_bottom_layer met2
#set_db add_stripes_trim_antenna_back_to_shape {stripe}
#set_db add_stripes_spacing_from_block 2.000
#add_stripes -create_pins 0 -block_ring_bottom_layer_limit met3 -block_ring_top_layer_limit met2 -direction horizontal -layer met3 -nets {VSS VDD} -pad_core_ring_bottom_layer_limit met2 -set_to_set_distance 75.90 -spacing 3.66 -switch_layer_over_obs 0 -width 1.86 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 1] + 7.35]

# Power strap definition for layer met4:

set_db add_stripes_stacked_via_top_layer met4
set_db add_stripes_stacked_via_bottom_layer met1
set_db add_stripes_trim_antenna_back_to_shape {stripe}
set_db add_stripes_spacing_from_block 2.000
#add_stripes -create_pins 0 -block_ring_bottom_layer_limit met4 -block_ring_top_layer_limit met3 -direction vertical -layer met4 -nets {VSS VDD} -pad_core_ring_bottom_layer_limit met3 -set_to_set_distance 75.90 -spacing 3.66 -switch_layer_over_obs 0 -width 1.86 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 7.35]
add_stripes -create_pins 0 -block_ring_bottom_layer_limit met4 -block_ring_top_layer_limit met1 -direction vertical -layer met4 -nets {VSS VDD} -pad_core_ring_bottom_layer_limit met1 -set_to_set_distance 75.90 -spacing 3.66 -switch_layer_over_obs 0 -width 1.86 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 0] + 7.35]

# Power strap definition for layer met5:

set_db add_stripes_stacked_via_top_layer met5
set_db add_stripes_stacked_via_bottom_layer met4
set_db add_stripes_trim_antenna_back_to_shape {stripe}
set_db add_stripes_spacing_from_block 2.000
add_stripes -create_pins 1 -block_ring_bottom_layer_limit met5 -block_ring_top_layer_limit met4 -direction horizontal -layer met5 -nets {VSS VDD} -pad_core_ring_bottom_layer_limit met4 -set_to_set_distance 225.40 -spacing 17.68 -switch_layer_over_obs 0 -width 1.64 -area [get_db designs .core_bbox] -start [expr [lindex [lindex [get_db designs .core_bbox] 0] 1] + 5.62]

"""
    )
    return True


def efabless_ring_io(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerPlaceAndRouteTool), "IO ring instantiation only for par"
    assert isinstance(ht, TCLTool), "IO ring instantiation can only run on TCL tools"
    io_file = ht.get_setting("technology.sky130.io_file")
    ht.append(f"read_io_file {io_file} -no_die_size_adjust")
    p_nets = list(map(lambda s: s.name, ht.get_independent_power_nets()))
    g_nets = list(map(lambda s: s.name, ht.get_independent_ground_nets()))
    ht.append(f'''
        # Global net connections
        connect_global_net VDDA -type pg_pin -pin_base_name VDDA -verbose
        connect_global_net VDDIO -type pg_pin -pin_base_name VDDIO* -verbose
        connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VCCD* -verbose
        connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VCCHIB -verbose
        connect_global_net {p_nets[0]} -type pg_pin -pin_base_name VSWITCH -verbose
        connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSA -verbose
        connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSIO* -verbose
        connect_global_net {g_nets[0]} -type pg_pin -pin_base_name VSSD* -verbose
    ''')
    ht.append('''
        # IO fillers
        set io_fillers {sky130_ef_io__com_bus_slice_20um sky130_ef_io__com_bus_slice_10um sky130_ef_io__com_bus_slice_5um sky130_ef_io__com_bus_slice_1um}
        add_io_fillers -io_ring 1 -cells $io_fillers -side top -filler_orient r0
        add_io_fillers -io_ring 1 -cells $io_fillers -side right -filler_orient r270
        add_io_fillers -io_ring 1 -cells $io_fillers -side bottom -filler_orient r180
        add_io_fillers -io_ring 1 -cells $io_fillers -side left -filler_orient r90
    ''')
    ht.append(f'''
        # Core ring
        add_rings -follow io -layer met5 -nets {{ {p_nets[0]} {g_nets[0]} }} -offset 5 -width 13 -spacing 3
        route_special -connect pad_pin -nets {{ {p_nets[0]} {g_nets[0]} }} -detailed_log
    ''')
    ht.append('''
        # Prevent buffering on TIE_LO_ESD and TIE_HI_ESD
        set_dont_touch [get_db [get_db pins -if {.name == *TIE*ESD}] .net]
    ''')
    return True

def calibre_drc_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "Exlude SRAMs only in DRC"
    drc_box = ""
    for name in SKY130Tech.sky130_sram_names():
        drc_box += f"\nEXCLUDE CELL {name}"
    run_file = ht.drc_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(drc_box)
    return True


def pegasus_drc_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerDRCTool), "Exlude SRAMs only in DRC"
    drc_box = ""
    for name in SKY130Tech.sky130_sram_names():
        drc_box += f"\nexclude_cell {name}"
    run_file = ht.drc_ctl_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(drc_box)
    return True


def calibre_lvs_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Blackbox and filter SRAMs only in LVS"
    lvs_box = ""
    for name in SKY130Tech.sky130_sram_names():
        lvs_box += f"\nLVS BOX {name}"
        lvs_box += f"\nLVS FILTER {name} OPEN "
    run_file = ht.lvs_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write(lvs_box)
    return True


# required for sram22 since they use the 130a primiviites
def pegasus_lvs_add_130a_primitives(ht: HammerTool) -> bool:
    return True
    assert isinstance(ht, HammerLVSTool), "Blackbox and filter SRAMs only in LVS"
    lvs_box = ""
    for name in SKY130Tech.sky130_sram_primitive_names():
        lvs_box += f"""\nschematic_path "{name}" spice;"""
    # this is because otherwise lvs crashes with tons of stdcell-level pin mismatches
    lvs_box += f"""\nlvs_inconsistent_reduction_threshold -none;"""
    run_file = ht.lvs_ctl_file  # type: ignore
    with open(run_file, "r+") as f:
        # Remove SRAM SPICE file includes.
        pattern = "schematic_path.*({}).*spice;\n".format(
            "|".join(SKY130Tech.sky130_sram_primitive_names())
        )
        matcher = re.compile(pattern)
        contents = f.read()
        fixed_contents = contents + lvs_box
        f.seek(0)
        f.write(fixed_contents)
    return True


def pegasus_lvs_blackbox_srams(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Blackbox and filter SRAMs only in LVS"
    lvs_box = ""
    for name in (
        SKY130Tech.sky130_sram_names() # + SKY130Tech.sky130_sram_primitive_names()
    ):
        lvs_box += f"\nlvs_black_box {name} -gray"
    run_file = ht.lvs_ctl_file  # type: ignore
    with open(run_file, "r+") as f:
        # Remove SRAM SPICE file includes.
        pattern = "schematic_path.*({}).*spice;\n".format(
            "|".join(SKY130Tech.sky130_sram_names())
        )
        matcher = re.compile(pattern)
        contents = f.read()
        fixed_contents = matcher.sub("", contents) + lvs_box
        f.seek(0)
        f.write(fixed_contents)
    return True


def sram22_lvs_recognize_gates_all(ht: HammerTool) -> bool:
    assert isinstance(
        ht, HammerLVSTool
    ), "Change 'LVS RECOGNIZE GATES' from 'NONE' to 'ALL' for SRAM22"
    run_file = ht.lvs_run_file  # type: ignore
    with open(run_file, "a") as f:
        f.write("LVS RECOGNIZE GATES ALL")
    return True






def setup_calibre_lvs_deck(ht: HammerTool) -> bool:
    assert isinstance(ht, HammerLVSTool), "Modify Calibre LVS deck for LVS only"
    if not self.use_nda_files: return
    pattern = '.*({}).*\n'.format('|'.join(LVS_DECK_SCRUB_LINES))
    matcher = re.compile(pattern)

    source_paths = self.get_setting('technology.sky130.lvs_deck_sources')
    lvs_decks = self.config.lvs_decks
    if not lvs_decks:
        return
    for i in range(len(lvs_decks)):
        deck = lvs_decks[i]
        try:
            source_path = Path(source_paths[i])
        except IndexError:
            self.logger.error(
                'No corresponding source for LVS deck {}'.format(deck))
        if not source_path.exists():
            raise FileNotFoundError(f"LVS deck not found: {source_path}")
        dest_path = self.expand_tech_cache_path(str(deck.path))
        self.ensure_dirs_exist(dest_path)
        with open(source_path, 'r') as sf:
            with open(dest_path, 'w') as df:
                self.logger.info("Modifying LVS deck: {} -> {}".format
                    (source_path, dest_path))
                df.write(matcher.sub("", sf.read()))
                df.write(LVS_DECK_INSERT_LINES)
    return True


tech = SKY130Tech()
