// W-bit Add Module


module add #( parameter W = 8 ) (
    input clock,
    input [W-1:0] in0, in1,
    output [W-1:0] out
);

reg [W-1:0] in0_reg, in1_reg;
always@(posedge clock) begin
    in0_reg <= in0;
    in1_reg <= in1;
end

adder #(W) adder0 (.in0(in0_reg), .in1(in1_reg), .out(out));
endmodule




module adder #( parameter W = 8 ) (
    input [W-1:0] in0, in1,
    output [W-1:0] out
);
assign out = in0 + in1;
endmodule