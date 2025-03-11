# hammer-vlsi plugin for Questa

from hammer.vlsi import HammerSimTool, DummyHammerTool, HammerToolStep, deepdict
from hammer.config import HammerJSONEncoder

import hammer.tech as hammer_tech
from hammer.tech import HammerTechnologyUtils

from typing import Dict, List, Any, Optional
from decimal import Decimal

import os
import json

class Questa(HammerSimTool, DummyHammerTool):

    # Simulation steps
    @property
    def steps(self) -> List[HammerToolStep]:
        return self.make_steps_from_methods([
            self.qhsim
        ])

    # Main simulation method
    def qhsim(self) -> bool:
        # Get Hammer settings
        tb_name = self.get_setting("sim.inputs.tb_name")  # testbench main module
        tb_dut = self.get_setting("sim.inputs.tb_dut")  # DUT instance name in testbench
        defines = self.get_setting("sim.inputs.defines")  # macro definitions
        timescale = self.get_setting("sim.inputs.timescale")  # timescale setup
        input_files_list = self.get_setting("sim.inputs.input_files")  # input HDL files
        top_module = self.get_setting("sim.inputs.top_module")  # DUT module name
        timing_annotated = self.get_setting("sim.inputs.timing_annotated")  # using SDF
        wave_file = self.get_setting("sim.inputs.wave_file")  # waveform format setup file
        vlog_args = self.get_setting("sim.inputs.vlog_args")  # custom vlog arguments
        vopt_args = self.get_setting("sim.inputs.vopt_args")  # custom vopt arguments
        vsim_args = self.get_setting("sim.inputs.vsim_args")  # custom vsim arguments
        no_gui = self.get_setting("sim.inputs.no_gui")  # do not open GUI
        questa_bin = self.get_setting("sim.questa.questa_bin")  # Questa binary file
        # Create a Questa command file
        do_file = f"{self.run_dir}/{tb_name}.do"
        f = open(do_file, "w+")
        # Create the working library
        lib_name = f"work_{tb_name}"
        lib_dir = f"{self.run_dir}/{lib_name}"
        f.write("# Create the working library\n")
        f.write(f"rm -rf {lib_dir}\n")
        f.write(f"vlib {lib_dir}\n")
        f.write(f"vmap {lib_name} {lib_dir}\n")  # potentially redundant
        # Compile the design units
        defines_list = [f"+define+{x}" for x in defines]
        defines_string = " ".join(defines_list)
        for i in range(len(input_files_list)):  # converting relative paths to absolute
            if (input_files_list[i][0] != '/'):
                input_files_list[i] = os.getcwd() + '/' + input_files_list[i]
        input_files_string = " ".join(input_files_list)
        if self.level.is_gatelevel():  # add Verilog models of standard cells
            verilog_models_list = self.get_verilog_models()
            verilog_models_string = " ".join(verilog_models_list)
            input_files_string += ' ' + verilog_models_string
        f.write("# Compile the design units\n")
        f.write(f"vlog -work {lib_name} {defines_string} -timescale {timescale} \
                {input_files_string} {vlog_args}\n")
        # Optimize the design
        sdf_args = "-nosdf +notimingchecks"
        if timing_annotated:
            sdf_corner = self.get_setting("sim.inputs.sdf_corner")
            # Convert relative paths to absolute (if needed)
            if self.sdf_file:  # if SDF file is specified in input .yml
                self.sdf_file = self.sdf_file if self.sdf_file[0] == '/' else os.getcwd() + '/' + self.sdf_file
            # Generate SDF-related arguments
            sdf_args = f" +sdf_verbose -sdf{sdf_corner} /{tb_name}/{tb_dut}={self.sdf_file}"
        f.write("# Optimize the design\n")
        f.write(f"vopt -debugdb -work {lib_name} -timescale {timescale} \
                {sdf_args} +acc {tb_name} -o opt_{tb_name} {vopt_args}\n")
        # Load the design
        f.write("# Load the design\n")
        f.write(f"vsim -debugDB -work {lib_name} opt_{tb_name} {vsim_args}\n")
        # Add waves
        f.write("# Add waves\n")
        if wave_file:  # if waveform setup file is specified in input .yml
            wave_file = wave_file if wave_file[0] == '/' else "../../" + wave_file
            f.write(f"do {wave_file}\n")
        else:
            f.write(f"add wave -group TB -internal {tb_name}/*\n")  # a group of all TB signals
            f.write(f"add wave -ports {tb_dut}/*\n")  # DUT ports displayed individually
            f.write(f"add wave -group INT -r -internal {tb_dut}/*\n")  # a group of internal DUT signal
            # Log simulation data
        f.write("# Log simulation data\n")
        f.write("log -r *\n")  # potentially redundant
        # Run simulation (if enabled)
        if self.get_setting("sim.inputs.execute_sim"):
            f.write("# Run simulation\n")
            f.write("run -all\n")
        else:
            self.logger.warning("Not running any simulations because sim.inputs.execute_sim is unset.")
        # Close the Questa command file
        f.close()
        # Run Questa simulation
        args = [questa_bin]
        if no_gui:
            args.append("-c")  # do not open GUI
        args.append("-do")
        args.append(f"{do_file}")
        self.run_executable(args, cwd=self.run_dir)
        return True

    # Fill output json file
    def fill_outputs(self) -> bool:
        self.output_waveforms = []
        self.output_saifs = []
        self.output_top_module = self.top_module
        self.output_tb_name = self.get_setting("sim.inputs.tb_name")
        self.output_tb_dut = self.get_setting("sim.inputs.tb_dut")
        self.output_level = self.get_setting("sim.inputs.level")
        return True

    # Get verilog models of standard cells
    def get_verilog_models(self) -> List[str]:
        verilog_sim_files = self.technology.read_libs([hammer_tech.filters.verilog_sim_filter],
                                                      hammer_tech.HammerTechnologyUtils.to_plain_item)
        return verilog_sim_files

    def tool_config_prefix(self) -> str:
        return "sim.questa"

tool = Questa
