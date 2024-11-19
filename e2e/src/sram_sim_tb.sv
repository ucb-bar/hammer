`timescale 1ns/10ps

module sram_sim_tb;

parameter DATA_WIDTH = 4;
parameter ADDR_WIDTH = 6;
parameter WMASK_WIDTH = 2;
parameter RAM_DEPTH = 1 << ADDR_WIDTH;

reg clk = 0;
always #(`CLOCK_PERIOD/2.0) clk = ~clk;

reg we;
reg [WMASK_WIDTH-1:0] wmask;
reg [ADDR_WIDTH-1:0]  addr;
reg [DATA_WIDTH-1:0]  din;
wire [DATA_WIDTH-1:0] dout;

sram_sim sram_sim_dut (
    .clock(clk),
    .we(we),
    .wmask(wmask),
    .addr(addr),
    .din(din),
    .dout(dout)
);

integer file, status;
integer operation, address, data_in;

task automatic read_input (input string file_path);

    $display("Attempting to open file: %s", file_path);
    file = $fopen(file_path, "r");

    if (file) begin

        while (!$feof(file)) begin
            status = $fscanf(file, "%d %d %d", operation, address, data_in);

            if (status == 3) begin

                addr = address;

                if (operation == 1'b1) begin

                    din = data_in;

                    // write
                    we = 1'b1;
                    @(posedge clk); // we --> we_reg in sram_wrapper
                    @(posedge clk); // perform SRAM write
                    $display("Wrote %d to address %d\n", din, addr);

                end else if (operation == 1'b0) begin
                    
                    // read
                    we = 1'b0;
                    @(posedge clk); // we --> we_reg in sram_wrapper
                    @(posedge clk); // perform SRAM read
                    @(negedge clk); // stabilize output
                    $display("Read %d from address %d\n", dout, addr);
                    
                end

            end else if (status == -1) begin
                
                $display("Finished reading file.");

            end else begin

                $display("Error reading line.");
                break;

            end
        end

        $fclose(file);

    end else begin

        $display("File not found.");

    end
endtask

initial begin

    @(negedge clk);

    // reset SRAM signals
    din = {DATA_WIDTH{'d13}};
    wmask = {DATA_WIDTH{1'b1}}; 
    addr = {DATA_WIDTH{'b0}};
    we = 0'b0;
    
    read_input({"/tools/scratch/henrycen/main/hammer/test_data/", `"`TESTNAME`", "/reset.txt"});

    $fsdbDumpfile("output.fsdb");
    $fsdbDumpvars("+all");
    $fsdbDumpon;

    read_input({"/tools/scratch/henrycen/main/hammer/test_data/", `"`TESTNAME`", "/input.txt"});

    $fsdbDumpoff;

    $finish;
    
end

endmodule