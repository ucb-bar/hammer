module Counter(
  input wire clock,
  input wire reset,
  output wire [4:0] count
);
  reg [4:0] r;

  always @(posedge clock)
  begin
    if (reset)
      r <= 0;
    else
      r <= r + 1;
  end

  assign count = r;
endmodule
