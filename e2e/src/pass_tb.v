`timescale 1ns/10ps

module pass_tb;

    reg clk = 0;
    always #(`CLOCK_PERIOD/2.0) clk = ~clk;

    reg in;
    wire out;

    pass pass_0 (
        .clock(clk),
        .in(in),
        .out(out)
    );

    initial begin
        $fsdbDumpfile("output.fsdb");
        $fsdbDumpvars("+all");
        $fsdbDumpon;

        in = 0;
        repeat(3) @(posedge clk);

        #(`CLOCK_PERIOD/4.0);

        in = 1;

        if (out == 1) begin
            $display("***Test Failed***");
        end

        @(posedge clk);
        #(`CLOCK_PERIOD/4.0);

        if (out == 0) begin
            $display("***Test Failed***");
        end

        #(`CLOCK_PERIOD/4.0);
        in = 0;

        @(posedge clk);
        #(`CLOCK_PERIOD/4.0);

        if (out == 1) begin
            $display("***Test Failed***");
        end

        $fsdbDumpoff;
        $finish;

    end

endmodule
