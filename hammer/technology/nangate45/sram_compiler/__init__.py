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
        
        # Check what type of installation we have
        if not os.path.exists(openroad + "flow/designs/src/tinyRocket"):
            # This uses the OpenRoad repository
            base_dir = os.path.join(openroad, "test/Nangate45/")
        else: 
            base_dir = os.path.join(openroad, "flow/designs/src/tinyRocket")

        tech_cache_dir = os.path.abspath(self.technology.cache_dir)

        if params.family == "1RW" or  params.family == "1R1W" or params.family =="2RmW" :
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
        sram_name_v="fakeram45_{fam}_{d}x{w}".format(
          d=params.depth,
          w=params.width,
          fam=params.family)
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
        verilog_path = "{t}/{n}.v".format(t=tech_cache_dir, n=sram_name_v)
        with open(verilog_path, 'w') as f:
            if params.family == "1R1W" :
                specify = ""
                for specify_j in range(0, params.width):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge ce_in, %s R0_data[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                            specify += "$setuphold(posedge ce_in, %s W0_data[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                        else:
                            specify += "$setuphold(posedge ce_in, %s R0_data[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                            specify += "$setuphold(posedge ce_in, %s W0_data[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                    specify += "(ce_in => R0_data[%d]) = 0;\n" % (specify_j)
                    specify += "(ce_in => W0_data[%d]) = 0;\n" % (specify_j)
                for specify_k in range(0, math.ceil(math.log2(params.depth))):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge ce_in, %s R0_addr[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                            specify += "$setuphold(posedge ce_in, %s W0_addr[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                        else:
                            specify += "$setuphold(posedge ce_in, %s R0_addr[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                            specify += "$setuphold(posedge ce_in, %s W0_addr[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                f.write("""
`timescale 1ns/100fs
module {NAME} (
  input  [{NUMADDR}-1:0] R0_addr,
  input  [{NUMADDR}-1:0] W0_addr,
  input                   R0_clk,
  input                   W0_clk,
  output [{WORDLENGTH}-1:0] R0_data,
  input  [{WORDLENGTH}-1:0] W0_data,
  
  input                   R0_en,
  input                   W0_en
);

  reg [{WORDLENGTH}-1:0] ram [0:{NUMWORDS}-1];

  wire [{NUMADDR}-1:0] ram_R_0_addr;
  wire [{WORDLENGTH}-1:0] ram_R_0_data;
  wire [{WORDLENGTH}-1:0] ram_W_0_data;
  wire [{NUMADDR}-1:0] ram_W_0_addr;
  wire  ram_W_0_mask;
  wire  ram_W_0_en;
  reg [{NUMADDR}-1:0] ram_R_0_addr_pipe_0;
  assign ram_R_0_addr = ram_R_0_addr_pipe_0;
  assign ram_R_0_data = ram[ram_R_0_addr];
  assign ram_W_0_data = W0_data;
  assign ram_W_0_addr = W0_addr;
  assign ram_W_0_mask = 1'h1;
  assign ram_W_0_en = W0_en ;
  assign R0_data = ram_R_0_data;

  always @(posedge W0_clk) begin
    if (ram_W_0_en & ram_W_0_mask) begin
      ram[ram_W_0_addr] <= ram_W_0_data;
    end
  end
  always @(posedge R0_clk) begin
    if (R0_en ) begin
      ram_R_0_addr_pipe_0 <= R0_addr;
    end
  end

`ifndef SYNTHESIS
`ifdef  RANDOMIZE_REG_INIT 

integer i;
initial begin
    for (i = 0; i < {NUMWORDS}; i = i + 1) begin
        ram[i] = {{{WORDLENGTH}{{$urandom()}}}};
end 
ram_R_0_addr_pipe_0 = {{{WORDLENGTH}{{$urandom()}}}};
end // initial
`endif // RANDOMIZE
`endif // SYNTHESIS
endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name_v,
           RAND_WIDTH=math.ceil(params.width / 32), specify=specify))
            elif params.family == "2RmW":
                specify = ""
                for specify_j in range(0, params.width):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge ce_in, %s R0_data[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                            specify += "$setuphold(posedge ce_in, %s W0_data[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                        else:
                            specify += "$setuphold(posedge ce_in, %s R0_data[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                            specify += "$setuphold(posedge ce_in, %s W0_data[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                    specify += "(ce_in => R0_data[%d]) = 0;\n" % (specify_j)
                    specify += "(ce_in => W0_data[%d]) = 0;\n" % (specify_j)
                for specify_k in range(0, math.ceil(math.log2(params.depth))):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge ce_in, %s R0_addr[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                            specify += "$setuphold(posedge ce_in, %s W0_addr[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                        else:
                            specify += "$setuphold(posedge ce_in, %s R0_addr[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                            specify += "$setuphold(posedge ce_in, %s W0_addr[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                f.write("""
`timescale 1ns/100fs
module {NAME} (
  input  [{NUMADDR}-1:0] R0_addr,
  input  [{NUMADDR}-1:0] W0_addr,
  input                   R0_clk,
  input                   W0_clk,
  output [{WORDLENGTH}-1:0] R0_data,
  input  [{WORDLENGTH}-1:0] W0_data,
  input                   W0_wmask,
  input                   R0_en,
  input                   W0_en
);

  reg [{WORDLENGTH}-1:0] ram [0:{NUMWORDS}-1];

  wire [{NUMADDR}-1:0] ram_R_0_addr;
  wire [{WORDLENGTH}-1:0] ram_R_0_data;
  wire [{WORDLENGTH}-1:0] ram_W_0_data;
  wire [{NUMADDR}-1:0] ram_W_0_addr;
  wire  ram_W_0_mask;
  wire  ram_W_0_en;
  reg [{NUMADDR}-1:0] ram_R_0_addr_pipe_0;
  assign ram_R_0_addr = ram_R_0_addr_pipe_0;
  assign ram_R_0_data = ram[ram_R_0_addr];
  assign ram_W_0_data = W0_data;
  assign ram_W_0_addr = W0_addr;
  assign ram_W_0_en = W0_en ;
  assign R0_data = ram_R_0_data;
  assign ram_W_0_mask = W0_wmask;

  always @(posedge W0_clk) begin
    if (ram_W_0_en & ram_W_0_mask) begin
      ram[ram_W_0_addr] <= ram_W_0_data;
    end
  end
  always @(posedge R0_clk) begin
    if (R0_en ) begin
      ram_R_0_addr_pipe_0 <= R0_addr;
    end
  end

`ifndef SYNTHESIS
`ifdef  RANDOMIZE_REG_INIT 

integer i;
initial begin
    for (i = 0; i < {NUMWORDS}; i = i + 1) begin
        ram[i] = {{{WORDLENGTH}{{$urandom()}}}};
end 
ram_R_0_addr_pipe_0 = {{{WORDLENGTH}{{$urandom()}}}};
end // initial
`endif // RANDOMIZE
`endif // SYNTHESIS
endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name_v,
           RAND_WIDTH=math.ceil(params.width / 32), specify=specify))
            elif params.family == "1RW":
                specify = ""
                for specify_j in range(0, params.width):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge ce_in, %s R0_data[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                            specify += "$setuphold(posedge ce_in, %s W0_data[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_j)
                        else:
                            specify += "$setuphold(posedge ce_in, %s R0_data[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                            specify += "$setuphold(posedge ce_in, %s W0_data[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_j)
                    specify += "(ce_in => R0_data[%d]) = 0;\n" % (specify_j)
                    specify += "(ce_in => W0_data[%d]) = 0;\n" % (specify_j)
                for specify_k in range(0, math.ceil(math.log2(params.depth))):
                    for specify_i in range(0, 2):
                        if specify_i == 0:
                            specify += "$setuphold(posedge ce_in, %s R0_addr[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                            specify += "$setuphold(posedge ce_in, %s W0_addr[%d], 0, 0, NOTIFIER);\n" % ("posedge", specify_k)
                        else:
                            specify += "$setuphold(posedge ce_in, %s R0_addr[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                            specify += "$setuphold(posedge ce_in, %s W0_addr[%d], 0, 0, NOTIFIER);\n" % ("negedge", specify_k)
                f.write("""
`timescale 1ns/100fs
module {NAME} (
  input  [{NUMADDR}-1:0] RW0_addr,
  input                   RW0_clk,
  input  [{WORDLENGTH}-1:0] RW0_wdata,
  output [{WORDLENGTH}-1:0] RW0_rdata,
  input                   RW0_en,
  input                   RW0_wmode,
  input                   RW0_wmask
);

  reg [{WORDLENGTH}-1:0] ram [0:{NUMWORDS}-1];

  wire                    ram_RW_0_r_en;
  wire [{NUMADDR}-1:0]    ram_RW_0_r_addr;
  wire [{WORDLENGTH}-1:0] ram_RW_0_r_data;
  wire [{WORDLENGTH}-1:0] ram_RW_0_w_data;
  wire [{NUMADDR}-1:0]    ram_RW_0_w_addr;
  wire                    ram_RW_0_w_mask;
  wire                    ram_RW_0_w_en;
  reg                     ram_RW_0_r_en_pipe_0;
  reg [{NUMADDR}-1:0]     ram_RW_0_r_addr_pipe_0;

  assign ram_RW_0_r_en   = ram_RW_0_r_en_pipe_0;
  assign ram_RW_0_r_addr = ram_RW_0_r_addr_pipe_0;
  assign ram_RW_0_r_data = ram[ram_RW_0_r_addr];

  assign ram_RW_0_w_data = RW0_wdata;
  assign ram_RW_0_w_addr = RW0_addr;
  assign ram_RW_0_w_mask = RW0_wmask;
  assign ram_RW_0_w_en   = RW0_en & RW0_wmode;

  assign RW0_rdata = ram_RW_0_r_data;

  always @(posedge RW0_clk) begin
    if (ram_RW_0_w_en & ram_RW_0_w_mask) begin
      ram[ram_RW_0_w_addr] <= ram_RW_0_w_data;
    end
    ram_RW_0_r_en_pipe_0 <= RW0_en & ~RW0_wmode;
    if (RW0_en & ~RW0_wmode) begin
      ram_RW_0_r_addr_pipe_0 <= RW0_addr;
    end
  end

`ifndef SYNTHESIS
`ifdef  RANDOMIZE_REG_INIT 

integer i;
initial begin
    for (i = 0; i < {NUMWORDS}; i = i + 1) begin
        ram[i] = {{{WORDLENGTH}{{$urandom()}}}};
end 
ram_RW_0_r_en_pipe_0 = {{{WORDLENGTH}{{$urandom()}}}};
ram_RW_0_r_addr_pipe_0 = {{{WORDLENGTH}{{$urandom()}}}};
end // initial
`endif // RANDOMIZE
`endif // SYNTHESIS
endmodule
""".format(NUMADDR=math.ceil(math.log2(params.depth)), NUMWORDS=params.depth, WORDLENGTH=params.width, NAME=sram_name_v,
           RAND_WIDTH=math.ceil(params.width / 32), specify=specify))

        return ExtraLibrary(
          prefix=None, 
          library=Library(
            name=sram_name_v,
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
