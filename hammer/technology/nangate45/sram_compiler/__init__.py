# sram generator for the nangate45 packaged with the OpenROAD-flow
#
# See LICENSE for licence details.

import os, tempfile, subprocess
import math
import importlib.resources

from hammer.vlsi import MMMCCorner, MMMCCornerType, HammerTool, \
                        HammerToolStep, HammerSRAMGeneratorTool, SRAMParameters
from hammer.vlsi.vendor import OpenROADTool
from hammer.vlsi.units import VoltageValue, TemperatureValue
from hammer.tech import Library, ExtraLibrary, Corner, Provide, Supplies
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

      # Generate Verilog file from template
        verilog_path = "{t}/{n}.v".format(t=tech_cache_dir, n=sram_name)
        with open(verilog_path, 'w') as f:
            if params.family == "1RW":
                specify = ""
                for specify_j in range(0, params.width):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge CE, %s I[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                        else:
                            specify += "$setuphold(posedge CE, %s I[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                    specify += "(CE => O[%d]) = 0;\n" % (specify_j)
                for specify_k in range(0, math.ceil(math.log2(params.depth))):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge CE, %s A[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                        else:
                            specify += "$setuphold(posedge CE, %s A[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                f.write("""
`timescale 1ns/100fs

module {NAME} (A,CE,WEB,OEB,CSB,I,O);

input CE;
input WEB;
input OEB;
input CSB;

input  [{NUMADDR}-1:0] A;
input  [{WORDLENGTH}-1:0] I;
output [{WORDLENGTH}-1:0] O;

reg     [{WORDLENGTH}-1:0] memory[{NUMWORDS}-1:0];
reg     [{WORDLENGTH}-1:0] data_out;
wire    [{WORDLENGTH}-1:0] O;

wire RE;
wire WE;
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

reg NOTIFIER;
specify
{specify}
endspecify

assign O = data_out;

endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name,
           RAND_WIDTH=math.ceil(params.width / 32), specify=specify))
            else:
                specify = ""

                for specify_j in range(0, params.width):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge CE1, %s I1[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                            specify += "$setuphold(posedge CE2, %s I2[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                        else:
                            specify += "$setuphold(posedge CE1, %s I1[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                            specify += "$setuphold(posedge CE2, %s I2[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                    specify += "(CE1 => O1[%d]) = 0;\n" % (specify_j)
                    specify += "(CE2 => O2[%d]) = 0;\n" % (specify_j)
                for specify_k in range(0, math.ceil(math.log2(params.depth))):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge CE1, %s A1[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                            specify += "$setuphold(posedge CE2, %s A2[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                        else:
                            specify += "$setuphold(posedge CE1, %s A1[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                            specify += "$setuphold(posedge CE2, %s A2[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                f.write("""
`timescale 1ns/100fs

module {NAME} (A1,A2,CE1,CE2,WEB1,WEB2,OEB1,OEB2,CSB1,CSB2,I1,I2,O1,O2);

input CE1;
input CE2;
input WEB1;
input WEB2;
input OEB1;
input OEB2;
input CSB1;
input CSB2;

input  [{NUMADDR}-1:0]    A1;
input  [{NUMADDR}-1:0]    A2;
input  [{WORDLENGTH}-1:0] I1;
input  [{WORDLENGTH}-1:0] I2;
output [{WORDLENGTH}-1:0] O1;
output [{WORDLENGTH}-1:0] O2;

reg     [{WORDLENGTH}-1:0] memory[{NUMWORDS}-1:0];
reg     [{WORDLENGTH}-1:0] data_out1;
reg     [{WORDLENGTH}-1:0] data_out2;
wire    [{WORDLENGTH}-1:0] O1;
wire    [{WORDLENGTH}-1:0] O2;

wire RE1;
wire RE2;
wire WE1;
wire WE2;
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

reg NOTIFIER;
specify
{specify}
endspecify

assign O1 = data_out1;
assign O2 = data_out2;

endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name,
           RAND_WIDTH=math.ceil(params.width / 32), specify=specify))

        return ExtraLibrary(
          prefix=None, 
          library=Library(
            name=sram_name,
            nldm_liberty_file=dst_lib,
            lef_file=dst_lef,
            verilog_sim=verilog_path,
            corner=Corner(
              nmos="typical",
              pmos="typical",
              temperature=str(corner.temp.value_in_units("C")) +" C"
            ),
            supplies=Supplies(
              VDD=str(corner.voltage.value_in_units("V")) + " V",
              GND="0 V"
            ),
            provides=[Provide(lib_type="sram", vt=params.vt)]))

tool=Nangate45SRAMGenerator
