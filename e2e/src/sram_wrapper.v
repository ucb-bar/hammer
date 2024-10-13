
module sram_wrapper (
    clock,we,wmask,addr,din,dout
);

  parameter DATA_WIDTH = 4 ;
  parameter ADDR_WIDTH = 6 ;
  parameter WMASK_WIDTH = 2 ;
  parameter RAM_DEPTH = 1 << ADDR_WIDTH;

  input  clock; // clock
  input  we; // write enable
  input [WMASK_WIDTH-1:0] wmask; // write mask
  input [ADDR_WIDTH-1:0]  addr; // address
  input [DATA_WIDTH-1:0]  din; // data in
  output [DATA_WIDTH-1:0] dout; // data out

  // need these internal registers for sram_wrapper module to synthesize properly
  reg  we_reg; // write enable
  reg [WMASK_WIDTH-1:0] wmask_reg; // write mask
  reg [ADDR_WIDTH-1:0]  addr_reg; // address
  reg [DATA_WIDTH-1:0]  din_reg; // data in
  
  always@(posedge clock) begin
      we_reg <= we;
      wmask_reg <= wmask;
      addr_reg <= addr;
      din_reg <= din;
  end

  sram22_64x4m4w2 mem0 (
  .clk(clock),.we(we_reg),.wmask(wmask_reg),
  .addr(addr_reg),.din(din_reg),.dout(dout)
  );

endmodule
