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

from hammer_utils import reverse_dict, add_dicts
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
    def _get_master(constraint_type: PlacementConstraintType, constraint: dict) -> Optional[str]:
        """
        A helper method to retrieve the master key from a constraint dict. This is broken out into its own function because it's
        used in multiple methods. The master key is mandatory for Hierarchical constraint, optional for HardMacro constraints,
        and disallowed otherwise.

        :param constraint_type: A PlacementConstraintType object describing the type of constraint
        :param constraint: A dict that may or may not contain a master key
        :return: The value pointed to by master or None, if allowed by the constraint type
        """
        # This field is mandatory for Hierarchical constraints
        # This field is optional for HardMacro constraints
        # This field is disallowed otherwise
        master = None  # type: Optional[str]
        if "master" in constraint:
            if constraint_type not in [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro]:
                raise ValueError("Constraints other than Hierarchical and HardMacro must not contain master: {}".format(constraint))
            master = str(constraint["master"])
        else:
            if constraint_type == PlacementConstraintType.Hierarchical:
                raise ValueError("Hierarchical constraint must contain master: {}".format(constraint))
        return master

    @staticmethod
    def from_masters_and_dict(masters: List[MacroSize], constraint: dict) -> "PlacementConstraint":
        """
        Create a PlacementConstraint tuple from a constraint dict and a list of masters. This method differs from from_dict by
        allowing the width and height to be auto-filled from a list of masters for the Hierarchical and HardMacro constraint types.

        :param masters: A list of MacroSize tuples containing cell macro definitions
        :param constraint: A dict containing information to be parsed into a PlacementConstraint tuple
        :return: A PlacementConstraint tuple
        """

        constraint_type = PlacementConstraintType.from_str(str(constraint["type"]))
        master = PlacementConstraint._get_master(constraint_type, constraint)

        checked_types = [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro]
        width_check = None  # type: Optional[Decimal]
        height_check = None  # type: Optional[Decimal]
        # Get the "Master" values
        if constraint_type == PlacementConstraintType.Hierarchical:
            # This should be true given the code above, but sanity check anyway
            assert master is not None
            matches = list(filter(lambda x: x.name == master, masters))
            if len(matches) > 0:
                width_check = matches[0].width
                height_check = matches[0].height
            else:
                raise ValueError("Could not find a master for hierarchical cell {} in masters list.".format(master))
        elif constraint_type == PlacementConstraintType.HardMacro:
            # TODO(johnwright) for now we're allowing HardMacros to be flexible- checks are performed if the data exists, but otherwise
            # we will "trust" the provided width and height. They aren't actually used, so this is not super important at the moment.
            # ucb-bar/hammer#414
            if master is not None:
                matches = list(filter(lambda x: x.name == master, masters))
                if len(matches) > 0:
                    width_check = matches[0].width
                    height_check = matches[0].height
        else:
            assert constraint_type not in checked_types, "Should not get here; update checked_types."

        width = None
        height = None

        if "width" in constraint:
            width = Decimal(str(constraint["width"]))
        else:
            width = width_check

        if "height" in constraint:
            height = Decimal(str(constraint["height"]))
        else:
            height = height_check

        # Perform the check
        if constraint_type in checked_types:
            if height != height_check and height_check is not None:
                raise ValueError("Optional height value {} must equal the master value {} for constraint: {}".format(height, height_check, constraint))
            if width != width_check and width_check is not None:
                raise ValueError("Optional width value {} must equal the master value {} for constraint: {}".format(width, width_check, constraint))

        updated_constraint = constraint
        if width is not None:
            updated_constraint = add_dicts(constraint, {'width': width})
        if height is not None:
            updated_constraint = add_dicts(constraint, {'height': height})

        return PlacementConstraint.from_dict(updated_constraint)

    @staticmethod
    def from_dict(constraint: dict) -> "PlacementConstraint":
        constraint_type = PlacementConstraintType.from_str(str(constraint["type"]))

        ### Margins ###
        # This field is mandatory in TopLevel constraints
        # This field is disallowed otherwise
        margins = None  # type: Optional[Margins]
        if "margins" in constraint:
            if constraint_type != PlacementConstraintType.TopLevel:
                raise ValueError("Non-TopLevel constraint must not contain margins: {}".format(constraint))
            margins_dict = constraint["margins"]
            margins = Margins(
                left=Decimal(str(margins_dict["left"])),
                bottom=Decimal(str(margins_dict["bottom"])),
                right=Decimal(str(margins_dict["right"])),
                top=Decimal(str(margins_dict["top"]))
            )
        else:
            if constraint_type == PlacementConstraintType.TopLevel:
                raise ValueError("TopLevel constraint must contain margins: {}".format(constraint))

        ### Orientation ###
        # This field is disallowed in TopLevel constraints
        # This field is optional otherwise
        orientation = None  # type: Optional[str]
        if "orientation" in constraint:
            if constraint_type == PlacementConstraintType.TopLevel:
                raise ValueError("Non-TopLevel constraint must not contain orientation: {}".format(constraint))
            orientation = str(constraint["orientation"])

        ### Top layer ###
        # This field is optional in Hierarchical and HardMacro constraints
        # This field is disallowed otherwise
        top_layer = None  # type: Optional[str]
        if "top_layer" in constraint:
            if constraint_type not in [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro]:
                raise ValueError("Constraints other than Hierarchical and HardMacro must not contain top_layer: {}".format(constraint))
            top_layer = str(constraint["top_layer"])

        ### Layers ###
        # This field is optional in Obstruction constraints
        # This field is disallowed otherwise
        layers = None  # type: Optional[List[str]]
        if "layers" in constraint:
            if constraint_type != PlacementConstraintType.Obstruction:
                raise ValueError("Non-Obstruction constraint must not contain layers: {}".format(constraint))
            layers = []
            for layer in constraint["layers"]:
                layers.append(str(layer))

        ### Obstruction types ###
        # This field is mandatory in Obstruction constraints
        # This field is disallowed otherwise
        obs_types = None  # type: Optional[List[ObstructionType]]
        if "obs_types" in constraint:
            if constraint_type != PlacementConstraintType.Obstruction:
                raise ValueError("Non-Obstruction constraint must not contain obs_types: {}".format(constraint))
            obs_types = []
            types = constraint["obs_types"]
            for obs_type in types:
                obs_types.append(ObstructionType.from_str(str(obs_type)))
        else:
            if constraint_type == PlacementConstraintType.Obstruction:
                raise ValueError("Obstruction constraint must contain obs_types: {}".format(constraint))

        ### Master ###
        master = PlacementConstraint._get_master(constraint_type, constraint)

        ### Width & height ###
        # These fields are mandatory for Hierarchical, Dummy, Placement, TopLevel, and Obstruction constraints
        # These fields are optional for HardMacro constraints
        # TODO(ucb-bar/hammer#414) make them mandatory for HardMacro once there's a more robust way of automatically getting that data into hammer
        # This is not None because we don't want to make width optional for the reason above
        width = Decimal(0)
        if "width" in constraint:
            width = Decimal(constraint["width"])
        else:
            # TODO(ucb-bar/hammer#414) remove this allowance and just raise the error
            if constraint_type != PlacementConstraintType.HardMacro:
                raise ValueError("Non-HardMacro constraint must contain a width: {}".format(constraint))

        # This is not None because we don't want to make height optional for the reason above
        height = Decimal(0)
        if "height" in constraint:
            height = Decimal(constraint["height"])
        else:
            # TODO(ucb-bar/hammer#414) remove this allowance and just raise the error
            if constraint_type != PlacementConstraintType.HardMacro:
                raise ValueError("Non-HardMacro constraint must contain a height: {}".format(constraint))

        ### X & Y coordinates ###
        # These fields are mandatory in all constraints
        if "x" not in constraint:
            raise ValueError("Constraint must contain an x coordinate: {}".format(constraint))
        if "y" not in constraint:
            raise ValueError("Constraint must contain an y coordinate: {}".format(constraint))
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
