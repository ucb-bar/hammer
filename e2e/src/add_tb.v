`timescale 1ns/10ps

// `define WIDTH 8
// `define CLOCK_PERIOD 1

module add_tb;

    reg clk = 0;
    always #(`CLOCK_PERIOD/2.0) clk = ~clk;

    reg [`WIDTH-1:0] in0, in1;
    wire [`WIDTH-1:0] out;

    add #(`WIDTH) add_dut (
        .clock(clk),
        .in0(in0), .in1(in1),
        .out(out)
    );

    initial begin
        // reset
        in0 = `WIDTH'b0; in1 = `WIDTH'b0;
        
        // load vals
        @(negedge clk);

        $fsdbDumpfile("output.fsdb");
        $fsdbDumpvars("+all");
        $fsdbDumpon;

        in0 = `WIDTH'b110; in1 = `WIDTH'b001;

        // perform add
        @(posedge clk);
        

        // check results
        @(negedge clk);
        $display(" %d + %d = %d",in0,in1,out);

        $fsdbDumpoff;
        $finish;

        // end
        @(posedge clk);
        

    end

endmodule
