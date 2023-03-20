#!/usr/bin/env python3
#  generate_properties.py
#
#  Helper script to generate properties for hammer-vlsi tool classes.
#
#  See LICENSE for licence details.

import argparse
import os
import re
import sys
from collections import namedtuple
from typing import Dict

InterfaceVar = namedtuple("InterfaceVar", 'name type desc')

Interface = namedtuple("Interface", 'module filename inputs outputs')


def isinstance_check(t: str) -> str:
    return "isinstance(value, {t})".format(t=t)


def generate_from_list(template: str, lst) -> list:
    def format_var(var):
        attr_error_logic = """raise ValueError("Nothing set for the {var_desc} yet")"""

        if var.type.startswith("Iterable"):
            var_type_instance_check = isinstance_check("Iterable")
        elif var.type.startswith("List"):
            var_type_instance_check = isinstance_check("List")
        elif var.type.startswith("Optional"):
            m = re.search(r"Optional\[(\S+)\]", var.type)
            subtype = str(m.group(1))
            var_type_instance_check = isinstance_check(subtype) + " or (value is None)"
            attr_error_logic = "return None"
        else:
            var_type_instance_check = isinstance_check(var.type)

        t = template.replace("[[attr_error_logic]]", attr_error_logic)

        return t.format(var_name=var.name, var_type=var.type, var_desc=var.desc,
                        var_type_instance_check=var_type_instance_check)

    return list(map(format_var, lst))


# Cache of files being modified.
file_cache = {}  # type: Dict[str, str]


def get_full_filename(filename: str) -> str:
    return os.path.join(os.path.dirname(__file__), filename)


def generate_interface(interface: Interface) -> None:
    template = """
    @property
    def {var_name}(self) -> {var_type}:
        \"""
        Get the {var_desc}.

        :return: The {var_desc}.
        \"""
        try:
            return self.attr_getter("_{var_name}", None)
        except AttributeError:
            [[attr_error_logic]]

    @{var_name}.setter
    def {var_name}(self, value: {var_type}) -> None:
        \"""Set the {var_desc}.\"""
        if not ({var_type_instance_check}):
            raise TypeError("{var_name} must be a {var_type}")
        self.attr_setter("_{var_name}", value)
"""
    start_key = "    ### Generated interface %s ###" % (interface.module)
    end_key = "    ### END Generated interface %s ###" % (interface.module)

    output = []
    output.append(start_key)
    output.append("    ### DO NOT MODIFY THIS CODE, EDIT %s INSTEAD ###" % (os.path.basename(__file__)))
    output.append("    ### Inputs ###")
    output.extend(generate_from_list(template, interface.inputs))
    output.append("")
    output.append("    ### Outputs ###")
    output.extend(generate_from_list(template, interface.outputs))
    output.append(end_key)

    filename = get_full_filename(interface.filename)

    if filename not in file_cache:
        with open(filename, "r") as f:
            file_cache[filename] = str(f.read())
    contents = file_cache[filename]

    new_contents = re.sub(re.escape(start_key) + ".*" + re.escape(end_key), "\n".join(output), contents,
                          flags=re.MULTILINE | re.DOTALL)

    file_cache[filename] = new_contents


def main(args) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', "--dry_run", action="store_true", required=False)
    parser.add_argument("-f", "--file", required=False, default="",
                        help='File to write/print. If unset, will write/print all files.')
    parsed_args = parser.parse_args(args[1:])

    HammerSynthesisTool = Interface(module="HammerSynthesisTool",
                                    filename="vlsi/hammer_vlsi_impl.py",
                                    inputs=[
                                        InterfaceVar("input_files", "List[str]",
                                                     "input collection of source RTL files (e.g. *.v)")
                                    ],
                                    outputs=[
                                        InterfaceVar("output_files", "List[str]",
                                                     "output collection of mapped (post-synthesis) RTL files"),
                                        InterfaceVar("output_sdc", "str",
                                                     "(optional) output post-synthesis SDC constraints file"),
                                        InterfaceVar("output_all_regs", "str",
                                                     "path to output list of all registers in the design with output pin for gate level simulation"),
                                        InterfaceVar("output_seq_cells", "str",
                                                     "path to output collection of all sequential standard cells in design"),
                                        InterfaceVar("sdf_file", "str",
                                                     "output SDF file to be read for timing annotated gate level sims")
                                        # TODO: model CAD junk
                                    ]
                                    )

    HammerPlaceAndRouteTool = Interface(module="HammerPlaceAndRouteTool",
                                        filename="vlsi/hammer_vlsi_impl.py",
                                        inputs=[
                                            InterfaceVar("input_files", "List[str]",
                                                         "input post-synthesis netlist files"),
                                            InterfaceVar("post_synth_sdc", "Optional[str]",
                                                         "(optional) input post-synthesis SDC constraint file"),
                                        ],
                                        outputs=[
                                            # TODO: model more CAD junk

                                            # e.g. par-rundir/TopModuleILMDir/mmmc/ilm_data/TopModule. Has a bunch of files TopModule_postRoute*
                                            InterfaceVar("output_ilms", "List[ILMStruct]",
                                                         "(optional) output ILM information for hierarchical mode"),
                                            InterfaceVar("output_gds", "str", "path to the output GDS file"),
                                            InterfaceVar("output_netlist", "str", "path to the output netlist file"),
                                            InterfaceVar("output_sim_netlist", "str", "path to the output simulation netlist file"),
                                            InterfaceVar("hcells_list", "List[str]",
                                                         "list of cells to explicitly map hierarchically in LVS"),
                                            InterfaceVar("output_all_regs", "str",
                                                         "path to output list of all registers in the design with output pin for gate level simulation"),
                                            InterfaceVar("output_seq_cells", "str",
                                                         "path to output collection of all sequential standard cells in design"),
                                            InterfaceVar("sdf_file", "str",
                                                     "output SDF file to be read for timing annotated gate level sims")
                                            # TODO: add individual parts of the ILM (e.g. verilog, sdc, spef, etc) for cross-tool compatibility?
                                        ]
                                        )

    HammerSRAMGeneratorTool = Interface(module="HammerSRAMGeneratorTool",
                                       filename="vlsi/hammer_vlsi_impl.py",
                                       inputs=[
                                           InterfaceVar("input_parameters", "List[SRAMParameters]",
                                                        "input sram parameters to be generated")
                                           ],
                                       outputs=[
                                           InterfaceVar("output_libraries", "List[ExtraLibrary]",
                                                        "list of the hammer tech libraries corresponding to generated srams")
                                           ]
                                       )

    HammerDRCTool = Interface(module="HammerDRCTool",
                              filename="vlsi/hammer_vlsi_impl.py",
                              inputs=[
                                  InterfaceVar("layout_file", "str", "path to the input layout file (e.g. a *.gds)")
                              ],
                              outputs=[]
                              )

    HammerLVSTool = Interface(module="HammerLVSTool",
                              filename="vlsi/hammer_vlsi_impl.py",
                              inputs=[
                                  InterfaceVar("layout_file", "str", "path to the input layout file (e.g. a *.gds)"),
                                  InterfaceVar("schematic_files", "List[str]",
                                               "path to the input SPICE or Verilog schematic files (e.g. *.v or *.spi)"),
                                  InterfaceVar("hcells_list", "List[str]",
                                               "list of cells to explicitly map hierarchically in LVS"),
                                  InterfaceVar("ilms", "List[ILMStruct]",
                                               "list of (optional) input ILM information for hierarchical mode")
                              ],
                              outputs=[]
                              )

    HammerSimTool = Interface(module="HammerSimTool",
                              filename="vlsi/hammer_vlsi_impl.py",
                              inputs=[
                                  InterfaceVar("top_module", "str", "top RTL module"),
                                  InterfaceVar("input_files", "List[str]", "paths to input verilog files"),
                                  InterfaceVar("all_regs", "str", "path to list of all registers in the design with output pin"),
                                  InterfaceVar("seq_cells", "str", "path to collection of all sequential standard cells in design"),
                                  InterfaceVar("sdf_file", "Optional[str]", "optional SDF file needed for timing annotated gate level sims")
                              ],
                              outputs=[
                                  InterfaceVar("output_waveforms", "List[str]", "paths to output waveforms"),
                                  InterfaceVar("output_saifs", "List[str]", "paths to output activity files"),
                                  InterfaceVar("output_top_module", "str", "top RTL module"),
                                  InterfaceVar("output_tb_name", "str", "sim testbench name"),
                                  InterfaceVar("output_tb_dut", "str", "sim DUT instance name"),
                                  InterfaceVar("output_level", "str", "simulation flow level")
                              ]
                              )
    HammerPowerTool = Interface(module="HammerPowerTool",
                                filename="vlsi/hammer_vlsi_impl.py",
                                inputs=[
                                  InterfaceVar("flow_database", "str", "path to syn or par database for power analysis"),
                                  InterfaceVar("input_files", "List[str]", "paths to RTL input files or design netlist"),
                                  InterfaceVar("spefs", "List[str]", "list of spef files for power anlaysis"),
                                  InterfaceVar("sdc", "Optional[str]","(optional) input SDC constraint file"),
                                  InterfaceVar("waveforms", "List[str]", "list of waveform dump files for dynamic power analysis"),
                                  InterfaceVar("saifs", "List[str]", "list of activity files for dynamic power analysis"),
                                  InterfaceVar("top_module", "str", "top RTL module"),
                                  InterfaceVar("tb_name", "str", "testbench name"),
                                  InterfaceVar("tb_dut", "str", "DUT instance name")
                                ],
                                outputs=[]
                                )
    HammerFormalTool = Interface(module="HammerFormalTool",
                            filename="vlsi/hammer_vlsi_impl.py",
                            inputs=[
                                InterfaceVar("check", "str",
                                    "formal verification check type to run"),
                                InterfaceVar("input_files", "List[str]",
                                    "input collection of implementation design files"),
                                InterfaceVar("reference_files", "List[str]",
                                    "input collection of reference design files"),
                                InterfaceVar("top_module", "str", "top RTL module"),
                                InterfaceVar("post_synth_sdc", "Optional[str]",
                                    "(optional) input post-synthesis SDC constraint file")
                            ],
                            outputs=[]
                            )
    HammerTimingTool = Interface(module="HammerTimingTool",
                            filename="vlsi/hammer_vlsi_impl.py",
                            inputs=[
                                InterfaceVar("input_files", "List[str]",
                                    "input collection of design files"),
                                InterfaceVar("top_module", "str", "top RTL module"),
                                InterfaceVar("post_synth_sdc", "Optional[str]",
                                    "(optional) input post-synthesis SDC constraint file"),
                                InterfaceVar("spefs", "Optional[List]",
                                    "(optional) list of SPEF files"),
                                InterfaceVar("sdf_file", "Optional[str]",
                                    "(optional) input SDF file")
                            ],
                            outputs=[]
                            )
    HammerPCBDeliverableTool = Interface(module="HammerPCBDeliverableTool",
                                       filename="vlsi/hammer_vlsi_impl.py",
                                       inputs=[],
                                       outputs=[
                                           InterfaceVar("output_footprints", "List[str]",
                                                        "list of the PCB footprint files for the project"),
                                           InterfaceVar("output_schematic_symbols", "List[str]",
                                                        "list of the PCB schematic symbol files for the project"),
                                           ]
                                       )

    dry_run = parsed_args.dry_run
    selected_file = str(parsed_args.file)

    generate_interface(HammerSynthesisTool)
    generate_interface(HammerPlaceAndRouteTool)
    generate_interface(HammerDRCTool)
    generate_interface(HammerLVSTool)
    generate_interface(HammerSRAMGeneratorTool)
    generate_interface(HammerSimTool)
    generate_interface(HammerPowerTool)
    generate_interface(HammerFormalTool)
    generate_interface(HammerTimingTool)
    generate_interface(HammerPCBDeliverableTool)

    if selected_file == "":
        # Export all files
        # print without extra newline
        for filename, contents in file_cache.items():
            if dry_run:
                print(contents, end='')
            else:
                with open(filename, "w") as f:
                    f.write(contents)
    else:
        # Export selected file
        contents = file_cache[get_full_filename(selected_file)]
        if dry_run:
            print(contents, end='')
        else:
            with open(filename, "w") as f:
                f.write(contents)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
