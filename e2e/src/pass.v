// Passthrough Module

module pass (
    input clock,
    input in,
    output reg out
);

always@(posedge clock) begin
    out <= in;
end

endmodule
