#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  constraints.py
#  Data structures for various types of Hammer IR constraints.
#
#  See LICENSE for licence details.

# pylint: disable=bad-continuation

from enum import Enum
from typing import Dict, NamedTuple, Optional, List, Any

from hammer_utils import reverse_dict
from hammer_tech import MacroSize
from .units import TimeValue, VoltageValue, TemperatureValue

from decimal import Decimal

__all__ = ['ILMStruct', 'SRAMParameters', 'Supply', 'PinAssignment',
           'BumpAssignment', 'BumpsDefinition', 'ClockPort',
           'OutputLoadConstraint', 'DelayConstraint', 'ObstructionType',
           'PlacementConstraintType', 'Margins', 'PlacementConstraint',
           'MMMCCornerType', 'MMMCCorner']


# Struct that holds various paths related to ILMs.
class ILMStruct(NamedTuple('ILMStruct', [
    ('dir', str),
    ('data_dir', str),
    ('module', str),
    ('lef', str),
    ('gds', str),
    ('netlist', str)
])):
    __slots__ = ()

    def to_setting(self) -> dict:
        return {
            "dir": self.dir,
            "data_dir": self.data_dir,
            "module": self.module,
            "lef": self.lef,
            "gds": self.gds,
            "netlist": self.netlist
        }

    @staticmethod
    def from_setting(ilm: dict) -> "ILMStruct":
        return ILMStruct(
            dir=str(ilm["dir"]),
            data_dir=str(ilm["data_dir"]),
            module=str(ilm["module"]),
            lef=str(ilm["lef"]),
            gds=str(ilm["gds"]),
            netlist=str(ilm["netlist"])
        )

# Transliterated-ish from SRAMGroup in MDF
# TODO: Convert this is to use the HammerIR library once #330 is resolved
class SRAMParameters(NamedTuple('SRAMParameters', [
    ('name', str),
    ('family', str),
    ('depth', int),
    ('width', int),
    ('mask', bool),
    ('vt', str),
    ('mux', int)
    ])):

    __slots__ = ()

    @staticmethod
    def from_setting(d: dict) -> "SRAMParameters":
        # pylint: disable=missing-docstring
        return SRAMParameters(
            name=str(d["name"]),
            family=str(d["family"]),
            depth=int(d["depth"]),
            width=int(d["width"]),
            mask=bool(d["mask"]),
            vt=str(d["vt"]),
            mux=int(d["mux"])
        )

Supply = NamedTuple('Supply', [
    ('name', str),
    ('pin', Optional[str]),
    ('tie', Optional[str]),
    ('weight', Optional[int])
])

PinAssignment = NamedTuple('PinAssignment', [
    ('pins', str),
    ('side', Optional[str]),
    ('layers', Optional[List[str]]),
    ('preplaced', Optional[bool])
])

BumpAssignment = NamedTuple('BumpAssignment', [
    ('name', Optional[str]),
    ('no_connect', Optional[bool]),
    ('x', Decimal),
    ('y', Decimal),
    ('custom_cell', Optional[str])
])

BumpsDefinition = NamedTuple('BumpsDefinition', [
    ('x', int),
    ('y', int),
    ('pitch', Decimal),
    ('cell', str),
    ('assignments', List[BumpAssignment])
])

ClockPort = NamedTuple('ClockPort', [
    ('name', str),
    ('period', TimeValue),
    ('path', Optional[str]),
    ('uncertainty', Optional[TimeValue]),
    ('generated', Optional[bool]),
    ('source_path', Optional[str]),
    ('divisor', Optional[int])
])


OutputLoadConstraint = NamedTuple('OutputLoadConstraint', [
    ('name', str),
    ('load', float)
])


class DelayConstraint(NamedTuple('DelayConstraint', [
    ('name', str),
    ('clock', str),
    ('direction', str),
    ('delay', TimeValue)
])):
    __slots__ = ()

    def __new__(cls, name: str, clock: str, direction: str, delay: TimeValue) -> "DelayConstraint":
        if direction not in ("input", "output"):
            raise ValueError("Invalid direction {direction}".format(direction=direction))
        return super().__new__(cls, name, clock, direction, delay)

    @staticmethod
    def from_dict(delay_src: Dict[str, Any]) -> "DelayConstraint":
        direction = str(delay_src["direction"])
        if direction not in ("input", "output"):
            raise ValueError("Invalid direction {direction}".format(direction=direction))
        return DelayConstraint(
            name=str(delay_src["name"]),
            clock=str(delay_src["clock"]),
            direction=direction,
            delay=TimeValue(delay_src["delay"])
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "clock": self.clock,
            "direction": self.direction,
            "delay": self.delay.str_value_in_units("ns", round_zeroes=False)
        }


class ObstructionType(Enum):
    Place = 1
    Route = 2
    Power = 3

    @classmethod
    def __mapping(cls) -> Dict[str, "ObstructionType"]:
        return {
            "place": ObstructionType.Place,
            "route": ObstructionType.Route,
            "power": ObstructionType.Power
        }

    @staticmethod
    def from_str(input_str: str) -> "ObstructionType":
        try:
            return ObstructionType.__mapping()[input_str]
        except KeyError:
            raise ValueError("Invalid obstruction type: " + str(input_str))

    def __str__(self) -> str:
        return reverse_dict(ObstructionType.__mapping())[self]


class PlacementConstraintType(Enum):
    Dummy = 1
    Placement = 2
    TopLevel = 3
    HardMacro = 4
    Hierarchical = 5
    Obstruction = 6

    @classmethod
    def __mapping(cls) -> Dict[str, "PlacementConstraintType"]:
        return {
            "dummy": PlacementConstraintType.Dummy,
            "placement": PlacementConstraintType.Placement,
            "toplevel": PlacementConstraintType.TopLevel,
            "hardmacro": PlacementConstraintType.HardMacro,
            "hierarchical": PlacementConstraintType.Hierarchical,
            "obstruction": PlacementConstraintType.Obstruction
        }

    @staticmethod
    def from_str(input_str: str) -> "PlacementConstraintType":
        try:
            return PlacementConstraintType.__mapping()[input_str]
        except KeyError:
            raise ValueError("Invalid placement constraint type: " + str(input_str))

    def __str__(self) -> str:
        return reverse_dict(PlacementConstraintType.__mapping())[self]


# For the top-level chip size constraint, set the margin from core area to left/bottom/right/top.
Margins = NamedTuple('Margins', [
    ('left', Decimal),
    ('bottom', Decimal),
    ('right', Decimal),
    ('top', Decimal)
])


class PlacementConstraint(NamedTuple('PlacementConstraint', [
    ('path', str),
    ('type', PlacementConstraintType),
    ('x', Decimal),
    ('y', Decimal),
    ('width', Decimal),
    ('height', Decimal),
    ('master', Optional[str]),
    ('orientation', Optional[str]),
    ('margins', Optional[Margins]),
    ('top_layer', Optional[str]),
    ('layers', Optional[List[str]]),
    ('obs_types', Optional[List[ObstructionType]])
])):
    __slots__ = ()

    @staticmethod
    def from_dict(masters: List[MacroSize], constraint: dict) -> "PlacementConstraint":
        constraint_type = PlacementConstraintType.from_str(
            str(constraint["type"]))

        ### Margins ###
        # This field is mandatory in TopLevel constraints
        # This field is disallowed otherwise
        margins = None  # type: Optional[Margins]
        if "margins" in constraint:
            assert constraint_type == PlacementConstraintType.TopLevel, "Non-TopLevel constraint must not contain margins: {}".format(constraint)
            margins_dict = constraint["margins"]
            margins = Margins(
                left=Decimal(str(margins_dict["left"])),
                bottom=Decimal(str(margins_dict["bottom"])),
                right=Decimal(str(margins_dict["right"])),
                top=Decimal(str(margins_dict["top"]))
            )
        else:
            assert constraint_type != PlacementConstraintType.TopLevel, "TopLevel constraint must contain margins: {}".format(constraint)

        ### Orientation ###
        # This field is disallowed in TopLevel constraints
        # This field is optional otherwise
        orientation = None  # type: Optional[str]
        if "orientation" in constraint:
            assert constraint_type != PlacementConstraintType.TopLevel, "Non-TopLevel constraint must not contain orientation: {}".format(constraint)
            orientation = str(constraint["orientation"])

        ### Top layer ###
        # This field is optional in HardMacro constraints
        # This field is disallowed otherwise
        top_layer = None  # type: Optional[str]
        if "top_layer" in constraint:
            assert constraint_type == PlacementConstraintType.HardMacro, "Non-HardMacro constraint must not contain top_layer: {}".format(constraint)
            top_layer = str(constraint["top_layer"])

        ### Layers ###
        # This field is optional in Obstruction constraints
        # This field is disallowed otherwise
        layers = None  # type: Optional[List[str]]
        if "layers" in constraint:
            assert constraint_type == PlacementConstraintType.Obstruction, "Non-Obstruction constraint must not contain layers: {}".format(constraint)
            layers = []
            for layer in constraint["layers"]:
                layers.append(str(layer))

        ### Obstruction types ###
        # This field is mandatory in Obstruction constraints
        # This field is disallowed otherwise
        obs_types = None  # type: Optional[List[ObstructionType]]
        if "obs_types" in constraint:
            assert constraint_type == PlacementConstraintType.Obstruction, "Non-Obstruction constraint must not contain obs_types: {}".format(constraint)
            obs_types = []
            types = constraint["obs_types"]
            for obs_type in types:
                obs_types.append(ObstructionType.from_str(str(obs_type)))
        else:
            assert constraint_type != PlacementConstraintType.Obstruction, "Obstruction constraint must contain obs_types: {}".format(constraint)

        ### Master ###
        # This field is mandatory for Hierarchical constraints
        # This field is optional for HardMacro constraints
        # This field is disallowed otherwise
        master = None  # type: Optional[str]
        if "master" in constraint:
            assert constraint_type in [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro], "Constraints other than Hierarchical and HardMacro must not contain master: {}".format(constraint)
            master = constraint["master"]
        else:
            assert constraint_type != PlacementConstraintType.Hierarchical, "Hierarchical constraint must contain master: {}".format(constraint)

        ### Width & height ###
        # These fields are mandatory for Dummy, Placement, TopLevel, and Obstruction constraints
        # These fields are optional for HardMacro and Hierarchical constraints
        #   If omitted, they are copied from the master definition (HardMacro) or hierarchical top-level width and height (Hierarchical).
        #   If present, they must match the values that would otherwise be automatically input.

        # TODO(johnwright) eventually support HardMacro LEF parsing. I think this would look like including a list of cells in the library definition,
        #   which would allow us to reverse lookup what LEF to parse for the individual cells that we want to check (and assert if it's wrong).
        #checked_types = [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro]
        checked_types = [PlacementConstraintType.Hierarchical]
        width_check = Decimal(-1)
        height_check = Decimal(-1)
        # Get the "Master" values
        if constraint_type == PlacementConstraintType.Hierarchical:
            # This should be true given the code above, but sanity check anyway
            assert master is not None
            matches = list(filter(lambda x: x.name == master, masters))
            if len(matches) > 0:
                width_check = matches[0].width
                height_check = matches[1].height
            else:
                raise ValueError("Could not find a master for hierarchical cell {} in masters list.".format(master))
        elif constraint_type == PlacementConstraintType.HardMacro:
            # For now we're going to punt on this (see TODO above)
            pass
        else:
            assert constraint_type not in checked_types, "Should not get here; update checked_types."

        width = Decimal(-1)
        height = Decimal(-1)

        if "width" in constraint:
            width = Decimal(str(constraint["width"]))
        else:
            assert constraint_type in checked_types, "Constraints other than Hierarchical and HardMacro must contain width: {}".format(constraint)
            width = width_check

        if "height" in constraint:
            height = Decimal(str(constraint["height"]))
        else:
            assert constraint_type in checked_types, "Constraints other than Hierarchical and HardMacro must contain height: {}".format(constraint)
            height = height_check

        # Perform the check
        if constraint_type in checked_types:
            assert height == height_check, "Optional height value {} for constraint must equal the master value: {} for constraint {}".format(height, height_check, constraint)
            assert width == width_check, "Optional width value {} for constraint must equal the master value: {} for constraint {}".format(width, width_check, constraint)

        ### X & Y coordinates ###
        # These fields are mandatory in all constraints
        assert "x" in constraint, "Constraint must contain an x coordinate: {}".format(constraint)
        x = Decimal(str(constraint["x"]))
        y = Decimal(str(constraint["y"]))

        return PlacementConstraint(
            path=str(constraint["path"]),
            type=constraint_type,
            x=x,
            y=y,
            width=width,
            height=height,
            master=master,
            orientation=orientation,
            margins=margins,
            top_layer=top_layer,
            layers=layers,
            obs_types=obs_types
        )

    def to_dict(self) -> dict:
        output = {
            "path": self.path,
            "type": str(self.type),
            "x": str(self.x),
            "y": str(self.y),
            "width": str(self.width),
            "height": str(self.height)
        }  # type: Dict[str, Any]
        if self.orientation is not None:
            output.update({"orientation": self.orientation})
        if self.margins is not None:
            output.update({"margins": {
                "left": self.margins.left,
                "bottom": self.margins.bottom,
                "right": self.margins.right,
                "top": self.margins.top
            }})
        if self.top_layer is not None:
            output.update({"top_layer": self.top_layer})
        if self.layers is not None:
            output.update({"layers": self.layers})
        if self.obs_types is not None:
            output.update({"obs_types": list(map(str, self.obs_types))})
        return output


class MMMCCornerType(Enum):
    Setup = 1
    Hold = 2
    Extra = 3

    @staticmethod
    def from_string(input_str: str) -> "MMMCCornerType":
        if input_str == "setup":  # pylint: disable=no-else-return
            return MMMCCornerType.Setup
        elif input_str == "hold":
            return MMMCCornerType.Hold
        elif input_str == "extra":
            return MMMCCornerType.Extra
        else:
            raise ValueError("Invalid MMMC corner type '{}'".format(input_str))


MMMCCorner = NamedTuple('MMMCCorner', [
    ('name', str),
    ('type', MMMCCornerType),
    ('voltage', VoltageValue),
    ('temp', TemperatureValue),
])
