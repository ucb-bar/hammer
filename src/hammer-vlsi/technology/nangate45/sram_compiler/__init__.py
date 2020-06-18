
import os, tempfile, subprocess

from hammer_vlsi import MMMCCorner, MMMCCornerType, HammerTool, \
                        HammerToolStep, HammerSRAMGeneratorTool, SRAMParameters
from hammer_vlsi.units import VoltageValue, TemperatureValue
from hammer_tech import Library, ExtraLibrary
from typing import NamedTuple, Dict, Any, List
from abc import ABCMeta, abstractmethod

class Nangate45SRAMGenerator(HammerSRAMGeneratorTool):
    def tool_config_prefix(self) -> str:
        return "sram_generator.nangate45"

    def version_number(self, version: str) -> int:
        return 0

    # Run generator for a single sram and corner
    def generate_sram(self, params: SRAMParameters, 
                      corner: MMMCCorner) -> ExtraLibrary:

        if "OPENROAD" not in os.environ:
            raise Exception("OPENROAD is not defined in environment!")
        openroad = os.path.realpath(
                    os.path.join(os.environ['OPENROAD'], "../.."))
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
