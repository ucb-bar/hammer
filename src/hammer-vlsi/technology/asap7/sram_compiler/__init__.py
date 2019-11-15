
import os, tempfile, subprocess

from hammer_vlsi import MMMCCorner, MMMCCornerType, HammerTool, HammerToolStep, HammerSRAMGeneratorTool, SRAMParameters
from hammer_vlsi.units import VoltageValue, TemperatureValue
from hammer_tech import Library, ExtraLibrary
from typing import NamedTuple, Dict, Any, List
from abc import ABCMeta, abstractmethod

class ASAP7SRAMGenerator(HammerSRAMGeneratorTool):
    def tool_config_prefix(self) -> str:
        return "sram_generator.asap7"

    def version_number(self, version: str) -> int:
        return 0

    # Run generator for a single sram and corner
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        tech_cache_dir = os.path.abspath(self.technology.cache_dir)
        base_dir=os.path.join(self.tool_dir, "memories")
        if params.family == "1RW" or params.family == "2RW":
            fam_code = params.family
        else:
            self.logger.error("ASAP7 SRAM cache does not support family:{f}".format(f=params.family))
        #TODO: this is really an abuse of the corner stuff
        #TODO: when we have matching corners remove real_corner and symlink junk
        if corner.type == MMMCCornerType.Setup:
            speed_name = "slow"
        elif corner.type == MMMCCornerType.Hold:
            speed_name = "fast"
        elif corner.type == MMMCCornerType.Extra:
            speed_name = "typical"
        corner_str = "PVT_{volt}V_{temp}C".format(
                volt = str(corner.voltage.value_in_units("V")).replace(".","P"),
                temp = str(int(corner.temp.value_in_units("C"))).replace(".","P"))
        sram_name = "SRAM{fc}{d}x{w}".format(
                fc=fam_code,
                d=params.depth,
                w=params.width)
        lib_path ="{t}/{n}_{c}.lib".format(t=tech_cache_dir,n=sram_name,c=corner_str)
        if not os.path.exists(lib_path):
            os.symlink("{b}/lib/{n}_lib/{n}_{c}.lib".format(b=base_dir,n=sram_name,c=corner_str), "{t}/{n}_{c}.lib".format(t=tech_cache_dir,n=sram_name,c=corner_str))
        lib = ExtraLibrary(prefix=None, library=Library(
                name=sram_name,
                nldm_liberty_file=lib_path,
                lef_file="{b}/lef/{n}_x4.lef".format(b=base_dir,n=sram_name),
                gds_file="{b}/gds/{n}_x4.gds".format(b=base_dir,n=sram_name),
                verilog_sim="{b}/behavioral/sram_behav_models.sv".format(b=base_dir),
                corner = {'nmos': speed_name, 'pmos': speed_name, 'temperature': str(corner.temp.value_in_units("C")) +" C"},
                supplies = {'VDD': str(corner.voltage.value_in_units("V")) + " V", 'GND': "0 V" },
                provides = [{'lib_type': "sram", 'vt': params.vt}]))  # type: ExtraLibrary
        return lib

tool=ASAP7SRAMGenerator
