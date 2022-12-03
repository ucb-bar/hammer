#  Data structures to represent technology's special cells.
#
#  See LICENSE for licence details.

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


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


class SpecialCell(BaseModel):
    # A SpecialCell is a technology cell used for non logic task (e.g. Tiecells,
    # Endcap, filler, etc.
    cell_type: CellType
    name: List[str]
    size: Optional[List[str]]
    input_ports: Optional[List[str]]
    output_ports: Optional[List[str]]

    class Config:
        # https://stackoverflow.com/questions/65209934/pydantic-enum-field-does-not-get-converted-to-string
        use_enum_values = True
