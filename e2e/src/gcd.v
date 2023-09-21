`timescale 1ns / 1ps
//=========================================================================
// RTL Model of GCD Unit Control
//-------------------------------------------------------------------------
//

module gcd_control
( 
	input clk, reset, operands_val, result_rdy,
	input B_zero, A_lt_B,
	output reg result_val, operands_rdy,
	output reg [1:0] A_mux_sel,
	output reg B_mux_sel, A_en, B_en
);

// Describe the control part as a stage machine

// Define state bits
parameter CALC = 2'b00;
parameter IDLE = 2'b10;
parameter DONE = 2'b01;

// Note that the only flip flop in the design is "state",
// nextstate must also be declared as a reg because
// it is reference from the always @* block, even though
// it isn't actually a register and is only a wire
reg [1:0] state;
reg [1:0] nextstate;



// Combinational logic decides what the next stage should be
always @* begin

	// Start by defining default values
	nextstate = state;// Stay in the same state by default
	// Only want to allow A/B registers to take new values when
	// we are sure the data on their inputs is valid
	A_en = 0;
	B_en = 0;
	result_val = 0;
	operands_rdy = 0;
	
	A_mux_sel = 0;
	B_mux_sel = 0;
	
	case (state)
	
		//IDLE STATE
		IDLE : begin
		    B_mux_sel = 0;
			operands_rdy = 1;
			if(operands_val == 1'b1) begin
				nextstate = CALC;
				A_en = 1;
				B_en = 1;
			end else begin
				nextstate = IDLE;
			end
		
		end
		
		//CALC STATE
		CALC : begin
			if(A_lt_B == 1'b1) begin
				//SWAP
				B_mux_sel = 1;
				A_mux_sel = 1;
				A_en = 1;
				B_en = 1;
				nextstate = CALC;
			end else if (B_zero == 1'b0) begin
			    B_mux_sel = 0;
				//SUBTRACT
				A_mux_sel = 2;
				A_en = 1;
				nextstate = CALC;
			end else begin
				//DONE
				nextstate = DONE;
				B_mux_sel = 0;
			end
		
		end
		
		//DONE STATE
		DONE : begin
		    B_mux_sel = 0;
			// see if outside is ready to take the result
			// if so, send it, and say that operands are ready
			// to take new values
            result_val = 1;
			if (result_rdy == 1'b1) begin
				nextstate = IDLE;
			// if not, stay in this state until the outside is ready for the result
			end else begin
				nextstate = DONE;
			end
		end
	
	endcase


end


// Sequential part of design.  At each clock edge, advance to the
// nextstate (as determined by combinational logic)
always @(posedge clk) begin

	if(reset)
		state <= IDLE;
	else
		state <= nextstate;

end

endmodule


//=========================================================================
// RTL Model of GCD Unit Datpath
//-------------------------------------------------------------------------
//

module gcd_datapath #( parameter W = 16 )
( 

	//data inputs/outputs
	input [W-1:0] operands_bits_A,
	input [W-1:0] operands_bits_B,
	output [W-1:0] result_bits_data,

	//global inputs
	input clk, reset,

	//control signal inputs and outputs
	input B_mux_sel, A_en, B_en,
	input [1:0] A_mux_sel,
	output B_zero,
	output A_lt_B
);


reg [W-1:0] A_reg;
reg [W-1:0] B_reg;
wire [W-1:0] A_next;
wire [W-1:0] B_next;
wire [W-1:0] sub_out;

// Combinational
// ------------
assign A_next
	= A_mux_sel == 0 ? operands_bits_A
	: A_mux_sel == 1 ? B_reg
	: A_mux_sel == 2 ? sub_out
	: {W{1'bx}};

assign B_next
	= B_mux_sel == 0 ? operands_bits_B
	: B_mux_sel == 1 ? A_reg
	: {W{1'bx}};

// Subtract
assign sub_out = A_reg - B_reg;

// Zero?
assign B_zero = (B_reg == 0) ? 1'b1 : 1'b0;

// LT
assign A_lt_B = (A_reg < B_reg) ? 1'b1 : 1'b0;

// Assign output
assign result_bits_data = A_reg;



// Sequential
// ---------
always @ (posedge clk or posedge reset) begin

	if(reset) begin
		A_reg <= 0;
		B_reg <= 0;
	end else begin
		if (A_en) A_reg <= A_next;
		if (B_en) B_reg <= B_next;
	end

end


endmodule


//=========================================================================
// RTL Model of GCD Unit
//-------------------------------------------------------------------------
//

// W is a parameter specifying the bit width of the module
module gcd#( parameter W = 16 ) 
( 
  input          clk,
  input          reset,

  input  [W-1:0] operands_bits_A,
  input  [W-1:0] operands_bits_B,  
  input          operands_val,
  output         operands_rdy,

  output [W-1:0] result_bits_data,
  output         result_val,
  input          result_rdy
);

// At this top level, hook together the 
// datapath part and control part only

// In verilog, multi-bit wires will only be
// a single bit wide if they are not declared
wire A_en, B_en, B_zero, A_lt_B, B_mux_sel;
wire [1:0] A_mux_sel;

// Notice W parameter is sent to the datapath
// module as well
gcd_datapath#(W) GCDdpath0(

	// external
	.operands_bits_A(operands_bits_A),
	.operands_bits_B(operands_bits_B),
	.result_bits_data(result_bits_data),

	// system
	.clk(clk), 
	.reset(reset),

	// internal (between ctrl and dpath)
	.A_mux_sel(A_mux_sel[1:0]), 
	.A_en(A_en), 
	.B_en(B_en),
	.B_mux_sel(B_mux_sel),
	.B_zero(B_zero),
	.A_lt_B(A_lt_B)
);

gcd_control GCDctrl0(

	// external
	.operands_rdy(operands_rdy),
	.operands_val(operands_val), 
	.result_rdy(result_rdy),
	.result_val(result_val), 

	// system
	.clk(clk), 
	.reset(reset), 

	// internal (between ctrl and dpath)
	.B_zero(B_zero), 
	.A_lt_B(A_lt_B),
	.A_mux_sel(A_mux_sel[1:0]), 
	.A_en(A_en), 
	.B_en(B_en),
	.B_mux_sel(B_mux_sel)

);

endmodule
