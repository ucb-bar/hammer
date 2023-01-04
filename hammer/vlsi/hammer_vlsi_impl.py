#  hammer_vlsi_impl.py
#  hammer-vlsi implementation file. Users should import hammer_vlsi instead.
#
#  See LICENSE for licence details.

from abc import abstractmethod
import importlib
import importlib.resources as resources
import os
import sys
import json
from typing import Iterable
import inspect
import datetime

import hammer.config as hammer_config
from hammer.utils import deepdict, coerce_to_grid
from hammer.tech import ExtraLibrary

from .constraints import *
from .units import VoltageValue, TimeValue

class HierarchicalMode(Enum):
    Flat = 1
    Leaf = 2
    Hierarchical = 3
    Top = 4

    @classmethod
    def __mapping(cls) -> Dict[str, "HierarchicalMode"]:
        return {
            "flat": HierarchicalMode.Flat,
            "leaf": HierarchicalMode.Leaf,
            "hierarchical": HierarchicalMode.Hierarchical,
            "top": HierarchicalMode.Top
        }

    @staticmethod
    def from_str(x: str) -> "HierarchicalMode":
        try:
            return HierarchicalMode.__mapping()[x]
        except KeyError:
            raise ValueError("Invalid string for HierarchicalMode: " + str(x))

    def __str__(self) -> str:
        return reverse_dict(HierarchicalMode.__mapping())[self]

    def is_nonleaf_hierarchical(self) -> bool:
        """
        Helper function that returns True if this mode is a non-leaf hierarchical mode (i.e. any block with
        hierarchical sub-blocks).
        """
        return self == HierarchicalMode.Hierarchical or self == HierarchicalMode.Top

class FlowLevel(Enum):
    RTL = 1
    SYN = 2
    PAR = 3

    @classmethod
    def __mapping(cls) -> Dict[str, "FlowLevel"]:
        return {
            "rtl": FlowLevel.RTL,
            "syn": FlowLevel.SYN,
            "par": FlowLevel.PAR
        }

    @staticmethod
    def from_str(x: str) -> "FlowLevel":
        try:
            return FlowLevel.__mapping()[x]
        except KeyError:
            raise ValueError("Invalid string for FlowLevel: " + str(x))

    def __str__(self) -> str:
        return reverse_dict(FlowLevel.__mapping())[self]

    def is_gatelevel(self) -> bool:
        return self == FlowLevel.SYN or self == FlowLevel.PAR


PowerReport = NamedTuple('PowerReport', [
    ('waveform_path', str),
    ('module', Optional[str]),
    ('levels', Optional[int]),
    ('start_time', Optional[TimeValue]),
    ('end_time', Optional[TimeValue]),
    ('toggle_signal', Optional[str]),
    ('num_toggles', Optional[int]),
    ('frame_count', Optional[int]),
    ('report_name', Optional[str])
])


import hammer.tech as hammer_tech


class HammerVLSISettings:
    """
    Static class which holds global hammer-vlsi settings.
    """

    @staticmethod
    def get_config() -> dict:
        """Export settings as a config dictionary."""
        return {}

    @classmethod
    def load_builtins_and_core(cls, database: hammer_config.HammerDatabase) -> None:
        """
        Helper function that loads builtins and core into a HammerDatabase.
        """

        # Load in builtins.
        builtins_yml = resources.files("hammer.config") / "builtins.yml"
        database.update_builtins([
            hammer_config.load_config_from_string(builtins_yml.read_text(), True),
            HammerVLSISettings.get_config()
        ])

        # Read in core defaults.
        database.update_core(*hammer_config.load_config_from_defaults("hammer.config", types=True))

        # Read in vendor-common defaults.
        # TODO: move these defaults into respective vendor plugin packages
        for pkg in ["hammer.common.cadence", "hammer.common.synopsys", "hammer.common.mentor", "hammer.common.openroad"]:
            config, types = hammer_config.load_config_from_defaults(pkg, types=True)
            database.update_defaults(config)
            database.update_types(types, check_type=False)

from .hammer_tool import HammerTool, HammerToolStep

class DummyHammerTool(HammerTool):
    """
    This is a dummy implementation of HammerTool that does nothing.
    It has no config, and no particular sense of versioning.
    It is present for nop tools and as a testing aid.
    """

    def tool_config_prefix(self) -> str:
        return ""

    def version_number(self, version: str) -> int:
        return 1

    @property
    def steps(self) -> List[HammerToolStep]:
        return []

class HammerSRAMGeneratorTool(HammerTool):
    ### Generated interface HammerSRAMGeneratorTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def input_parameters(self) -> List[SRAMParameters]:
        """
        Get the input sram parameters to be generated.

        :return: The input sram parameters to be generated.
        """
        try:
            return self.attr_getter("_input_parameters", None)
        except AttributeError:
            raise ValueError("Nothing set for the input sram parameters to be generated yet")

    @input_parameters.setter
    def input_parameters(self, value: List[SRAMParameters]) -> None:
        """Set the input sram parameters to be generated."""
        if not (isinstance(value, List)):
            raise TypeError("input_parameters must be a List[SRAMParameters]")
        self.attr_setter("_input_parameters", value)


    ### Outputs ###

    @property
    def output_libraries(self) -> List[ExtraLibrary]:
        """
        Get the list of the hammer tech libraries corresponding to generated srams.

        :return: The list of the hammer tech libraries corresponding to generated srams.
        """
        try:
            return self.attr_getter("_output_libraries", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of the hammer tech libraries corresponding to generated srams yet")

    @output_libraries.setter
    def output_libraries(self, value: List[ExtraLibrary]) -> None:
        """Set the list of the hammer tech libraries corresponding to generated srams."""
        if not (isinstance(value, List)):
            raise TypeError("output_libraries must be a List[ExtraLibrary]")
        self.attr_setter("_output_libraries", value)

    ### END Generated interface HammerSRAMGeneratorTool ###

    @property
    def steps(self) -> List[HammerToolStep]:
        steps = [
            self.generate_all_srams_and_corners
            ]
        return self.make_steps_from_methods(steps)

    def fill_outputs(self) -> bool:
        return True #we fill in output_libraries in generate_all_srams_and_corners

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = deepdict(super().export_config_outputs())
        simple_ex = []
        for ex in self.output_libraries: # type: ExtraLibrary
            simple_lib = json.loads(ex.library.json())
            if(ex.prefix == None):
                new_ex = {"library": simple_lib}
            else:
                new_ex = {"prefix": ex.prefix, "library": simple_lib}
            simple_ex.append(new_ex)
        outputs["vlsi.technology.extra_libraries"] = simple_ex
        outputs["vlsi.technology.extra_libraries_meta"] = "append"
        return outputs

    #TODO: Is this the right way for these two generate_all methods to work
    # in techX16 you can generate only ever generate a single SRAM per run but can
    # generate multiple corners at once
    def generate_all_srams_and_corners(self) -> bool:
        srams_corners = list(map(lambda c: self.generate_all_srams(c), self.get_mmmc_corners())) # type: List[List[ExtraLibrary]]
        if len(srams_corners):
            self.output_libraries = reduce(list.__add__, srams_corners)
        else:
            self.output_libraries = []
        return True

    def generate_all_srams(self, corner: MMMCCorner) -> List[ExtraLibrary]:
        srams = list(map(lambda p: self.generate_sram(p, corner), self.input_parameters)) # type: List[ExtraLibrary]
        return srams

    # Run compiler for a single sram and corner
    @abstractmethod
    def generate_sram(self, params: SRAMParameters, corner: MMMCCorner) -> ExtraLibrary:
        pass

class HammerSynthesisTool(HammerTool):
    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = deepdict(super().export_config_outputs())
        outputs["synthesis.outputs.output_files"] = self.output_files
        outputs["synthesis.inputs.input_files"] = self.input_files
        outputs["synthesis.inputs.top_module"] = self.top_module
        return outputs

    ### Generated interface HammerSynthesisTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def input_files(self) -> List[str]:
        """
        Get the input collection of source RTL files (e.g. *.v).

        :return: The input collection of source RTL files (e.g. *.v).
        """
        try:
            return self.attr_getter("_input_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the input collection of source RTL files (e.g. *.v) yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """Set the input collection of source RTL files (e.g. *.v)."""
        if not (isinstance(value, List)):
            raise TypeError("input_files must be a List[str]")
        self.attr_setter("_input_files", value)


    ### Outputs ###

    @property
    def output_files(self) -> List[str]:
        """
        Get the output collection of mapped (post-synthesis) RTL files.

        :return: The output collection of mapped (post-synthesis) RTL files.
        """
        try:
            return self.attr_getter("_output_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the output collection of mapped (post-synthesis) RTL files yet")

    @output_files.setter
    def output_files(self, value: List[str]) -> None:
        """Set the output collection of mapped (post-synthesis) RTL files."""
        if not (isinstance(value, List)):
            raise TypeError("output_files must be a List[str]")
        self.attr_setter("_output_files", value)


    @property
    def output_sdc(self) -> str:
        """
        Get the (optional) output post-synthesis SDC constraints file.

        :return: The (optional) output post-synthesis SDC constraints file.
        """
        try:
            return self.attr_getter("_output_sdc", None)
        except AttributeError:
            raise ValueError("Nothing set for the (optional) output post-synthesis SDC constraints file yet")

    @output_sdc.setter
    def output_sdc(self, value: str) -> None:
        """Set the (optional) output post-synthesis SDC constraints file."""
        if not (isinstance(value, str)):
            raise TypeError("output_sdc must be a str")
        self.attr_setter("_output_sdc", value)


    @property
    def output_all_regs(self) -> str:
        """
        Get the path to output list of all registers in the design with output pin for gate level simulation.

        :return: The path to output list of all registers in the design with output pin for gate level simulation.
        """
        try:
            return self.attr_getter("_output_all_regs", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to output list of all registers in the design with output pin for gate level simulation yet")

    @output_all_regs.setter
    def output_all_regs(self, value: str) -> None:
        """Set the path to output list of all registers in the design with output pin for gate level simulation."""
        if not (isinstance(value, str)):
            raise TypeError("output_all_regs must be a str")
        self.attr_setter("_output_all_regs", value)


    @property
    def output_seq_cells(self) -> str:
        """
        Get the path to output collection of all sequential standard cells in design.

        :return: The path to output collection of all sequential standard cells in design.
        """
        try:
            return self.attr_getter("_output_seq_cells", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to output collection of all sequential standard cells in design yet")

    @output_seq_cells.setter
    def output_seq_cells(self, value: str) -> None:
        """Set the path to output collection of all sequential standard cells in design."""
        if not (isinstance(value, str)):
            raise TypeError("output_seq_cells must be a str")
        self.attr_setter("_output_seq_cells", value)


    @property
    def sdf_file(self) -> str:
        """
        Get the output SDF file to be read for timing annotated gate level sims.

        :return: The output SDF file to be read for timing annotated gate level sims.
        """
        try:
            return self.attr_getter("_sdf_file", None)
        except AttributeError:
            raise ValueError("Nothing set for the output SDF file to be read for timing annotated gate level sims yet")

    @sdf_file.setter
    def sdf_file(self, value: str) -> None:
        """Set the output SDF file to be read for timing annotated gate level sims."""
        if not (isinstance(value, str)):
            raise TypeError("sdf_file must be a str")
        self.attr_setter("_sdf_file", value)

    ### END Generated interface HammerSynthesisTool ###


class HammerPlaceAndRouteTool(HammerTool):
    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = deepdict(super().export_config_outputs())
        outputs["par.outputs.output_ilms"] = list(map(lambda s: s.to_setting(), self.output_ilms))
        outputs["par.outputs.output_ilms_meta"] = "append"
        outputs["par.outputs.output_gds"] = str(self.output_gds)
        outputs["par.outputs.output_netlist"] = str(self.output_netlist)
        outputs["par.outputs.output_sim_netlist"] = str(self.output_sim_netlist)
        outputs["par.outputs.hcells_list"] = list(self.hcells_list)
        outputs["par.outputs.seq_cells"] = self.output_seq_cells
        outputs["par.outputs.all_regs"] = self.output_all_regs
        outputs["par.inputs.input_files"] = self.input_files
        outputs["par.inputs.top_module"] = self.top_module
        return outputs

    ### Generated interface HammerPlaceAndRouteTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def input_files(self) -> List[str]:
        """
        Get the input post-synthesis netlist files.

        :return: The input post-synthesis netlist files.
        """
        try:
            return self.attr_getter("_input_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the input post-synthesis netlist files yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """Set the input post-synthesis netlist files."""
        if not (isinstance(value, List)):
            raise TypeError("input_files must be a List[str]")
        self.attr_setter("_input_files", value)


    @property
    def post_synth_sdc(self) -> Optional[str]:
        """
        Get the (optional) input post-synthesis SDC constraint file.

        :return: The (optional) input post-synthesis SDC constraint file.
        """
        try:
            return self.attr_getter("_post_synth_sdc", None)
        except AttributeError:
            return None

    @post_synth_sdc.setter
    def post_synth_sdc(self, value: Optional[str]) -> None:
        """Set the (optional) input post-synthesis SDC constraint file."""
        if not (isinstance(value, str) or (value is None)):
            raise TypeError("post_synth_sdc must be a Optional[str]")
        self.attr_setter("_post_synth_sdc", value)


    ### Outputs ###

    @property
    def output_ilms(self) -> List[ILMStruct]:
        """
        Get the (optional) output ILM information for hierarchical mode.

        :return: The (optional) output ILM information for hierarchical mode.
        """
        try:
            return self.attr_getter("_output_ilms", None)
        except AttributeError:
            raise ValueError("Nothing set for the (optional) output ILM information for hierarchical mode yet")

    @output_ilms.setter
    def output_ilms(self, value: List[ILMStruct]) -> None:
        """Set the (optional) output ILM information for hierarchical mode."""
        if not (isinstance(value, List)):
            raise TypeError("output_ilms must be a List[ILMStruct]")
        self.attr_setter("_output_ilms", value)


    @property
    def output_gds(self) -> str:
        """
        Get the path to the output GDS file.

        :return: The path to the output GDS file.
        """
        try:
            return self.attr_getter("_output_gds", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to the output GDS file yet")

    @output_gds.setter
    def output_gds(self, value: str) -> None:
        """Set the path to the output GDS file."""
        if not (isinstance(value, str)):
            raise TypeError("output_gds must be a str")
        self.attr_setter("_output_gds", value)


    @property
    def output_netlist(self) -> str:
        """
        Get the path to the output netlist file.

        :return: The path to the output netlist file.
        """
        try:
            return self.attr_getter("_output_netlist", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to the output netlist file yet")

    @output_netlist.setter
    def output_netlist(self, value: str) -> None:
        """Set the path to the output netlist file."""
        if not (isinstance(value, str)):
            raise TypeError("output_netlist must be a str")
        self.attr_setter("_output_netlist", value)


    @property
    def output_sim_netlist(self) -> str:
        """
        Get the path to the output simulation netlist file.

        :return: The path to the output simulation netlist file.
        """
        try:
            return self.attr_getter("_output_sim_netlist", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to the output simulation netlist file yet")

    @output_sim_netlist.setter
    def output_sim_netlist(self, value: str) -> None:
        """Set the path to the output simulation netlist file."""
        if not (isinstance(value, str)):
            raise TypeError("output_sim_netlist must be a str")
        self.attr_setter("_output_sim_netlist", value)


    @property
    def hcells_list(self) -> List[str]:
        """
        Get the list of cells to explicitly map hierarchically in LVS.

        :return: The list of cells to explicitly map hierarchically in LVS.
        """
        try:
            return self.attr_getter("_hcells_list", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of cells to explicitly map hierarchically in LVS yet")

    @hcells_list.setter
    def hcells_list(self, value: List[str]) -> None:
        """Set the list of cells to explicitly map hierarchically in LVS."""
        if not (isinstance(value, List)):
            raise TypeError("hcells_list must be a List[str]")
        self.attr_setter("_hcells_list", value)


    @property
    def output_all_regs(self) -> str:
        """
        Get the path to output list of all registers in the design with output pin for gate level simulation.

        :return: The path to output list of all registers in the design with output pin for gate level simulation.
        """
        try:
            return self.attr_getter("_output_all_regs", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to output list of all registers in the design with output pin for gate level simulation yet")

    @output_all_regs.setter
    def output_all_regs(self, value: str) -> None:
        """Set the path to output list of all registers in the design with output pin for gate level simulation."""
        if not (isinstance(value, str)):
            raise TypeError("output_all_regs must be a str")
        self.attr_setter("_output_all_regs", value)


    @property
    def output_seq_cells(self) -> str:
        """
        Get the path to output collection of all sequential standard cells in design.

        :return: The path to output collection of all sequential standard cells in design.
        """
        try:
            return self.attr_getter("_output_seq_cells", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to output collection of all sequential standard cells in design yet")

    @output_seq_cells.setter
    def output_seq_cells(self, value: str) -> None:
        """Set the path to output collection of all sequential standard cells in design."""
        if not (isinstance(value, str)):
            raise TypeError("output_seq_cells must be a str")
        self.attr_setter("_output_seq_cells", value)


    @property
    def sdf_file(self) -> str:
        """
        Get the output SDF file to be read for timing annotated gate level sims.

        :return: The output SDF file to be read for timing annotated gate level sims.
        """
        try:
            return self.attr_getter("_sdf_file", None)
        except AttributeError:
            raise ValueError("Nothing set for the output SDF file to be read for timing annotated gate level sims yet")

    @sdf_file.setter
    def sdf_file(self, value: str) -> None:
        """Set the output SDF file to be read for timing annotated gate level sims."""
        if not (isinstance(value, str)):
            raise TypeError("sdf_file must be a str")
        self.attr_setter("_sdf_file", value)

    ### END Generated interface HammerPlaceAndRouteTool ###

    def create_power_straps_tcl(self) -> List[str]:
        """
        Create power straps TCL commands depending on the mode.
        """
        output = []  # type: List[str]

        power_straps_mode = str(self.get_setting("par.power_straps_mode"))
        if power_straps_mode == "manual":
            power_straps_script_contents = str(self.get_setting("par.power_straps_script_contents"))
            # TODO(edwardw): proper source locators/SourceInfo
            output.append("# Power straps script manually specified from HAMMER")
            output.extend(power_straps_script_contents.split("\n"))
        elif power_straps_mode == "generate":
            output.extend(self.generate_power_straps_tcl())
        else:
            if power_straps_mode != "empty":
                self.logger.error(
                    "Invalid power_straps_mode {mode}. Using blank power straps script.".format(mode=power_straps_mode))
            # Write blank power straps
            output.append("# Blank power straps script specified from HAMMER")
        return output

    def generate_power_straps_tcl(self) -> List[str]:
        """
        Generate a TCL script to create power straps from the config/IR.
        :return: Power straps TCL script.
        """
        method = self.get_setting("par.generate_power_straps_method")
        if method == "by_tracks":
            # By default put straps everywhere
            bbox = None # type: Optional[List[Decimal]]
            namespace = "par.generate_power_straps_options.by_tracks"
            layers = self.get_setting("{}.strap_layers".format(namespace))
            pin_layers = self.get_setting("{}.pin_layers".format(namespace))
            ground_net_names = list(map(lambda x: x.name, self.get_independent_ground_nets()))  # type: List[str]
            power_net_names = list(map(lambda x: x.name, self.get_independent_power_nets()))  # type: List[str]
            def get_weight(s: Supply) -> int:
                # Check that it's not None
                assert isinstance(s.weight, int)
                return s.weight
            weights = list(map(get_weight, self.get_independent_power_nets()))  # type: List[int]
            assert len(ground_net_names) == 1, "FIXME, I am assuming there's only 1 ground net"
            return self.specify_all_power_straps_by_tracks(layers, ground_net_names[0], power_net_names, weights, bbox, pin_layers)
        else:
            raise NotImplementedError("Power strap generation method %s is not implemented" % method)

    def specify_power_straps_by_tracks(self, layer_name: str, bottom_via_layer: str, blockage_spacing: Decimal, track_pitch: int, track_width: int, track_spacing: int, track_start: int, track_offset: Decimal, bbox: Optional[List[Decimal]], nets: List[str], add_pins: bool, layer_is_all_power: bool) -> List[str]:
        """
        Generate a list of TCL commands that will create power straps on a given layer by specifying the desired track consumption.
        This method assumes that power straps are built bottom-up, starting with standard cell rails.

        :param layer_name: The layer name of the metal on which to create straps.
        :param bottom_via_layer_name: The layer name of the lowest metal layer down to which to drop vias.
        :param blockage_spacing: The minimum spacing between the end of a strap and the beginning of a macro or blockage.
        :param track_pitch: The integer pitch between groups of power straps (i.e. from left edge of strap A to the next left edge of strap A) in units of the routing pitch.
        :param track_width: The desired number of routing tracks to consume by a single power strap.
        :param track_spacing: The desired number of USABLE routing tracks between power straps. It is recommended to leave this at 0 except to fix DRC issues.
        :param track_start: The index of the first track to start using for power straps relative to the bounding box.
        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param nets: A list of power nets to create (e.g. ["VDD", "VSS"], ["VDDA", "VSS", "VDDB"], ... etc.).
        :param add_pins: True if pins are desired on this layer; False otherwise.
        :param layer_is_all_power: True if there will be no signal wires on this layer.
        :return: A list of TCL commands that will generate power straps.
        """
        # Note: even track_widths will be snapped to a half-track
        layer = self.get_stackup().get_metal(layer_name)
        pitch = track_pitch * layer.pitch
        width = Decimal(0)
        spacing = Decimal(0)
        strap_offset = Decimal(0)
        if track_spacing == 0:
            # An all-power (100% utilization) layer results in us wanting to do a uniform strap pattern, so we can just calculate the
            # maximum width and minimum spacing from the desired pitch, instead of using TWWT.
            if layer_is_all_power:
                one_strap_pitch = track_width * layer.pitch
                spacing, width = layer.min_spacing_and_max_width_from_pitch(one_strap_pitch)
                strap_start = spacing / 2 + layer.offset
            else:
                width, spacing, strap_start = layer.get_width_spacing_start_twwt(track_width, force_even=True, logger=self.logger.context(layer_name))
        else:
            width, spacing, strap_start = layer.get_width_spacing_start_twt(track_width, logger=self.logger.context(layer_name))
            spacing = 2*spacing + (track_spacing - 1) * layer.pitch + layer.min_width
        offset = track_offset + track_start * layer.pitch + strap_start
        assert width > Decimal(0), "Width must be greater than zero. You probably have a malformed tech plugin on layer {}.".format(layer_name)
        assert spacing > Decimal(0), "Spacing must be greater than zero. You probably have a malformed tech plugin on layer {}.".format(layer_name)
        density = Decimal(len(nets)) * width / pitch * Decimal(100)
        if density > Decimal(85):
            self.logger.warning("CAUTION! Your {layer} power strap density is {density}%. Check your technology's DRM to see if this violates maximum density rules.".format(layer=layer_name, density=density))
        return self.specify_power_straps(layer_name, bottom_via_layer, blockage_spacing, pitch, width, spacing, offset, bbox, nets, add_pins)

    def specify_all_power_straps_by_tracks(self, layer_names: List[str], ground_net: str, power_nets: List[str], power_weights: List[int], bbox: Optional[List[Decimal]], pin_layers: List[str]) -> List[str]:
        """
        Generate a list of TCL commands that will create power straps on a given set of layers by specifying the desired per-track track consumption and utilization.
        This will build standard cell power strap rails first. Layer-specific parameters are read from the hammer config:
            - par.generate_power_straps_options.by_tracks.blockage_spacing
            - par.generate_power_straps_options.by_tracks.track_width
            - par.generate_power_straps_options.by_tracks.track_spacing
            - par.generate_power_straps_options.by_tracks.power_utilization
        These settings are all overridable by appending an underscore followed by the metal name (e.g. power_utilization_M3).

        :param layer_names: The list of metal layer names on which to create straps.
        :param ground_net: The name of the ground net in this design. Only 1 ground net is supported.
        :param power_nets: A list of power nets to create (not ground).
        :param power_weights: Specifies the power strap placement pattern for multiple-domain designs (e.g. ["VDDA", "VDDB"] with [2, 1] will produce 2 VDDA straps for ever 1 VDDB strap).
        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param pin_layers: A list of layers on which to place pins
        :return: A list of TCL commands that will generate power straps.
        """
        assert len(power_nets) == len(power_weights)

        # Do some sanity checking
        for l in pin_layers:
            assert l in layer_names, "Pin layer {} must be in power strap layers".format(l)

        rail_layer_name = self.get_setting("technology.core.std_cell_rail_layer")
        rail_layer = self.get_stackup().get_metal(rail_layer_name)
        blockage_spacing = coerce_to_grid(float(self._get_by_tracks_metal_setting("blockage_spacing", rail_layer_name)), rail_layer.grid_unit)
        # TODO does the CPF help this, or do we need to be more explicit about the bbox for each domain
        output = self.specify_std_cell_power_straps(blockage_spacing, bbox, [ground_net] + power_nets)
        # The layer to via down to
        bottom_via_layer = rail_layer_name
        # The last layer we used
        last = rail_layer
        for layer_name in layer_names:
            layer = self.get_stackup().get_metal(layer_name)
            assert layer.index > last.index, "Must build power straps bottom-up"
            if last.direction == layer.direction:
                raise ValueError("Layers {a} and {b} run in the same direction, but have no power straps between them.".format(a=last.name, b=layer.name))

            blockage_spacing = coerce_to_grid(float(self._get_by_tracks_metal_setting("blockage_spacing", layer_name)), layer.grid_unit)
            track_width = int(self._get_by_tracks_metal_setting("track_width", layer_name))
            track_spacing = int(self._get_by_tracks_metal_setting("track_spacing", layer_name))
            track_start = int(self._get_by_tracks_metal_setting("track_start", layer_name))
            track_pitch = self._get_by_tracks_track_pitch(layer_name)
            track_offset = Decimal(str(self._get_by_tracks_metal_setting("track_offset", layer_name)))
            offset = layer.offset # TODO this is relaxable if we can auto-recalculate this based on hierarchical setting

            add_pins = layer_name in pin_layers
            # For multiple domains, we'll stripe them like this:
            # 2:1 :   A A B A A B ...
            # 3:1 :   A A A B A A A B ...
            # 3:2 :   A A A B B A A A B B ...
            # 2:2:1 : A A B B C A A B B C ...
            sum_weights = sum(power_weights)
            # If the power + ground tracks are equal to the pitch, we have no signals
            layer_is_all_power = (2 * track_width) == track_pitch
            for i in range(sum_weights):
                nets = [ground_net, power_nets[i]]
                group_offset = offset + track_offset + track_pitch * i * layer.pitch
                group_pitch = sum_weights * track_pitch
                output.extend(self.specify_power_straps_by_tracks(layer_name, last.name, blockage_spacing, group_pitch, track_width, track_spacing, track_start, group_offset, bbox, nets, add_pins, layer_is_all_power))
            last = layer
        return output

    _power_straps_last_index = -1

    def _power_straps_check_index(self, layer_name: str) -> None:
        next_index = self.get_stackup().get_metal(layer_name).index
        assert next_index >= self._power_straps_last_index, "Must construct power straps from bottom to top"
        self._power_straps_last_index = next_index

    def _get_by_tracks_metal_setting(self, key: str, layer_name: str) -> Any:
        """
        Return the metal setting used by the by_tracks power strap generation method.
        This will return the value from the provided key in the par.generate_power_straps.by_tracks namespace,
        which can be overridden for a specific metal layer by appending _<layer name>.

        :param key: The base key name (e.g. track_spacing). Do not include the namespace or metal override.
        :return: The value associated with the key, after applying any metal overrides
        """
        default = "par.generate_power_straps_options.by_tracks." + key
        override = default + "_" + layer_name
        try:
            return self.get_setting(override)
        except KeyError:
            try:
                return self.get_setting(default)
            except KeyError:
                raise ValueError("No value set for key {}".format(default))

    def _get_by_tracks_track_pitch(self, layer_name: str) -> int:
        """
        Returns the track pitch used by the by_tracks power rail generation method

        :param layer_name: The string name of the metal layer
        :return: The power strap group pitch in tracks
        """
        track_width = int(self._get_by_tracks_metal_setting("track_width", layer_name))
        track_spacing = int(self._get_by_tracks_metal_setting("track_spacing", layer_name))
        power_utilization = float(self._get_by_tracks_metal_setting("power_utilization", layer_name))

        assert power_utilization > 0.0
        assert power_utilization <= 1.0

        # Calculate how many tracks we consume
        # This strategy uses pairs of power and ground
        consumed_tracks = 2 * track_width + track_spacing
        return round(consumed_tracks / power_utilization)

    @abstractmethod
    def specify_power_straps(self, layer_name: str, bottom_via_layer_name: str, blockage_spacing: Decimal, pitch: Decimal, width: Decimal, spacing: Decimal, offset: Decimal, bbox: Optional[List[Decimal]], nets: List[str], add_pins: bool) -> List[str]:
        """
        Generate a list of TCL commands that will create power straps on a given layer.
        This is a low-level, cad-tool-specific API. It is designed to be called by higher-level methods, so calling this directly is not recommended.
        This method assumes that power straps are built bottom-up, starting with standard cell rails.

        :param layer_name: The layer name of the metal on which to create straps.
        :param bottom_via_layer_name: The layer name of the lowest metal layer down to which to drop vias.
        :param blockage_spacing: The minimum spacing between the end of a strap and the beginning of a macro or blockage.
        :param pitch: The pitch between groups of power straps (i.e. from left edge of strap A to the next left edge of strap A).
        :param width: The width of each strap in a group.
        :param spacing: The spacing between straps in a group.
        :param offset: The offset to start the first group.
        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param nets: A list of power nets to create (e.g. ["VDD", "VSS"], ["VDDA", "VSS", "VDDB"],  ... etc.).
        :param add_pins: True if pins are desired on this layer; False otherwise.
        :return: A list of TCL commands that will generate power straps.
        """
        # This should get overriden but be sure to use this check in your implementations
        self._power_straps_check_index(layer_name)
        return []

    @abstractmethod
    def specify_std_cell_power_straps(self, blockage_spacing: Decimal, bbox: Optional[List[Decimal]], nets: List[str]) -> List[str]:
        """
        Generate a list of TCL commands that build the low-level standard cell power strap rails.
        This is a low-level, cad-tool-specific API. It is designed to be called by higher-level methods, so calling this directly is not recommended.
        This will create power straps based on technology.core.tap_cell_rail_reference.
        The layer is set by technology.core.std_cell_rail_layer, which should be the highest metal layer in the std cell rails.
        This method should be called before any calls to specify_power_straps.

        :param blockage_spacing: The spacing to leave between the end of a stripe and a macro or routing blockage.
        :param bbox: The optional (2N)-point bounding box of the area to generate straps. By default the entire core area is used.
        :param nets: A list of power net names (e.g. ["VDD", "VSS"]).
        :return: A list of TCL commands that will generate power straps on rails.
        """
        # This should get overriden but be sure to use this check in your implementations
        layer_name = self.get_setting("technology.core.std_cell_rail_layer")
        self._power_straps_check_index(layer_name)
        return []


class HammerSignoffTool(HammerTool):
    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    ### Inputs ###

    ### Outputs ###
    @abstractmethod
    def signoff_results(self) -> int:
        """
        Return the number of issues raised by the signoff tool (0 = all checks pass).
        Individual tools extending HammerSignoffTool should implement their own *_results methods that provide tool-specific information,
        and then pass a meaningful count of issues to their implementation of this method.

        :return: The number of signoff issues raised by the tool
        """
        pass

class HammerDRCTool(HammerSignoffTool):

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = deepdict(super().export_config_outputs())
        outputs["drc.inputs.top_module"] = self.top_module
        return outputs

    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    @abstractmethod
    def globally_waived_drc_rules(self) -> List[str]:
        # TODO(johnwright) how to waive specific instances of DRC rules, rather than blanket waivers
        # TODO(johnwright) should this go in the YAML file?
        """
        Get the list of waived DRC rule names.

        :return: The list of waived DRC rule names.
        """
        pass

    def drc_rules_to_run(self) -> List[str]:
        """
        Return a list of the specific DRC rules to run. If empty, run all rules (the default).

        :return: A list of DRC rules to run or an empty list if running all rules
        """
        res = self.get_setting("drc.inputs.drc_rules_to_run", [])  # type: List[str]
        assert isinstance(res, list)
        return res

    def get_drc_decks(self) -> List[hammer_tech.DRCDeck]:
        """ Get all DRC decks for this tool. """
        return self.technology.get_drc_decks_for_tool(self.name)

    def get_additional_drc_text(self) -> str:
        """ Get the additional custom DRC command text to add after the boilerplate commands at the top of the DRC run file. """

        # Mode can be auto, manual, append, or prepend
        add_drc_text_mode = str(self.get_setting("drc.inputs.additional_drc_text_mode"))

        # manul_add_drc_text will only be used in manual, append, and prepend modes
        manual_add_drc_text = str(self.get_setting("drc.inputs.additional_drc_text"))

        # tech_add_drc_text will only be used in auto, append, and prepend modes
        tech_add_drc_text = get_or_else(self.technology.additional_drc_text, "") # type: str

        # Default to auto (use tech_add_drc_text)
        add_drc_text = tech_add_drc_text

        if add_drc_text_mode == "auto":
            pass
        elif add_drc_text_mode == "manual":
            add_drc_text = manual_add_drc_text
        elif add_drc_text_mode == "append":
            add_drc_text = tech_add_drc_text + manual_add_drc_text
        elif add_drc_text_mode == "prepend":
            add_drc_text = manual_add_drc_text + tech_add_drc_text
        else:
            self.logger.error(
                "Invalid additional_drc_text_mode {mode}. Using auto.".format(mode=add_drc_text_mode))

        return add_drc_text

    @abstractmethod
    def drc_results_pre_waived(self) -> Dict[str, int]:
        """ Return a Dict mapping the DRC check name to an error count (pre-waivers). """
        pass

    def signoff_results(self) -> int:
        """ Return the count of unwaived DRC errors. """
        return sum(self.drc_results().values())

    def drc_results(self) -> Dict[str, int]:
        """ Return a Dict mapping the DRC check name to an error count (with waivers). """
        res = self.drc_results_pre_waived()
        return {k: 0 if k in self.globally_waived_drc_rules() else int(res[k]) for k in res}

    ### Generated interface HammerDRCTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def layout_file(self) -> str:
        """
        Get the path to the input layout file (e.g. a *.gds).

        :return: The path to the input layout file (e.g. a *.gds).
        """
        try:
            return self.attr_getter("_layout_file", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to the input layout file (e.g. a *.gds) yet")

    @layout_file.setter
    def layout_file(self, value: str) -> None:
        """Set the path to the input layout file (e.g. a *.gds)."""
        if not (isinstance(value, str)):
            raise TypeError("layout_file must be a str")
        self.attr_setter("_layout_file", value)


    ### Outputs ###
    ### END Generated interface HammerDRCTool ###


class HammerLVSTool(HammerSignoffTool):

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = deepdict(super().export_config_outputs())
        outputs["lvs.inputs.top_module"] = self.top_module
        return outputs

    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    @abstractmethod
    def globally_waived_erc_rules(self) -> List[str]:
        # TODO(johnwright) how to waive specific instances of ERC rules, rather than blanket waivers
        # TODO(johnwright) should this go in the YAML file?
        """
        Get the list of waived ERC rule names.

        :return: The list of waived ERC rule names.
        """
        pass

    @abstractmethod
    def erc_results_pre_waived(self) -> Dict[str, int]:
        """ Return a Dict mapping the ERC check name to an error count (pre-waivers). """
        pass

    def signoff_results(self) -> int:
        """ Return the count of unwaived ERC errors and LVS errors. """
        return sum(self.erc_results().values()) + len(self.lvs_results())

    def erc_results(self) -> Dict[str, int]:
        """ Return a Dict mapping the ERC check name to an error count (with waivers). """
        res = self.erc_results_pre_waived()
        return {k: 0 if k in self.globally_waived_erc_rules() else int(res[k]) for k in res}

    @abstractmethod
    def lvs_results(self) -> List[str]:
        """ Return the LVS issue descriptions for each issue. An empty list means LVS passes. """
        pass

    def get_lvs_decks(self) -> List[hammer_tech.LVSDeck]:
        """ Get all the LVS decks for this tool. """
        return self.technology.get_lvs_decks_for_tool(self.name)

    def get_additional_lvs_text(self) -> str:
        """ Get the additional custom LVS command text to add after the boilerplate commands at the top of the LVS run file. """

        # Mode can be auto, manual, append, or prepend
        add_lvs_text_mode = str(self.get_setting("lvs.inputs.additional_lvs_text_mode"))

        # manul_add_lvs_text will only be used in manual, append, and prepend modes
        manual_add_lvs_text = str(self.get_setting("lvs.inputs.additional_lvs_text"))

        # tech_add_lvs_text will only be used in auto, append, and prepend modes
        tech_add_lvs_text = get_or_else(self.technology.additional_lvs_text, "") # type: str

        # Default to auto (use tech_add_lvs_text)
        add_lvs_text = tech_add_lvs_text

        if add_lvs_text_mode == "auto":
            pass
        elif add_lvs_text_mode == "manual":
            add_lvs_text = manual_add_lvs_text
        elif add_lvs_text_mode == "append":
            add_lvs_text = tech_add_lvs_text + manual_add_lvs_text
        elif add_lvs_text_mode == "prepend":
            add_lvs_text = manual_add_lvs_text + tech_add_lvs_text
        else:
            self.logger.error(
                "Invalid additional_lvs_text_mode {mode}. Using auto.".format(mode=add_lvs_text_mode))

        return add_lvs_text

    ### Generated interface HammerLVSTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def layout_file(self) -> str:
        """
        Get the path to the input layout file (e.g. a *.gds).

        :return: The path to the input layout file (e.g. a *.gds).
        """
        try:
            return self.attr_getter("_layout_file", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to the input layout file (e.g. a *.gds) yet")

    @layout_file.setter
    def layout_file(self, value: str) -> None:
        """Set the path to the input layout file (e.g. a *.gds)."""
        if not (isinstance(value, str)):
            raise TypeError("layout_file must be a str")
        self.attr_setter("_layout_file", value)


    @property
    def schematic_files(self) -> List[str]:
        """
        Get the path to the input SPICE or Verilog schematic files (e.g. *.v or *.spi).

        :return: The path to the input SPICE or Verilog schematic files (e.g. *.v or *.spi).
        """
        try:
            return self.attr_getter("_schematic_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to the input SPICE or Verilog schematic files (e.g. *.v or *.spi) yet")

    @schematic_files.setter
    def schematic_files(self, value: List[str]) -> None:
        """Set the path to the input SPICE or Verilog schematic files (e.g. *.v or *.spi)."""
        if not (isinstance(value, List)):
            raise TypeError("schematic_files must be a List[str]")
        self.attr_setter("_schematic_files", value)


    @property
    def hcells_list(self) -> List[str]:
        """
        Get the list of cells to explicitly map hierarchically in LVS.

        :return: The list of cells to explicitly map hierarchically in LVS.
        """
        try:
            return self.attr_getter("_hcells_list", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of cells to explicitly map hierarchically in LVS yet")

    @hcells_list.setter
    def hcells_list(self, value: List[str]) -> None:
        """Set the list of cells to explicitly map hierarchically in LVS."""
        if not (isinstance(value, List)):
            raise TypeError("hcells_list must be a List[str]")
        self.attr_setter("_hcells_list", value)


    @property
    def ilms(self) -> List[ILMStruct]:
        """
        Get the list of (optional) input ILM information for hierarchical mode.

        :return: The list of (optional) input ILM information for hierarchical mode.
        """
        try:
            return self.attr_getter("_ilms", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of (optional) input ILM information for hierarchical mode yet")

    @ilms.setter
    def ilms(self, value: List[ILMStruct]) -> None:
        """Set the list of (optional) input ILM information for hierarchical mode."""
        if not (isinstance(value, List)):
            raise TypeError("ilms must be a List[ILMStruct]")
        self.attr_setter("_ilms", value)


    ### Outputs ###
    ### END Generated interface HammerLVSTool ###


class HammerSimTool(HammerTool):

    def export_config_outputs(self) -> Dict[str, Any]:
        outputs = deepdict(super().export_config_outputs())
        outputs["sim.outputs.waveforms"] = self.output_waveforms
        outputs["sim.outputs.saifs"] = self.output_saifs
        outputs["sim.outputs.output_top_module"] = self.output_top_module
        outputs["sim.outputs.output_tb_name"] = self.output_tb_name
        outputs["sim.outputs.output_tb_dut"] = self.output_tb_dut
        outputs["sim.outputs.output_level"] = self.output_level
        return outputs

    @property
    def level(self) -> FlowLevel:
        """Return the flow level."""
        return FlowLevel.from_str(self.get_setting("sim.inputs.level"))

    @property
    def benchmarks(self) -> List[str]:
        """Return the benchmarks to run."""
        # TODO(ucb-bar/hammer#462) We may want to make these keys that point to a "Benchmarks" library type
        bms = list(self.get_setting("sim.inputs.benchmarks", []))  # type: List[str]
        return bms

    ### Generated interface HammerSimTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def top_module(self) -> str:
        """
        Get the top RTL module.

        :return: The top RTL module.
        """
        try:
            return self.attr_getter("_top_module", None)
        except AttributeError:
            raise ValueError("Nothing set for the top RTL module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top RTL module."""
        if not (isinstance(value, str)):
            raise TypeError("top_module must be a str")
        self.attr_setter("_top_module", value)


    @property
    def input_files(self) -> List[str]:
        """
        Get the paths to input verilog files.

        :return: The paths to input verilog files.
        """
        try:
            return self.attr_getter("_input_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the paths to input verilog files yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """Set the paths to input verilog files."""
        if not (isinstance(value, List)):
            raise TypeError("input_files must be a List[str]")
        self.attr_setter("_input_files", value)


    @property
    def all_regs(self) -> str:
        """
        Get the path to list of all registers in the design with output pin.

        :return: The path to list of all registers in the design with output pin.
        """
        try:
            return self.attr_getter("_all_regs", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to list of all registers in the design with output pin yet")

    @all_regs.setter
    def all_regs(self, value: str) -> None:
        """Set the path to list of all registers in the design with output pin."""
        if not (isinstance(value, str)):
            raise TypeError("all_regs must be a str")
        self.attr_setter("_all_regs", value)


    @property
    def seq_cells(self) -> str:
        """
        Get the path to collection of all sequential standard cells in design.

        :return: The path to collection of all sequential standard cells in design.
        """
        try:
            return self.attr_getter("_seq_cells", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to collection of all sequential standard cells in design yet")

    @seq_cells.setter
    def seq_cells(self, value: str) -> None:
        """Set the path to collection of all sequential standard cells in design."""
        if not (isinstance(value, str)):
            raise TypeError("seq_cells must be a str")
        self.attr_setter("_seq_cells", value)


    @property
    def sdf_file(self) -> Optional[str]:
        """
        Get the optional SDF file needed for timing annotated gate level sims.

        :return: The optional SDF file needed for timing annotated gate level sims.
        """
        try:
            return self.attr_getter("_sdf_file", None)
        except AttributeError:
            return None

    @sdf_file.setter
    def sdf_file(self, value: Optional[str]) -> None:
        """Set the optional SDF file needed for timing annotated gate level sims."""
        if not (isinstance(value, str) or (value is None)):
            raise TypeError("sdf_file must be a Optional[str]")
        self.attr_setter("_sdf_file", value)


    ### Outputs ###

    @property
    def output_waveforms(self) -> List[str]:
        """
        Get the paths to output waveforms.

        :return: The paths to output waveforms.
        """
        try:
            return self.attr_getter("_output_waveforms", None)
        except AttributeError:
            raise ValueError("Nothing set for the paths to output waveforms yet")

    @output_waveforms.setter
    def output_waveforms(self, value: List[str]) -> None:
        """Set the paths to output waveforms."""
        if not (isinstance(value, List)):
            raise TypeError("output_waveforms must be a List[str]")
        self.attr_setter("_output_waveforms", value)


    @property
    def output_saifs(self) -> List[str]:
        """
        Get the paths to output activity files.

        :return: The paths to output activity files.
        """
        try:
            return self.attr_getter("_output_saifs", None)
        except AttributeError:
            raise ValueError("Nothing set for the paths to output activity files yet")

    @output_saifs.setter
    def output_saifs(self, value: List[str]) -> None:
        """Set the paths to output activity files."""
        if not (isinstance(value, List)):
            raise TypeError("output_saifs must be a List[str]")
        self.attr_setter("_output_saifs", value)


    @property
    def output_top_module(self) -> str:
        """
        Get the top RTL module.

        :return: The top RTL module.
        """
        try:
            return self.attr_getter("_output_top_module", None)
        except AttributeError:
            raise ValueError("Nothing set for the top RTL module yet")

    @output_top_module.setter
    def output_top_module(self, value: str) -> None:
        """Set the top RTL module."""
        if not (isinstance(value, str)):
            raise TypeError("output_top_module must be a str")
        self.attr_setter("_output_top_module", value)


    @property
    def output_tb_name(self) -> str:
        """
        Get the sim testbench name.

        :return: The sim testbench name.
        """
        try:
            return self.attr_getter("_output_tb_name", None)
        except AttributeError:
            raise ValueError("Nothing set for the sim testbench name yet")

    @output_tb_name.setter
    def output_tb_name(self, value: str) -> None:
        """Set the sim testbench name."""
        if not (isinstance(value, str)):
            raise TypeError("output_tb_name must be a str")
        self.attr_setter("_output_tb_name", value)


    @property
    def output_tb_dut(self) -> str:
        """
        Get the sim DUT instance name.

        :return: The sim DUT instance name.
        """
        try:
            return self.attr_getter("_output_tb_dut", None)
        except AttributeError:
            raise ValueError("Nothing set for the sim DUT instance name yet")

    @output_tb_dut.setter
    def output_tb_dut(self, value: str) -> None:
        """Set the sim DUT instance name."""
        if not (isinstance(value, str)):
            raise TypeError("output_tb_dut must be a str")
        self.attr_setter("_output_tb_dut", value)


    @property
    def output_level(self) -> str:
        """
        Get the simulation flow level.

        :return: The simulation flow level.
        """
        try:
            return self.attr_getter("_output_level", None)
        except AttributeError:
            raise ValueError("Nothing set for the simulation flow level yet")

    @output_level.setter
    def output_level(self, value: str) -> None:
        """Set the simulation flow level."""
        if not (isinstance(value, str)):
            raise TypeError("output_level must be a str")
        self.attr_setter("_output_level", value)

    ### END Generated interface HammerSimTool ###

class HammerPowerTool(HammerTool):

    @property
    def level(self) -> FlowLevel:
        """Return the flow level."""
        return FlowLevel.from_str(self.get_setting("power.inputs.level"))

    def get_power_report_configs(self) -> List[PowerReport]:
        """
        Get the power report config settings
        """
        configs = self.get_setting("power.inputs.report_configs")
        output = []
        for config in configs:
            report = PowerReport(
                waveform_path=config["waveform_path"], module=None,
                levels=None, start_time=None,
                end_time=None, toggle_signal=None,
                num_toggles=None, frame_count=None,
                report_name=None
            )
            if "module" in config:
                report = report._replace(module=config["module"])
            if "levels" in config:
                report = report._replace(levels=config["levels"])
            if "start_time" in config:
                start_time = report._replace(start_time=TimeValue(config["start_time"]))
            if "end_time" in config:
                report = report._replace(end_time=TimeValue(config["end_time"]))
            if "toggle_signal" in config:
                report = report._replace(toggle_signal=config["toggle_signal"])
            if "num_toggles" in config:
                report = report._replace(num_toggles=config["num_toggles"])
            if "frame_count" in config:
                report = report._replace(frame_count=config["frame_count"])
            if "report_name" in config:
                report = report._replace(report_name=config["report_name"])
            output.append(report)
        return output

    ### Generated interface HammerPowerTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def flow_database(self) -> str:
        """
        Get the path to syn or par database for power analysis.

        :return: The path to syn or par database for power analysis.
        """
        try:
            return self.attr_getter("_flow_database", None)
        except AttributeError:
            raise ValueError("Nothing set for the path to syn or par database for power analysis yet")

    @flow_database.setter
    def flow_database(self, value: str) -> None:
        """Set the path to syn or par database for power analysis."""
        if not (isinstance(value, str)):
            raise TypeError("flow_database must be a str")
        self.attr_setter("_flow_database", value)


    @property
    def input_files(self) -> List[str]:
        """
        Get the paths to RTL input files or design netlist.

        :return: The paths to RTL input files or design netlist.
        """
        try:
            return self.attr_getter("_input_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the paths to RTL input files or design netlist yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """Set the paths to RTL input files or design netlist."""
        if not (isinstance(value, List)):
            raise TypeError("input_files must be a List[str]")
        self.attr_setter("_input_files", value)


    @property
    def spefs(self) -> List[str]:
        """
        Get the list of spef files for power anlaysis.

        :return: The list of spef files for power anlaysis.
        """
        try:
            return self.attr_getter("_spefs", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of spef files for power anlaysis yet")

    @spefs.setter
    def spefs(self, value: List[str]) -> None:
        """Set the list of spef files for power anlaysis."""
        if not (isinstance(value, List)):
            raise TypeError("spefs must be a List[str]")
        self.attr_setter("_spefs", value)


    @property
    def sdc(self) -> Optional[str]:
        """
        Get the (optional) input SDC constraint file.

        :return: The (optional) input SDC constraint file.
        """
        try:
            return self.attr_getter("_sdc", None)
        except AttributeError:
            return None

    @sdc.setter
    def sdc(self, value: Optional[str]) -> None:
        """Set the (optional) input SDC constraint file."""
        if not (isinstance(value, str) or (value is None)):
            raise TypeError("sdc must be a Optional[str]")
        self.attr_setter("_sdc", value)


    @property
    def waveforms(self) -> List[str]:
        """
        Get the list of waveform dump files for dynamic power analysis.

        :return: The list of waveform dump files for dynamic power analysis.
        """
        try:
            return self.attr_getter("_waveforms", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of waveform dump files for dynamic power analysis yet")

    @waveforms.setter
    def waveforms(self, value: List[str]) -> None:
        """Set the list of waveform dump files for dynamic power analysis."""
        if not (isinstance(value, List)):
            raise TypeError("waveforms must be a List[str]")
        self.attr_setter("_waveforms", value)


    @property
    def saifs(self) -> List[str]:
        """
        Get the list of activity files for dynamic power analysis.

        :return: The list of activity files for dynamic power analysis.
        """
        try:
            return self.attr_getter("_saifs", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of activity files for dynamic power analysis yet")

    @saifs.setter
    def saifs(self, value: List[str]) -> None:
        """Set the list of activity files for dynamic power analysis."""
        if not (isinstance(value, List)):
            raise TypeError("saifs must be a List[str]")
        self.attr_setter("_saifs", value)


    @property
    def top_module(self) -> str:
        """
        Get the top RTL module.

        :return: The top RTL module.
        """
        try:
            return self.attr_getter("_top_module", None)
        except AttributeError:
            raise ValueError("Nothing set for the top RTL module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top RTL module."""
        if not (isinstance(value, str)):
            raise TypeError("top_module must be a str")
        self.attr_setter("_top_module", value)


    @property
    def tb_name(self) -> str:
        """
        Get the testbench name.

        :return: The testbench name.
        """
        try:
            return self.attr_getter("_tb_name", None)
        except AttributeError:
            raise ValueError("Nothing set for the testbench name yet")

    @tb_name.setter
    def tb_name(self, value: str) -> None:
        """Set the testbench name."""
        if not (isinstance(value, str)):
            raise TypeError("tb_name must be a str")
        self.attr_setter("_tb_name", value)


    @property
    def tb_dut(self) -> str:
        """
        Get the DUT instance name.

        :return: The DUT instance name.
        """
        try:
            return self.attr_getter("_tb_dut", None)
        except AttributeError:
            raise ValueError("Nothing set for the DUT instance name yet")

    @tb_dut.setter
    def tb_dut(self, value: str) -> None:
        """Set the DUT instance name."""
        if not (isinstance(value, str)):
            raise TypeError("tb_dut must be a str")
        self.attr_setter("_tb_dut", value)


    ### Outputs ###
    ### END Generated interface HammerPowerTool ###

class HammerFormalTool(HammerTool):

    ### Generated interface HammerFormalTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def check(self) -> str:
        """
        Get the formal verification check type to run.

        :return: The formal verification check type to run.
        """
        try:
            return self.attr_getter("_check", None)
        except AttributeError:
            raise ValueError("Nothing set for the formal verification check type to run yet")

    @check.setter
    def check(self, value: str) -> None:
        """Set the formal verification check type to run."""
        if not (isinstance(value, str)):
            raise TypeError("check must be a str")
        self.attr_setter("_check", value)


    @property
    def input_files(self) -> List[str]:
        """
        Get the input collection of implementation design files.

        :return: The input collection of implementation design files.
        """
        try:
            return self.attr_getter("_input_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the input collection of implementation design files yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """Set the input collection of implementation design files."""
        if not (isinstance(value, List)):
            raise TypeError("input_files must be a List[str]")
        self.attr_setter("_input_files", value)


    @property
    def reference_files(self) -> List[str]:
        """
        Get the input collection of reference design files.

        :return: The input collection of reference design files.
        """
        try:
            return self.attr_getter("_reference_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the input collection of reference design files yet")

    @reference_files.setter
    def reference_files(self, value: List[str]) -> None:
        """Set the input collection of reference design files."""
        if not (isinstance(value, List)):
            raise TypeError("reference_files must be a List[str]")
        self.attr_setter("_reference_files", value)


    @property
    def top_module(self) -> str:
        """
        Get the top RTL module.

        :return: The top RTL module.
        """
        try:
            return self.attr_getter("_top_module", None)
        except AttributeError:
            raise ValueError("Nothing set for the top RTL module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top RTL module."""
        if not (isinstance(value, str)):
            raise TypeError("top_module must be a str")
        self.attr_setter("_top_module", value)


    @property
    def post_synth_sdc(self) -> Optional[str]:
        """
        Get the (optional) input post-synthesis SDC constraint file.

        :return: The (optional) input post-synthesis SDC constraint file.
        """
        try:
            return self.attr_getter("_post_synth_sdc", None)
        except AttributeError:
            return None

    @post_synth_sdc.setter
    def post_synth_sdc(self, value: Optional[str]) -> None:
        """Set the (optional) input post-synthesis SDC constraint file."""
        if not (isinstance(value, str) or (value is None)):
            raise TypeError("post_synth_sdc must be a Optional[str]")
        self.attr_setter("_post_synth_sdc", value)


    ### Outputs ###
    ### END Generated interface HammerFormalTool ###

class HammerTimingTool(HammerTool):

    @property
    def max_paths(self) -> FlowLevel:
        """Return the max paths to report."""
        return self.get_setting("timing.inputs.max_paths")


    ### Generated interface HammerTimingTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    @property
    def input_files(self) -> List[str]:
        """
        Get the input collection of design files.

        :return: The input collection of design files.
        """
        try:
            return self.attr_getter("_input_files", None)
        except AttributeError:
            raise ValueError("Nothing set for the input collection of design files yet")

    @input_files.setter
    def input_files(self, value: List[str]) -> None:
        """Set the input collection of design files."""
        if not (isinstance(value, List)):
            raise TypeError("input_files must be a List[str]")
        self.attr_setter("_input_files", value)


    @property
    def top_module(self) -> str:
        """
        Get the top RTL module.

        :return: The top RTL module.
        """
        try:
            return self.attr_getter("_top_module", None)
        except AttributeError:
            raise ValueError("Nothing set for the top RTL module yet")

    @top_module.setter
    def top_module(self, value: str) -> None:
        """Set the top RTL module."""
        if not (isinstance(value, str)):
            raise TypeError("top_module must be a str")
        self.attr_setter("_top_module", value)


    @property
    def post_synth_sdc(self) -> Optional[str]:
        """
        Get the (optional) input post-synthesis SDC constraint file.

        :return: The (optional) input post-synthesis SDC constraint file.
        """
        try:
            return self.attr_getter("_post_synth_sdc", None)
        except AttributeError:
            return None

    @post_synth_sdc.setter
    def post_synth_sdc(self, value: Optional[str]) -> None:
        """Set the (optional) input post-synthesis SDC constraint file."""
        if not (isinstance(value, str) or (value is None)):
            raise TypeError("post_synth_sdc must be a Optional[str]")
        self.attr_setter("_post_synth_sdc", value)


    @property
    def spefs(self) -> Optional[List]:
        """
        Get the (optional) list of SPEF files.

        :return: The (optional) list of SPEF files.
        """
        try:
            return self.attr_getter("_spefs", None)
        except AttributeError:
            return None

    @spefs.setter
    def spefs(self, value: Optional[List]) -> None:
        """Set the (optional) list of SPEF files."""
        if not (isinstance(value, List) or (value is None)):
            raise TypeError("spefs must be a Optional[List]")
        self.attr_setter("_spefs", value)


    @property
    def sdf_file(self) -> Optional[str]:
        """
        Get the (optional) input SDF file.

        :return: The (optional) input SDF file.
        """
        try:
            return self.attr_getter("_sdf_file", None)
        except AttributeError:
            return None

    @sdf_file.setter
    def sdf_file(self, value: Optional[str]) -> None:
        """Set the (optional) input SDF file."""
        if not (isinstance(value, str) or (value is None)):
            raise TypeError("sdf_file must be a Optional[str]")
        self.attr_setter("_sdf_file", value)


    ### Outputs ###
    ### END Generated interface HammerTimingTool ###

class HasUPFSupport(HammerTool):
    """Mix-in trait with functions useful for tools with UPF style power
    constraints"""
    @property
    def upf_power_specification(self) -> str:
        raise NotImplementedError("Automatic generation of UPF power specifications is not supported yet.")


class HasCPFSupport(HammerTool):
    """Mix-in trait with functions useful for tools with CPF style power
    constraints"""
    @property
    def cpf_power_specification(self) -> str:
        output = [] # type: List[str]
        # Just names
        domain = "AO"
        condition = "nominal"
        mode = "aon"
        # Header
        output.append("set_cpf_version 1.0e")
        output.append("set_hierarchy_separator /")

        output.append("set_design {t}".format(t=self.top_module))
        # Define power and ground nets
        power_nets = self.get_all_power_nets() # type: List[Supply]
        ground_nets = self.get_all_ground_nets() # type: List[Supply]
        vdd = VoltageValue(self.get_setting("vlsi.inputs.supplies.VDD")) # type: VoltageValue
        output.append("create_power_nets -nets {{ {p} }} -voltage {v}".
                format(p=" ".join(map(lambda x: x.name, power_nets)), v=vdd.value))
        output.append("create_ground_nets -nets {{ {g} }}".
                format(g=" ".join(map(lambda x: x.name, ground_nets))))

        # Define power domain and connections
        output.append("create_power_domain -name {d} -default".format(d=domain))
        # Assume primary power are first in list
        output.append("update_power_domain -name {d} -primary_power_net {pp} -primary_ground_net {pg}".
                format(d=domain, pp=power_nets[0].name, pg=ground_nets[0].name))
        # Assuming that all power/ground nets correspond to pins
        for pg_net in (power_nets+ground_nets):
            if(pg_net.pin != None):
                output.append("create_global_connection -domain {d} -net {n} -pins {p}".
                        format(d=domain, n=pg_net.name, p=pg_net.pin))

        # Create nominal operation condtion and power mode
        output.append("create_nominal_condition -name {c} -voltage {v}".
                format(c=condition, v=vdd.value))
        output.append("create_power_mode -name {m} -default -domain_conditions {{{d}@{c}}}".
                format(m=mode, d=domain, c=condition))

        # Footer
        output.append("end_design")

        return "\n".join(output)

class HasSDCSupport(HammerTool):
    """Mix-in trait with functions useful for tools with SDC-style
    constraints."""
    @property
    def sdc_clock_constraints(self) -> str:
        """Generate TCL fragments for top module clock constraints."""
        output = [] # type: List[str]
        groups = {} # type: Dict[str, List[str]]
        ungrouped_clocks = [] # type: List[str]

        clocks = self.get_clock_ports()
        time_unit = self.get_time_unit().value_prefix + self.get_time_unit().unit
        for clock in clocks:
            # TODO: FIXME This assumes that library units are always in ns!!!
            if get_or_else(clock.generated, False):
                output.append("create_generated_clock -name {n} -source {m_path} -divide_by {div} {path}".
                        format(n=clock.name, m_path=clock.source_path, div=clock.divisor, path=clock.path))
            elif clock.path is not None:
                output.append("create_clock {0} -name {1} -period {2}".format(clock.path, clock.name, clock.period.value_in_units(time_unit)))
            else:
                output.append("create_clock {0} -name {0} -period {1}".format(clock.name, clock.period.value_in_units(time_unit)))
            if clock.uncertainty is not None:
                output.append("set_clock_uncertainty {1} [get_clocks {0}]".format(clock.name, clock.uncertainty.value_in_units(time_unit)))
            if clock.group is not None:
                if clock.group in groups:
                    groups[clock.group].append(clock.name)
                else:
                    groups[clock.group] = [clock.name]
            else:
                ungrouped_clocks.append(clock.name)
        if len(clocks):
            output.append("set_clock_groups -asynchronous {grouped} {ungrouped}".format(
                    grouped = " ".join(["-group {{ {c} }}".format(c=" ".join(clks)) for clks in groups.values()]),
                    ungrouped = " ".join(["-group {{ {c} }}".format(c=clk) for clk in ungrouped_clocks])
                    ))

        output.append("\n")
        return "\n".join(output)

    @property
    def sdc_pin_constraints(self) -> str:
        """Generate a fragment for I/O pin constraints."""
        output = []  # type: List[str]

        default_output_load = float(self.get_setting("vlsi.inputs.default_output_load"))

        # Specify default load.
        output.append("set_load {load} [all_outputs]".format(
            load=default_output_load
        ))

        # Also specify loads for specific pins.
        for load in self.get_output_load_constraints():
            output.append("set_load {load} [get_port \"{name}\"]".format(
                load=load.load,
                name=load.name
            ))

        # Also specify delays for specific pins.
        for delay in self.get_delay_constraints():
            output.append("set_{direction}_delay {delay} -clock {clock} [get_port \"{name}\"]".format(
                delay=delay.delay.value_in_units(self.get_time_unit().value_prefix + self.get_time_unit().unit),
                clock=delay.clock,
                direction=delay.direction,
                name=delay.name
            ))

        # Custom sdc constraints that are verbatim appended
        custom_sdc_constraints = self.get_setting("vlsi.inputs.custom_sdc_constraints")  # type: Union[List[str], str]
        if isinstance(custom_sdc_constraints, str):
            custom_sdc_constraints = [custom_sdc_constraints]
        for custom in custom_sdc_constraints:
            output.append(str(custom))

        return "\n".join(output)

    @property
    @abstractmethod
    def post_synth_sdc(self) -> Optional[str]:
        """
        Get the (optional) input post-synthesis SDC constraint file.

        :return: The (optional) input post-synthesis SDC constraint file.
        """
        pass

class TCLTool(HammerTool):
    """Mix-in trait for tools which consume a flat TCL file as input"""

    @property
    def output(self) -> List[str]:
        """
        Buffered output to be put in <name>.tcl
        """
        return self.attr_getter("_output", [])

    # Python doesn't have Scala's nice currying syntax (e.g. val newfunc = func(_, fixed_arg))
    def verbose_append(self, cmd: str, clean: bool = False) -> None:
        self.verbose_tcl_append(cmd, self.output, clean)

    def append(self, cmd: str, clean: bool = False) -> None:
        self.tcl_append(cmd, self.output, clean)

    # append a multiline string with proper formatting (makes plugins easier to read)
    def block_append(self, cmds: str, verbose: bool = True) -> bool:
        verbose_commands = []
        commands = cmds.split('\n')
        # remove first line if it's empty because it messes up indentation
        if len(commands[0].strip()) == 0:
            commands = commands[1:]
        prev_line = ""
        for line in commands:
            # add "verbose" statement (echo TCL command to terminal)
            #   if line isn't (1) empty, (2) part of a multiline command, or (3) a comment
            # we can't just use verbose_append because it blindly echoes all commands
            empty = not any(c.isalpha() for c in line)
            if verbose and not (empty or '\\' in prev_line or ('#' in line)):
                indent_len = len(line) - len(line.lstrip())
                indent = ' ' * indent_len
                puts_cmd = line.strip("\\ ") # remove leading/trailing characters
                escape_str = '"[]'  # NOTE: there may be more characters that need to be escaped!
                for c in escape_str:  # escape characters in commands for puts command
                    puts_cmd = puts_cmd.replace(c, '\\'+c)
                if puts_cmd != "":
                    verbose_commands.append(f'{indent}puts "(hammer) {puts_cmd}"')
            verbose_commands.append(line)
            prev_line = line
        self.append('\n'.join(verbose_commands), clean=True)
        self.append("")
        return True

class SynopsysTool(HasSDCSupport, TCLTool, HammerTool):
    """Mix-in trait with functions useful for Synopsys-based tools."""

    ## FIXME: not used by any Synopsys tool
    @property
    def post_synth_sdc(self) -> Optional[str]:
        return None

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        result = dict(super().env_vars)
        result.update({
            "SNPSLMD_LICENSE_FILE": self.get_setting("synopsys.SNPSLMD_LICENSE_FILE"),
            # TODO: this is actually a Mentor Graphics licence, not sure why the old dc scripts depend on it.
            "MGLS_LICENSE_FILE": self.get_setting("synopsys.MGLS_LICENSE_FILE")
        })
        return result

    def version_number(self, version: str) -> int:
        """
        Assumes versions look like NAME-YYYY.MM-SPMINOR.
        Assumes less than 100 minor versions.
        """
        date = "-".join(version.split("-")[1:])  # type: str
        year = int(date.split(".")[0])  # type: int
        month = int(date.split(".")[1][:2])  # type: int
        minor_version = 0  # type: int
        if "-" in date:
            minor_version = int(date.split("-")[1][2:])
        return (year * 100 + month) * 100 + minor_version

    @property
    def header(self) -> str:
        """
        Header for all generated Tcl scripts
        """
        header_text = f"""
        # ---------------------------------------------------------------------------------
        # Portions Copyright ©{datetime.date.today().year} Synopsys, Inc. All rights reserved. Portions of
        # these TCL scripts are proprietary to and owned by Synopsys, Inc. and may only be
        # used for internal use by educational institutions (including United States
        # government labs, research institutes and federally funded research and
        # development centers) on Synopsys tools for non-profit research, development,
        # instruction, and other non-commercial uses or as otherwise specifically set forth
        # by written agreement with Synopsys. All other use, reproduction, modification, or
        # distribution of these TCL scripts is strictly prohibited.
        # ---------------------------------------------------------------------------------
        """
        return inspect.cleandoc(header_text)

    def get_synopsys_rm_tarball(self, product: str, settings_key: str = "") -> str:
        """Locate reference methodology tarball.

        :param product: Either "DC" or "ICC"
        :param settings_key: Key to retrieve the version for the product. Leave blank for DC and ICC.
        """
        key = self.tool_config_prefix() + "." + "version" # type: str

        synopsys_rm_tarball = os.path.join(self.get_setting("synopsys.rm_dir"), "%s-RM_%s.tar" % (product, self.get_setting(key)))
        if not os.path.exists(synopsys_rm_tarball):
            # TODO: convert these to logger calls
            raise FileNotFoundError("Expected reference methodology tarball not found at %s. Use the Synopsys RM generator <https://solvnet.synopsys.com/rmgen> to generate a DC reference methodology. If these tarballs have been pre-downloaded, you can set synopsys.rm_dir instead of generating them yourself." % (synopsys_rm_tarball))
        else:
            return synopsys_rm_tarball

class MentorTool(HammerTool):
    """ Mix-in trait with functions useful for Mentor-Graphics-based tools. """

    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        # Use the base extra_env_variables and ensure that our custom variables are on top.
        list_of_vars = self.get_setting("mentor.extra_env_vars")  # type: List[Dict[str, Any]]
        assert isinstance(list_of_vars, list)

        mentor_vars = {
            "MGLS_LICENSE_FILE": self.get_setting("mentor.MGLS_LICENSE_FILE"),
            "MENTOR_HOME": self.get_setting("mentor.mentor_home")
        }

        return reduce(add_dicts, [dict(super().env_vars)] + list_of_vars + [mentor_vars], {})

    def version_number(self, version: str) -> int:
        """
        Assumes versions look like NAME-YYYY.MM-SPMINOR.
        Assumes less than 100 minor versions.
        """
        # TODO(johnwright)
        # We currently do not support Calibre versions
        return 0

class MentorCalibreTool(MentorTool):
    """ Mix-in trait for Mentor's Calibre tool suite. """
    @property
    def env_vars(self) -> Dict[str, str]:
        """
        Get the list of environment variables required for this tool.
        Note to subclasses: remember to include variables from super().env_vars!
        """
        return super().env_vars


def load_tool(tool_module: str) -> HammerTool:
    """
    Load the given tool.
    See the hammer-vlsi README for how it works.

    :param tool_module: The tool module e.g. "hammer.synthesis.yosys"
    :return: HammerTool of the given tool
    """
    mod = importlib.import_module(tool_module)
    tool_class = getattr(mod, "tool")
    tool: HammerTool = tool_class()
    tool.package = tool_module
    return tool


class HammerPCBDeliverableTool(HammerTool):
    @abstractmethod
    def fill_outputs(self) -> bool:
        pass

    @property
    def naming_scheme(self) -> BumpsPinNamingScheme:
        """
        Get the desired bump naming scheme.
        """
        name = self.get_setting("vlsi.inputs.bumps_pin_naming_scheme")
        if name is None:
            raise ValueError("Must provide a vlsi.inputs.bumps_pin_naming_scheme if generating PCB deliverables.")
        else:
            return BumpsPinNamingScheme.from_str(str(name))

    ### Generated interface HammerPCBDeliverableTool ###
    ### DO NOT MODIFY THIS CODE, EDIT generate_properties.py INSTEAD ###
    ### Inputs ###

    ### Outputs ###

    @property
    def output_footprints(self) -> List[str]:
        """
        Get the list of the PCB footprint files for the project.

        :return: The list of the PCB footprint files for the project.
        """
        try:
            return self.attr_getter("_output_footprints", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of the PCB footprint files for the project yet")

    @output_footprints.setter
    def output_footprints(self, value: List[str]) -> None:
        """Set the list of the PCB footprint files for the project."""
        if not (isinstance(value, List)):
            raise TypeError("output_footprints must be a List[str]")
        self.attr_setter("_output_footprints", value)


    @property
    def output_schematic_symbols(self) -> List[str]:
        """
        Get the list of the PCB schematic symbol files for the project.

        :return: The list of the PCB schematic symbol files for the project.
        """
        try:
            return self.attr_getter("_output_schematic_symbols", None)
        except AttributeError:
            raise ValueError("Nothing set for the list of the PCB schematic symbol files for the project yet")

    @output_schematic_symbols.setter
    def output_schematic_symbols(self, value: List[str]) -> None:
        """Set the list of the PCB schematic symbol files for the project."""
        if not (isinstance(value, List)):
            raise TypeError("output_schematic_symbols must be a List[str]")
        self.attr_setter("_output_schematic_symbols", value)

    ### END Generated interface HammerPCBDeliverableTool ###
