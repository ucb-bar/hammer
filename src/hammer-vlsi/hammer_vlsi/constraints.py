#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  constraints.py
#  Data structures for various types of Hammer IR constraints.
#
#  See LICENSE for licence details.

# pylint: disable=bad-continuation
import operator
from enum import Enum
from functools import reduce
from typing import Dict, NamedTuple, Optional, List, Any, Tuple, Union, cast

from hammer_utils import reverse_dict, get_or_else
from .units import TimeValue, VoltageValue, TemperatureValue

from decimal import Decimal

__all__ = ['ILMStruct', 'SRAMParameters', 'Supply', 'PinAssignment',
           'BumpAssignment', 'BumpsDefinition', 'ClockPort',
           'OutputLoadConstraint', 'DelayConstraint', 'ObstructionType',
           'PlacementConstraintType', 'Margins', 'PlacementConstraint',
           'MMMCCornerType', 'MMMCCorner', 'PinAssignmentError', 'PinAssignmentPreplacedError',
           'PinAssignmentSemiAutoError']


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


class PinAssignmentError(ValueError):
    """Exception raised from parsing an invalid PinAssignment object."""


class PinAssignmentSemiAutoError(PinAssignmentError):
    """Exception raised from parsing a PinAssignment that requires semi-auto features without explicitly enabing
    them."""


class PinAssignmentPreplacedError(PinAssignmentError):
    """Exception raised from parsing a preplaced pin with extraneous information."""

    def __init__(self, pin: "PinAssignment") -> None:
        self.pin = pin

    def __str__(self) -> str:
        return "Pins {p} assigned as a preplaced pin with layers or side. Assuming pins are preplaced pins and ignoring layers and side.".format(
            p=self.pin.pins)


class PinAssignment(NamedTuple('PinAssignment', [
    ('pins', str),
    ('side', Optional[str]),
    ('layers', Optional[List[str]]),
    ('preplaced', bool),
    ('location', Optional[Tuple[float, float]]),
    ('width', Optional[float]),
    ('depth', Optional[float])
])):
    __slots__ = ()

    def __new__(cls, pins: str, side: Optional[str] = None, layers: Optional[List[str]] = None,
                preplaced: Optional[bool] = None,
                location: Optional[Tuple[float, float]] = None, width: Optional[float] = None,
                depth: Optional[float] = None) -> "PinAssignment":
        return super().__new__(cls, pins, side, layers, get_or_else(preplaced, False), location, width, depth)

    @staticmethod
    def create(pins: str, side: Optional[str] = None, layers: Optional[List[str]] = None,
                preplaced: Optional[bool] = None,
                location: Optional[Tuple[float, float]] = None, width: Optional[float] = None,
                depth: Optional[float] = None) -> "PinAssignment":
        """
        Static method that works around the fact that mypy gets very confused at
        the custom constructor above that defines default arguments.
        """
        return PinAssignment(pins, side, layers, get_or_else(preplaced, False), location, width, depth)

    @staticmethod
    def from_dict(raw_assign: Dict[str, Any], semi_auto: bool = True) -> "PinAssignment":
        pins = str(raw_assign["pins"])  # type: str

        side = None  # type: Optional[str]
        if "side" in raw_assign:
            raw_side = raw_assign["side"]  # type: str
            assert isinstance(raw_side, str), "side must be a str"

            if raw_side in ("top", "bottom", "right", "left", "internal"):
                side = raw_side
                if side == "internal" and not semi_auto:
                    raise PinAssignmentSemiAutoError("side set to internal")
            else:
                raise PinAssignmentError(
                    "Pins {p} have invalid side {s}. Assuming pins will be handled by CAD tool.".format(p=pins,
                                                                                                        s=raw_side))

        preplaced = raw_assign.get("preplaced", False)  # type: bool
        assert isinstance(preplaced, bool), "preplaced must be a bool"

        location = None  # type: Optional[Tuple[float, float]]
        if "location" in raw_assign:
            location_raw = raw_assign["location"]  # type: Union[List[float], Tuple[float, float]]
            assert len(location_raw) == 2, "location must be a Optional[Tuple[float, float]]"
            assert isinstance(location_raw[0], float), "location must be a Optional[Tuple[float, float]]"
            assert isinstance(location_raw[1], float), "location must be a Optional[Tuple[float, float]]"
            location = (location_raw[0], location_raw[1])
        if not semi_auto and location is not None:
            raise PinAssignmentSemiAutoError("location requires semi_auto")

        width = raw_assign.get("width", None)  # type: Optional[float]
        if width is not None:
            assert isinstance(width, float), "width must be a float"
        if not semi_auto and width is not None:
            raise PinAssignmentSemiAutoError("width requires semi_auto")

        depth = raw_assign.get("depth", None)  # type: Optional[float]
        if depth is not None:
            assert isinstance(depth, float), "depth must be a float"
        if not semi_auto and depth is not None:
            raise PinAssignmentSemiAutoError("depth requires semi_auto")

        layers = None  # type: Optional[List[str]]
        if "layers" in raw_assign:
            raw_layers = raw_assign["layers"]  # type: List[str]
            assert isinstance(raw_layers, list), "layers must be a List[str]"
            for layer in "layers":
                assert isinstance(layer, str), "layers must be a List[str]"
            layers = raw_layers

        if preplaced:
            should_be_none = reduce(operator.and_, map(lambda x: x is None, [side, location, width, depth]))
            if len(get_or_else(layers, cast(List[str], []))) > 0 or not should_be_none:
                raise PinAssignmentPreplacedError(
                    PinAssignment(pins=pins, side=None, layers=[], preplaced=preplaced, location=None, width=None,
                                  depth=None))
        else:
            if len(get_or_else(layers, cast(List[str], []))) == 0 or side is None:
                raise PinAssignmentError(
                    "Pins {p} assigned without layers or side. Assuming pins will be handled by CAD tool.".format(
                        p=pins))
        return PinAssignment(
            pins=pins,
            side=side,
            layers=layers,
            preplaced=preplaced,
            location=location,
            width=width,
            depth=depth
        )

    def to_dict(self) -> dict:
        base = {
            "pins": self.pins,
            "preplaced": self.preplaced
        }  # type: Dict[str, Any]
        if self.side is not None:
            base['side'] = self.side
        if self.layers is not None:
            base['layers'] = self.layers
        if self.location is not None:
            base['location'] = self.location
        if self.width is not None:
            base['width'] = self.width
        if self.depth is not None:
            base['depth'] = self.depth
        return base


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
    ('pitch', float),
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
    ('left', float),
    ('bottom', float),
    ('right', float),
    ('top', float)
])


class PlacementConstraint(NamedTuple('PlacementConstraint', [
    ('path', str),
    ('type', PlacementConstraintType),
    ('x', float),
    ('y', float),
    ('width', float),
    ('height', float),
    ('orientation', Optional[str]),
    ('margins', Optional[Margins]),
    ('top_layer', Optional[str]),
    ('layers', Optional[List[str]]),
    ('obs_types', Optional[List[ObstructionType]])
])):
    __slots__ = ()

    @staticmethod
    def from_dict(constraint: dict) -> "PlacementConstraint":
        constraint_type = PlacementConstraintType.from_str(
            str(constraint["type"]))
        margins = None  # type: Optional[Margins]
        orientation = None  # type: Optional[str]
        top_layer = None  # type: Optional[str]
        layers = None  # type: Optional[List[str]]
        obs_types = None  # type: Optional[List[ObstructionType]]
        if constraint_type == PlacementConstraintType.TopLevel:
            margins_dict = constraint["margins"]
            margins = Margins(
                left=float(margins_dict["left"]),
                bottom=float(margins_dict["bottom"]),
                right=float(margins_dict["right"]),
                top=float(margins_dict["top"])
            )
        if "orientation" in constraint:
            orientation = str(constraint["orientation"])
        if "top_layer" in constraint:
            top_layer = str(constraint["top_layer"])
        if "layers" in constraint:
            layers = []
            for layer in constraint["layers"]:
                layers.append(str(layer))
        if "obs_types" in constraint:
            obs_types = []
            types = constraint["obs_types"]
            for obs_type in types:
                obs_types.append(ObstructionType.from_str(str(obs_type)))
        return PlacementConstraint(
            path=str(constraint["path"]),
            type=constraint_type,
            x=float(constraint["x"]),
            y=float(constraint["y"]),
            width=float(constraint["width"]),
            height=float(constraint["height"]),
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
