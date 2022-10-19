#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  stackup.py
#  Data structures to represent technology's special cells.
#
#  See LICENSE for licence details.

from enum import Enum
from typing import List, NamedTuple, Tuple, Dict, Optional
from hammer_utils import reverse_dict
from decimal import Decimal

class CellType(Enum):
    TieHiCell = 1
    TieLoCell = 2
    TieHiLoCell = 3
    EndCap = 4
    IOFiller = 5
    StdFiller = 6
    Decap = 7
    TapCell = 8
    Driver = 9
    CTSBuffer = 10

    @classmethod
    def __mapping(cls) -> Dict[str, "CellType"]:
        return {
            "tiehicell": CellType.TieHiCell,
            "tielocell": CellType.TieLoCell,
            "tiehilocell": CellType.TieHiLoCell,
            "endcap": CellType.EndCap,
            "iofiller": CellType.IOFiller,
            "stdfiller": CellType.StdFiller,
            "decap": CellType.Decap,
            "tapcell": CellType.TapCell,
            "driver": CellType.Driver,
            "ctsbuffer": CellType.CTSBuffer
        }

    @staticmethod
    def from_str(input_str: str) -> "CellType":
        # pylint: disable=missing-docstring
        try:
            return CellType.__mapping()[input_str]
        except KeyError:
            raise ValueError("Invalid CellType: " + str(input_str))

    def __str__(self) -> str:
        return reverse_dict(CellType.__mapping())[self]


class SpecialCell(NamedTuple('SpecialCell', [
        ('cell_type', CellType),
        ('name', List[str]),
        ('size', Optional[List[str]]),
        ('input_ports', Optional[List[str]]),
        ('output_ports', Optional[List[str]])
])):
    """
    A SpecialCell is a technology cell used for non logic task (e.g. Tiecells,
    Endcap, filler, etc.

    """
    __slots__ = ()

    @staticmethod
    def from_setting(d: dict) -> "SpecialCell":
        size = d["size"]
        input_ports = d["input_ports"]
        output_ports = d["output_ports"]
        if size is not None:
            size = list(map(lambda x: str(x), size))
        if input_ports is not None:
            input_ports = list(input_ports)
        if output_ports is not None:
            output_ports = list(output_ports)
        # pylint: disable=missing-docstring
        return SpecialCell(
            cell_type=CellType.from_str(d["cell_type"]),
            name=list(d["name"]),
            size=size,
            input_ports=input_ports,
            output_ports=output_ports,
        )
