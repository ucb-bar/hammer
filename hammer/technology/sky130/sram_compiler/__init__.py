
import os, tempfile, subprocess
from pathlib import Path

from hammer.vlsi import MMMCCorner, MMMCCornerType, HammerTool, HammerToolStep, HammerSRAMGeneratorTool, SRAMParameters
from hammer.vlsi.units import VoltageValue, TemperatureValue
from hammer.tech import Library, ExtraLibrary
from typing import NamedTuple, Dict, Any, List
from abc import ABCMeta, abstractmethod

class SKY130SRAMGenerator(HammerSRAMGeneratorTool):
    def tool_config_prefix(self) -> str:
        return "sram_generator.sky130"

    def version_number(self, version: str) -> int:
        return 0

    # Run generator for a single sram and corner
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        cache_dir = os.path.abspath(self.technology.cache_dir)

        #TODO: this is really an abuse of the corner stuff
        if corner.type == MMMCCornerType.Setup:
            speed_name = "slow"
            speed = "SS"
            # self.logger.error("SKY130 SRAM cache does not support corner: {}".format(speed_name))
        elif corner.type == MMMCCornerType.Hold:
            speed_name = "fast"
            speed = "FF"
            # self.logger.error("SKY130 SRAM cache does not support corner: {}".format(speed_name))
        elif corner.type == MMMCCornerType.Extra:
            speed_name = "typical"
            speed = "TT"

        if params.family == "1rw" or params.family == "1rw1r":
            self.logger.info(f"Compiling {params.family} memories to OpenRAM instances")
            base_dir = self.get_setting("technology.sky130.openram_lib")
            s=round(round(params.width*params.depth/8, -3)/1000) # size in kiB
            w=params.width
            d=params.depth
            m=8
            sram_name = f"sky130_sram_{s}kbyte_{params.family}_{w}x{d}_{m}"
            #TODO: Hammer SRAMParameters doesn't have this info
            #TODO: replace this if OpenRAM characterization done for other corners
            # we only have typical lib for sky130 srams
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
                self.logger.error(f"SKY130 {params.family} SRAM cache does not support corner: {corner_str}")

            self.setup_sram_spice(sram_name)
            self.setup_sram_lef(sram_name)
            self.setup_sram_verilog(sram_name)
            # self.setup_sram_verilog(sram_name)
            return ExtraLibrary(prefix=None, library=Library(
                name=sram_name,
                nldm_liberty_file=lib_path,
                lef_file="{b}/{n}/{n}.lef".format(b=cache_dir,n=sram_name),
                gds_file="{b}/{n}/{n}.gds".format(b=base_dir,n=sram_name),
                spice_file="{b}/{n}/{n}.lvs.sp".format(b=cache_dir,n=sram_name),
                verilog_sim="{b}/{n}/{n}.v".format(b=cache_dir,n=sram_name),
                corner={'nmos': speed_name, 'pmos': speed_name, 'temperature': str(corner.temp.value_in_units("C")) + " C"},
                supplies={'VDD': str(corner.voltage.value_in_units("V")) + " V", 'GND': "0 V"},
                provides=[{'lib_type': "sram", 'vt': params.vt}]))
        else:
            self.logger.error("SKY130 SRAM cache does not support family:{f}".format(f=params.family))
            return ExtraLibrary(prefix=None, library=None)


    def setup_sram_spice(self,sram_name) -> None:
        source_path = Path(self.get_setting("technology.sky130.openram_lib")) / sram_name / f"{sram_name}.lvs.sp"
        dest_path = f"{os.path.abspath(self.technology.cache_dir)}/{sram_name}/{sram_name}.lvs.sp"
        self.technology.ensure_dirs_exist(dest_path)
        if not source_path.exists():
            raise FileNotFoundError(f"SRAM Spice file not found: {source_path}")        
        with open(source_path,'r') as sf:
            with open(dest_path,'w') as df:
                self.logger.info("Modifying SRAM SPICE deck: {} -> {}".format
                    (source_path, dest_path))
                for line in sf:
                    line = line.replace('sky130_fd_pr__pfet_01v8','pshort')
                    line = line.replace('sky130_fd_pr__nfet_01v8','nshort')
                    if sram_name == "sky130_sram_1kbyte_1rw1r_8x1024_8":
                        line = line.replace('wmask0[0]'    , 'wmask0')
                    df.write(line)


    def setup_sram_lef(self,sram_name) -> None:
        source_path = Path(self.get_setting("technology.sky130.openram_lib")) / sram_name / f"{sram_name}.lef"
        dest_path = f"{os.path.abspath(self.technology.cache_dir)}/{sram_name}/{sram_name}.lef"
        self.technology.ensure_dirs_exist(dest_path)
        if not source_path.exists():
            raise FileNotFoundError(f"SRAM LEF file not found: {source_path}")
        with open(source_path,'r') as sf:
            with open(dest_path,'w') as df:
                self.logger.info("Modifying SRAM LEF deck: {} -> {}".format
                    (source_path, dest_path))
                units=False
                for line in sf:
                    if line.strip().startswith("UNITS"):
                        units=True
                    if line.strip().startswith("END UNITS"):
                        units=False
                        continue
                    if not units:
                        df.write(line)


    def setup_sram_verilog(self, sram_name) -> None:
        """ Move 'mem' declaration before it is referenced in the verilog. """
        source_path = Path(self.get_setting("technology.sky130.openram_lib")) / sram_name / f"{sram_name}.v"
        dest_path = f"{os.path.abspath(self.technology.cache_dir)}/{sram_name}/{sram_name}.v"
        if not source_path.exists():
            raise FileNotFoundError(f"SRAM Spice file not found: {source_path}")
        self.technology.ensure_dirs_exist(dest_path)
        with open(source_path,'r') as sf:
            with open(dest_path,'w') as df:
                self.logger.info("Modifying SRAM Verilog deck: {} -> {}".format
                    (source_path, dest_path))
                lines = sf.readlines()
                insert_idx = 0
                for i,line in enumerate(lines):
                    if insert_idx == 0 and line.strip().startswith('always'):
                        insert_idx = i
                    elif line.strip() == "reg [DATA_WIDTH-1:0]    mem [0:RAM_DEPTH-1];":
                        lines.pop(i)
                        lines.insert(insert_idx,line)
                df.write(''.join(lines))

tool=SKY130SRAMGenerator
