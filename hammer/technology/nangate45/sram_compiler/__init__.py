# sram generator for the nangate45 packaged with the OpenROAD-flow
#
# See LICENSE for licence details.

import os, tempfile, subprocess

from hammer.vlsi import MMMCCorner, MMMCCornerType, HammerTool, \
                        HammerToolStep, HammerSRAMGeneratorTool, SRAMParameters
from hammer.vlsi.vendor import OpenROADTool
from hammer.vlsi.units import VoltageValue, TemperatureValue
from hammer.tech import Library, ExtraLibrary
from typing import NamedTuple, Dict, Any, List, Optional
from abc import ABCMeta, abstractmethod

class Nangate45SRAMGenerator(OpenROADTool, HammerSRAMGeneratorTool):

    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None

    def tool_config_prefix(self) -> str:
        return "sram_generator.nangate45"

    def version_number(self, version: str) -> int:
        return 0

    # Run generator for a single sram and corner
    def generate_sram(self, params: SRAMParameters, 
                      corner: MMMCCorner) -> ExtraLibrary:

        self.validate_openroad_installation()
        openroad = self.openroad_flow_path()
        base_dir = os.path.join(openroad, "flow/designs/src/tinyRocket")

        tech_cache_dir = os.path.abspath(self.technology.cache_dir)
        if params.family == "1RW":
            fam_code = params.family
        else:
            self.logger.error(
              "Nangate45 SRAM cache does not support family:{f}".format(
              f=params.family))

        corner_str = "PVT_{volt}V_{temp}C".format(
          volt = str(corner.voltage.value_in_units("V")).replace(".","P"),
          temp = str(int(corner.temp.value_in_units("C"))).replace(".","P"))

        sram_name = "fakeram45_{d}x{w}".format(
          d=params.depth,
          w=params.width)

        # NOTE: fakemem libs don't define a corner
        src_lib = "{}/{}.lib".format(base_dir, sram_name)
        dst_lib ="{}/{}_{}.lib".format(tech_cache_dir, sram_name, corner_str)

        src_lef = "{}/{}.lef".format(base_dir, sram_name)
        dst_lef ="{}/{}.lef".format(tech_cache_dir, sram_name)

        if not os.path.exists(dst_lib):
          os.symlink(src_lib, dst_lib)

        if not os.path.exists(dst_lef):
          os.symlink(src_lef, dst_lef)

        return ExtraLibrary(
          prefix=None, 
          library=Library(
            name=sram_name,
            nldm_liberty_file=dst_lib,
            lef_file=dst_lef,
            corner = {
              'nmos': "typical",
              'pmos': "typical",
              'temperature': str(corner.temp.value_in_units("C")) +" C"
            },
            supplies = {
              'VDD': str(corner.voltage.value_in_units("V")) + " V", 
              'VSS': "0 V" 
            },
            provides = [{'lib_type': "sram", 'vt': params.vt}]))

tool=Nangate45SRAMGenerator
