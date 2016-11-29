// This file contains behavioral Verilog that is used as the test harness for
// running simulations.

module CounterHarness;
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

  reg [4:0] goldCount;
  always @(posedge clock)
  begin
    if (reset)
      goldCount <= 0;
    else
      goldCount <= goldCount + 1;
  end

  reg [4:0] dutCount;
  Counter dut(
    .clock(clock),
    .reset(reset),
    .count(dutCount)
  );

  always @(posedge clock)
  begin
    $display("cycle=%d reset=%d goldCount=%d dutCount=%d", cycle, reset, goldCount, dutCount);
    if (!reset)
    begin
      casez (goldCount - dutCount)
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
