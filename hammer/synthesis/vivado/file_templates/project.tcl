# TCL fragment to create a Vivado project.

create_project -part {part_fpga} -in_memory
set_property -dict [list \
                        BOARD_PART {part_board} \
                        TARGET_LANGUAGE {{Verilog}} \
                        SIMULATOR_LANGUAGE {{Mixed}} \
                        TARGET_SIMULATOR {{XSim}} \
                        DEFAULT_LIB {{xil_defaultlib}} \
                       ] [current_project]
