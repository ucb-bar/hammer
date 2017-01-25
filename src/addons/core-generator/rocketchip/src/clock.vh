`define CLOCK_PERIOD 10.0
`ifdef VERILATOR
`define PRINTF_COND $c("done_reset")
`define STOP_COND $c("done_reset")
`else
`define PRINTF_COND !TestDriver.reset
`define STOP_COND !TestDriver.reset
`endif
`define RANDOMIZE_MEM_INIT
`define RANDOMIZE_REG_INIT
`define RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE_INVALID_ASSIGN
