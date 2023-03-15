`timescale 1ns/10ps

module pass_tb;

    reg clk = 0;
    always #(5) clk = ~clk;

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

        #1;

        in = 1;

        if (out == 1) begin
            $display("***Test Failed***");
        end

        @(posedge clk);
        #1;

        if (out == 0) begin
            $display("***Test Failed***");
        end

        #1;
        in = 0;

        @(posedge clk);
        #1;

        if (out == 1) begin
            $display("***Test Failed***");
        end

        $fsdbDumpoff;
        $finish;

    end

endmodule
