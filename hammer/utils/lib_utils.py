#  lib_utils.py
#  Misc Liberty utilities
#
#  See LICENSE for licence details.

import re
import os
import gzip
from decimal import Decimal
from typing import List, Optional, Tuple
__all__ = ['LIBUtils']


class LIBUtils:
    @staticmethod
    def get_time_unit(source: str) -> Optional[str]:
        """
        Get the time unit from the given LIB source file.
        """
        lines = LIBUtils.get_headers(source)
        try:
            match = next(line for line in lines if "time_unit" in line)
            # attibute syntax: time_unit : <value><unit> ;
            unit = re.split(" : | ; ", match)[1]
            return unit
        except StopIteration:  # should not get here
            return None

    @staticmethod
    def get_cap_unit(source: str) -> Optional[str]:
        """
        Get the load capacitance unit from the given LIB source file.
        """
        lines = LIBUtils.get_headers(source)
        try:
            match = next(line for line in lines if "capacitive_load_unit" in line)
            # attibute syntax: capacitive_load_unit(<value>,<unit>);
            # Also need to capitalize last f to F
            split = re.split("\(|,|\)", match)
            return split[1] + split[2].strip()[:-1] + split[2].strip()[-1].upper()
        except StopIteration:  # should not get here
            return None

    @staticmethod
    def get_headers(source: str) -> List[str]:
        """
        Get the header lines with the major info
        """
        nbytes = 10000
        if source.split('.')[-1] == "gz":
            z = gzip.GzipFile(source)
            lines = z.peek(nbytes).splitlines()
        else:
            # TODO: handle other compressed file types? Tools only seem to support gzip.
            fd = os.open(source, os.O_RDONLY)
            lines = os.pread(fd, nbytes, 0).splitlines()
        return list(map(lambda l: l.decode('ascii', errors='ignore'), lines))
