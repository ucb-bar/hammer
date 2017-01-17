// This file contains behavioral Verilog that is used as the test harness for
// running simulations.

module MultiplierHarness;
  // VPD dumping
  reg [1023:0] vcdplusfile = 0;
  initial
  begin
    if ($value$plusargs("vcdplusfile=%s", vcdplusfile))
    begin
`ifdef HAVE_SYNOPSYS_VCDPLUS
      $vcdplusfile(vcdplusfile);
      $vcdpluson(0);
      $vcdplusmemon(0);
`endif
    end
  end

  reg clock = 1'b0;
  always #(1) clock = ~clock;

  reg reset = 1'b1;
  initial #10 reset = 0;

  reg [7:0] cycle = 0;
  always @(posedge clock)
  begin
    cycle <= cycle + 1;
    if (cycle > 250)
    begin
`ifdef HAVE_SYNOPSYS_VCDPLUS
      $vcdplusclose;
      $dumpoff;
`endif
      $finish;
    end
  end

  reg [31:0] a;
  reg [31:0] b;
  always @(posedge clock)
  begin
    if (reset)
      begin
        a <= 0;
        b <= 256;
      end
    else
      begin
        a <= a + 1;
        b <= b + 1;
      end
  end

  reg [63:0] goldQ;
  assign goldQ = a * b;

  reg [63:0] dutQ;
  Multiplier dut(
    .clock(clock),
    .reset(reset),
    .io_a(a),
    .io_b(b),
    .io_q(dutQ)
  );

  always @(posedge clock)
  begin
    $display("cycle=%d reset=%d a=%d b=%d dutQ=%d goldQ=%d", cycle, reset, a, b, dutQ, goldQ);
    if (!reset)
    begin
      casez (goldQ - dutQ)
        0: ;
        default:
        begin
          $display("*** FAILED ***");
`ifdef HAVE_SYNOPSYS_VCDPLUS
          $vcdplusclose;
          $dumpoff;
          $fatal;
`endif
        end
      endcase
    end
  end

endmodule
