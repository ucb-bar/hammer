`timescale 1 ns /  100 ps

module gcd_tb;

  //--------------------------------------------------------------------
  // Define test vectors
  //--------------------------------------------------------------------
  wire [31:0] src_bits [7:0];
  wire [15:0] sink_bits [7:0];
  assign src_bits[0] = { 16'd27,  16'd15  }; assign sink_bits[0] = { 16'd3  };
  assign src_bits[1] = { 16'd21,  16'd49  }; assign sink_bits[1] = { 16'd7  };
  assign src_bits[2] = { 16'd25,  16'd30  }; assign sink_bits[2] = { 16'd5  };
  assign src_bits[3] = { 16'd19,  16'd27  }; assign sink_bits[3] = { 16'd1  };
  assign src_bits[4] = { 16'd40,  16'd40  }; assign sink_bits[4] = { 16'd40 };
  assign src_bits[5] = { 16'd250, 16'd190 }; assign sink_bits[5] = { 16'd10 };
  assign src_bits[6] = { 16'd5,   16'd250 }; assign sink_bits[6] = { 16'd5  };
  assign src_bits[7] = { 16'd0,   16'd0   }; assign sink_bits[7] = { 16'd0  };


  //--------------------------------------------------------------------
  // Setup a clock
  //--------------------------------------------------------------------
  reg clk = 0;
  always #(`CLOCK_PERIOD/2) clk = ~clk;

  //--------------------------------------------------------------------
  // Instantiate DUT and wire/reg the inputs and outputs
  //--------------------------------------------------------------------
  reg [7:0] test_index;
  wire [15:0] src_bits_A;
  wire [15:0] src_bits_B;
  wire [15:0] compare_bits;

  assign src_bits_A = src_bits[test_index][31:16];
  assign src_bits_B = src_bits[test_index][15:0];
  assign compare_bits = sink_bits[test_index];

  reg reset;
  reg        src_val;
  wire        src_rdy;
  wire [15:0] result_bits_data;
  wire        result_val;
  reg        result_rdy;
  
  gcd #(16) gcd_dut
  ( 
    .clk              (clk),
    .reset            (reset),

    .operands_bits_A  (src_bits_A),
    .operands_bits_B  (src_bits_B),  
    .operands_val     (src_val),
    .operands_rdy     (src_rdy),

    .result_bits_data (result_bits_data), 
    .result_val       (result_val),
    .result_rdy       (result_rdy)

  );

  //--------------------------------------------------------------------
  // Define a sequential interface that steps through each test in
  // the src/sink array every time a valid ready/val handshake occurs
  //--------------------------------------------------------------------

  initial begin

`ifdef USE_VPD
    $vcdpluson;
`else // FSDB
    $fsdbDumpfile("output.fsdb");
    $fsdbDumpvars("+all");
    $fsdbDumpon;
`endif
    // Initial values
    src_val = 0;
    result_rdy = 1;
    reset = 1;

    // Strobe reset
    repeat (5) @(negedge clk) reset = 1;
    @(negedge clk) reset = 0;

    // Loop through test vectors..
    for (test_index = 0; test_index < 7; test_index = test_index + 1) begin
      // Start when DUT is ready
      @(negedge clk & src_rdy);
      src_val = 1; 
      @(negedge clk);
      src_val = 0; 
      // Wait until result is made valid
      @(posedge result_val);
      // Don't check right away (not sure when this signal will go high),
      // but check at the next positive edge
      @(posedge clk);
      if (compare_bits == result_bits_data) begin
        $display(" [ passed ] Test ( %d ), [ %d == %d ] (decimal)",test_index,compare_bits,result_bits_data);
      end else begin
        $display(" [ failed ] Test ( %d ), [ %d == %d ] (decimal)",test_index,compare_bits,result_bits_data);
      end
    end

`ifdef USE_VPD
    $vcdplusoff;
`else // FSDB
    $fsdbDumpoff;
`endif
    $finish;

  end


  //--------------------------------------------------------------------
  // Timeout
  //--------------------------------------------------------------------
  // If something goes wrong, kill the simulation...
  reg [  63:0] cycle_count = 0;
  always @(posedge clk) begin
    cycle_count = cycle_count + 1;
    if (cycle_count >= 1000) begin
      $display("TIMEOUT");
`ifdef USE_VPD
      $vcdplusoff;
`else // FSDB
      $fsdbDumpoff;
`endif
      $finish;
    end
  end


endmodule
