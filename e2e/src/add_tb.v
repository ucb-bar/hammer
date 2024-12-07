`timescale 1ns/10ps


module add_tb;

    reg clk = 0;
    always #(`CLOCK_PERIOD/2.0) clk = ~clk;

    reg [`WIDTH-1:0] in0, in1;
    wire [`WIDTH-1:0] out;

    integer file, status;

    add #(`WIDTH) add_dut (
        .clock(clk),
        .in0(in0), .in1(in1),
        .out(out)
    );

    initial begin
        // reset
        in0 = `WIDTH'b0; in1 = `WIDTH'b0;
        @(negedge clk);
        
        // open test file
        $fsdbDumpfile({`"`TESTROOT`", "/output.fsdb"});
        $fsdbDumpvars("+all");
        $fsdbDumpon;

        file = $fopen({`"`TESTROOT`", "/input.txt"}, "r");
        if (file) begin
            while (!$feof(file)) begin
                // load vals
                status = $fscanf(file, "%b %b", in0, in1);
                if (status == 2) begin
                end else if (status == -1) begin
                    $display("Finished reading file.");
                end else begin
                    $display("Error reading line.");
                end
                // perform operation
                @(posedge clk);
                @(negedge clk);
                $display(" %d + %d = %d",in0,in1,out);
            end
        end
        $fsdbDumpoff;
        $finish;

        // end        

    end

endmodule
