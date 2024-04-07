#  Data structures to represent technology's special cells.
#
#  See LICENSE for licence details.

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, BaseModel


class CellType(str, Enum):
    TieHiCell = "tiehicell"
    TieLoCell = "tielocell"
    TieHiLoCell = "tiehilocell"
    EndCap = "endcap"
    IOFiller = "iofiller"
    StdFiller = "stdfiller"
    Decap = "decap"
    TapCell = "tapcell"
    Driver = "driver"
    CTSBuffer = "ctsbuffer"
    CTSInverter = "ctsinverter"
    CTSGate = "ctsgate"
    CTSLogic = "ctslogic"
    LevelShifter = "levelshifter"
    Isolation = "isolation"


class SpecialCell(BaseModel):
    # A SpecialCell is a technology cell used for non logic task (e.g. Tiecells,
    # Endcap, filler, etc.
    cell_type: CellType
    name: List[str]
    size: Optional[List[str]] = None
    input_ports: Optional[List[str]] = None
    output_ports: Optional[List[str]] = None
    model_config = ConfigDict(use_enum_values=True)
