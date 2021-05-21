
import os, tempfile, subprocess

from hammer_vlsi import MMMCCorner, MMMCCornerType, HammerTool, HammerToolStep, HammerSRAMGeneratorTool, SRAMParameters
from hammer_vlsi.units import VoltageValue, TemperatureValue
from hammer_tech import Library, ExtraLibrary
from typing import NamedTuple, Dict, Any, List
from abc import ABCMeta, abstractmethod

class SKY130SRAMGenerator(HammerSRAMGeneratorTool):
    def tool_config_prefix(self) -> str:
        return "sram_generator.skywater"

    def version_number(self, version: str) -> int:
        return 0

    # Run generator for a single sram and corner
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        tech_cache_dir = os.path.abspath(self.technology.cache_dir)

        #TODO: this is really an abuse of the corner stuff
        if corner.type == MMMCCornerType.Setup:
            speed_name = "slow"
            speed = "SS"
        elif corner.type == MMMCCornerType.Hold:
            speed_name = "fast"
            speed = "FF"
        elif corner.type == MMMCCornerType.Extra:
            speed_name = "typical"
            speed = "TT"

        # Different target memories based on port count
        # if params.family == "1rw":
        #     self.logger.info("Compiling 1rw memories to DFFRAM instances")
        #     base_dir = self.get_setting("technology.sky130.dffram_lib")
        #     fam_code = params.family
        #     sram_name = "RAM{d}x{w}".format(
        #         d=params.depth,
        #         w=params.width)
        #     #TODO: need real libs (perhaps run Liberate here?)
        #     #For now, use the dummy lib for all corners
        #     corner_str = "" #
        #     lib_path = "{b}/{n}.lib".format(
        #         b=base_dir,
        #         n=sram_name)
        #     if not os.path.exists(lib_path):
        #         self.logger.error("SKY130 1rw1r SRAM cache does not support corner: {c}".format(c=corner_str))
        #     return ExtraLibrary(prefix=None, library=Library(
        #         name=sram_name,
        #         nldm_liberty_file=lib_path,
        #         lef_file="{b}/{n}/{n}.lef".format(b=base_dir,n=sram_name),
        #         #TODO: GDS not generated. Unclear which DEF to use?
        #         #gds_file="{b}/{n}/{n}.gds".format(b=base_dir,n=sram_name),
        #         spice_file="{b}/{n}/{n}.spice".format(b=base_dir,n=sram_name),
        #         #TODO: Will not work as-is for behav. sim (this is a structural netlist referencing std. cells)
        #         #Need to add std cell behavioral Verilog to sim.inputs.input_files
        #         verilog_sim="{b}/{n}/{n}.nl.v".format(b=base_dir,n=sram_name),
        #         corner={'nmos': speed_name, 'pmos': speed_name, 'temperature': str(corner.temp.value_in_units("C")) + " C"},
        #         supplies={'VDD': str(corner.voltage.value_in_units("V")) + " V", 'GND': "0 V"},
        #         provides=[{'lib_type': "sram", 'vt': params.vt}]))
        # elif params.family == "1rw1r":
        if params.family == "1rw":
            self.logger.info("Compiling 1rw1r memories to OpenRAM instances")
            base_dir = self.get_setting("technology.skywater.openram_lib")
            fam_code = params.family
            s=round(round(params.width*params.depth/8, -3)/1000) # size in kiB
            w=params.width
            d=params.depth
            m=8
            sram_name = f"sky130_sram_{s}kbyte_1rw1r_{w}x{d}_{m}"
            print(f"SRAM_NAME: {sram_name}")
            #TODO: Hammer SRAMParameters doesn't have this info
            #TODO: replace this if OpenRAM characterization done for other corners
            #For now, use typical lib for all corners
            corner_str = "TT_1p8V_25C"
            #corner_str = "{speed}_{volt}V_{temp}C".format(
            #        speed = speed,
            #        volt = str(corner.voltage.value_in_units("V")).replace(".","p"),
            #        temp = str(int(corner.temp.value_in_units("C"))).replace(".","p"))
            lib_path = "{b}/{n}/{n}_{c}.lib".format(
                b=base_dir,
                n=sram_name,
                c=corner_str)
            if not os.path.exists(lib_path):
                self.logger.error("SKY130 1rw1r SRAM cache does not support corner: {c}".format(c=corner_str))
            return ExtraLibrary(prefix=None, library=Library(
                name=sram_name,
                nldm_liberty_file=lib_path,
                lef_file="{b}/{n}/{n}.lef".format(b=base_dir,n=sram_name),
                gds_file="{b}/{n}/{n}.gds".format(b=base_dir,n=sram_name),
                spice_file="{b}/{n}/{n}.lvs.sp".format(b=base_dir,n=sram_name),
                verilog_sim="{b}/{n}/{n}.v".format(b=base_dir,n=sram_name),
                corner={'nmos': speed_name, 'pmos': speed_name, 'temperature': str(corner.temp.value_in_units("C")) + " C"},
                supplies={'VDD': str(corner.voltage.value_in_units("V")) + " V", 'GND': "0 V"},
                provides=[{'lib_type': "sram", 'vt': params.vt}]))
        else:
            self.logger.error("SKY130 SRAM cache does not support family:{f}".format(f=params.family))
            return ExtraLibrary(prefix=None, library=None)

tool=SKY130SRAMGenerator
