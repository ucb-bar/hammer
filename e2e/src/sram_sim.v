`timescale 1ns/10ps

module sram_sim (clock, we, wmask, addr, din, dout);

parameter DATA_WIDTH = 4;
parameter ADDR_WIDTH = 6;
parameter WMASK_WIDTH = 2;
parameter RAM_DEPTH = 1 << ADDR_WIDTH;

input clock;
input we;

input [WMASK_WIDTH-1:0] wmask;
input [ADDR_WIDTH-1:0]  addr;
input [DATA_WIDTH-1:0]  din;
output [DATA_WIDTH-1:0] dout;

reg we_reg;

reg [WMASK_WIDTH-1:0] wmask_reg;
reg [ADDR_WIDTH-1:0]  addr_reg;
reg [DATA_WIDTH-1:0]  din_reg;

always @(posedge clock) begin
  we_reg <= we;
  wmask_reg <= wmask;
  addr_reg <= addr;
  din_reg <= din;
end

`SRAM mem0 (
  .clk(clock),
  .we(we_reg),
  .wmask(wmask_reg),
  .addr(addr_reg),
  .din(din_reg),
  .dout(dout)
);

endmodule