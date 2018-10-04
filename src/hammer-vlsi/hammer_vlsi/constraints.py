#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  constraints.py
#  Data structures for various types of Hammer IR constraints.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from enum import Enum
from typing import Dict, NamedTuple, Optional, List, Any

from hammer_utils import reverse_dict
from .units import TimeValue, VoltageValue, TemperatureValue

__all__ = ['ILMStruct', 'ClockPort', 'OutputLoadConstraint', 'ObstructionType', 'PlacementConstraintType', 'Margins',
           'PlacementConstraint', 'MMMCCornerType', 'MMMCCorner']


# Struct that holds various paths related to ILMs.
class ILMStruct(NamedTuple('ILMStruct', [
    ('dir', str),
    ('data_dir', str),
    ('module', str),
    ('lef', str)
])):
    __slots__ = ()

    def to_setting(self) -> dict:
        return {
            "dir": self.dir,
            "data_dir": self.data_dir,
            "module": self.module,
            "lef": self.lef
        }

    @staticmethod
    def from_setting(ilm: dict) -> "ILMStruct":
        return ILMStruct(
            dir=str(ilm["dir"]),
            data_dir=str(ilm["data_dir"]),
            module=str(ilm["module"]),
            lef=str(ilm["lef"])
        )


ClockPort = NamedTuple('ClockPort', [
    ('name', str),
    ('period', TimeValue),
    ('port', Optional[str]),
    ('uncertainty', Optional[TimeValue])
])

OutputLoadConstraint = NamedTuple('OutputLoadConstraint', [
    ('name', str),
    ('load', float)
])


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
    def from_str(x: str) -> "ObstructionType":
        try:
            return ObstructionType.__mapping()[x]
        except KeyError:
            raise ValueError("Invalid obstruction type: " + str(x))

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
    def from_str(x: str) -> "PlacementConstraintType":
        try:
            return PlacementConstraintType.__mapping()[x]
        except KeyError:
            raise ValueError("Invalid placement constraint type: " + str(x))

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
    ('layers', Optional[List[str]]),
    ('obs_types', Optional[List[ObstructionType]])
])):
    __slots__ = ()

    @staticmethod
    def from_dict(constraint: dict) -> "PlacementConstraint":
        constraint_type = PlacementConstraintType.from_str(str(constraint["type"]))
        margins = None  # type: Optional[Margins]
        orientation = None  # type: Optional[str]
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
        if "layers" in constraint:
            layers = []
            for l in constraint["layers"]:
                layers.append(str(l))
        if "obs_types" in constraint:
            obs_types = []
            types = constraint["obs_types"]
            for t in types:
                obs_types.append(ObstructionType.from_str(str(t)))
        return PlacementConstraint(
            path=str(constraint["path"]),
            type=constraint_type,
            x=float(constraint["x"]),
            y=float(constraint["y"]),
            width=float(constraint["width"]),
            height=float(constraint["height"]),
            orientation=orientation,
            margins=margins,
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
    def from_string(s: str) -> "MMMCCornerType":
        if s == "setup":
            return MMMCCornerType.Setup
        elif s == "hold":
            return MMMCCornerType.Hold
        elif s == "extra":
            return MMMCCornerType.Extra
        else:
            raise ValueError("Invalid mmmc corner type '{}'".format(s))


MMMCCorner = NamedTuple('MMMCCorner', [
    ('name', str),
    ('type', MMMCCornerType),
    ('voltage', VoltageValue),
    ('temp', TemperatureValue),
])
