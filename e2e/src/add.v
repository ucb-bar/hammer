// W-bit Add Module


module add (
    input clock,
    input [`WIDTH-1:0] in0, in1,
    output [`WIDTH-1:0] out
);

reg [`WIDTH-1:0] in0_reg, in1_reg;
always@(posedge clock) begin
    in0_reg <= in0;
    in1_reg <= in1;
end

adder adder0 (.in0(in0_reg), .in1(in1_reg), .out(out));
endmodule




module adder (
    input [`WIDTH-1:0] in0, in1,
    output [`WIDTH-1:0] out
);
assign out = in0 + in1;
endmodule