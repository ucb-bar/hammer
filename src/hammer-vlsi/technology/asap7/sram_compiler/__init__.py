
import os, tempfile, subprocess, math

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

        # Generate Verilog file from template
        verilog_path ="{t}/{n}.v".format(t=tech_cache_dir,n=sram_name)
        with open(verilog_path, 'w') as f:
            if params.family == "1RW":
                f.write("""
`timescale 1ns/100fs

module {NAME} (A,CE,WEB,OEB,CSB,I,O);

input 				CE;
input 				WEB;
input 				OEB;
input 				CSB;

input 	[{NUMADDR}-1:0] 		A;
input 	[{WORDLENGTH}-1:0] 	I;
output 	[{WORDLENGTH}-1:0] 	O;

reg     [{WORDLENGTH}-1:0]	memory[{NUMWORDS}-1:0];
reg  	[{WORDLENGTH}-1:0]	data_out;
wire 	[{WORDLENGTH}-1:0] 	O;

wire 				RE;
wire 				WE;
and u1 (RE, ~CSB, ~OEB);
and u2 (WE, ~CSB, ~WEB);

// Initialization for simulation
integer i;
initial begin
    for (i = 0; i < {NUMWORDS}; i = i + 1) begin
        memory[i] = {{{RAND_WIDTH}{{$urandom()}}}};
    end
    data_out = {{{RAND_WIDTH}{{$urandom()}}}};
end

always @ (posedge CE) begin
	if (RE)
		data_out <= memory[A];
	if (WE)
		memory[A] <= I;
end

assign O = data_out;

endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name, RAND_WIDTH=math.ceil(params.width/32)))
            else:
                f.write("""
`timescale 1ns/100fs

module {NAME} (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input 				CE1;
input 				CE2;
input 				WEB1;
input 				WEB2;
input 				OEB1;
input 				OEB2;
input 				CSB1;
input 				CSB2;

input 	[{NUMADDR}-1:0] 		A1;
input 	[{NUMADDR}-1:0] 		A2;
input 	[{WORDLENGTH}-1:0] 	I1;
input 	[{WORDLENGTH}-1:0] 	I2;
output 	[{WORDLENGTH}-1:0] 	O1;
output 	[{WORDLENGTH}-1:0] 	O2;

reg     [{WORDLENGTH}-1:0]	memory[{NUMWORDS}-1:0];
reg  	[{WORDLENGTH}-1:0]	data_out1;
reg  	[{WORDLENGTH}-1:0]	data_out2;
wire 	[{WORDLENGTH}-1:0] 	O1;
wire  	[{WORDLENGTH}-1:0]	O2;

wire 				RE1;
wire 				RE2;
wire 				WE1;
wire 				WE2;
and u1 (RE1, ~CSB1, ~OEB1);
and u2 (RE2, ~CSB2, ~OEB2);
and u3 (WE1, ~CSB1, ~WEB1);
and u4 (WE2, ~CSB2, ~WEB2);

// Initialization for simulation
integer i;
initial begin
    for (i = 0; i < {NUMWORDS}; i = i + 1) begin
        memory[i] = {{{RAND_WIDTH}{{$urandom()}}}};
    end
    data_out1 = {{{RAND_WIDTH}{{$urandom()}}}};
    data_out2 = {{{RAND_WIDTH}{{$urandom()}}}};
end

always @ (posedge CE1) begin
	if (RE1)
		data_out1 <= memory[A1];
	if (WE1)
		memory[A1] <= I1;
end

always @ (posedge CE2) begin
	if (RE2)
		data_out2 <= memory[A2];
	if (WE2)
		memory[A2] <= I2;
end

assign O1 = data_out1;
assign O2 = data_out2;

endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name, RAND_WIDTH=math.ceil(params.width/32)))

        #lib_path ="{t}/{n}_{c}.lib".format(t=tech_cache_dir,n=sram_name,c=corner_str)
        #if not os.path.exists(lib_path):
        #    os.symlink("{b}/lib/{n}_lib/{n}_{c}.lib".format(b=base_dir,n=sram_name,c=corner_str), "{t}/{n}_{c}.lib".format(t=tech_cache_dir,n=sram_name,c=corner_str))
        lib = ExtraLibrary(prefix=None, library=Library(
                name=sram_name,
                nldm_liberty_file="{b}/lib/{n}_lib/{n}_{c}.lib".format(b=base_dir,n=sram_name,c=corner_str),
                lef_file="{b}/lef/{n}_x4.lef".format(b=base_dir,n=sram_name),
                gds_file="{b}/gds/{n}_x4.gds".format(b=base_dir,n=sram_name),
                #verilog_sim="{b}/behavioral/sram_behav_models.v".format(b=base_dir),
                verilog_sim=verilog_path,
                corner = {'nmos': speed_name, 'pmos': speed_name, 'temperature': str(corner.temp.value_in_units("C")) +" C"},
                supplies = {'VDD': str(corner.voltage.value_in_units("V")) + " V", 'GND': "0 V" },
                provides = [{'lib_type': "sram", 'vt': params.vt}]))  # type: ExtraLibrary
        return lib

tool=ASAP7SRAMGenerator
