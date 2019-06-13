#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  spice_utils.py
#  Misc Verilog utilities
#
#  See LICENSE for licence details.

import re
from typing import Enum, Tuple, Optional, List

# Some convenience types
class SpiceModule(str):
    pass

class SpiceWithoutMultilines(str):
    pass

ModuleTree = Dict[SpiceModule, List[SpiceModule]]

class SpiceUtils:

#    # A convenience type for a data structure that is a mapping of a SPICE file name to
#    # a list of top cells or None (for an auto-detect mode)
#    SourceTopTuple = Tuple[str, Optional[List[str]]]
#
#    @staticmethod
#    def _str_to_source_top_tuple(source: Union[str, SourceTopTuple]) -> SourceTopTuple:
#        if isinstance(source, str):
#            return (str, None)
#        else:
#            return source

    @staticmethod
    def uniquify_spice(sources: List[str]):
        """
        Uniquify the provided SPICE sources. TODO finish doc

        :param sources:
        """
        #sources_tuple = [SpiceUtils._str_to_source_top_tuple(x) for x in sources]

        sources_no_multiline = 


    @staticmethod
    def module_tree(s: SpiceWithoutMultilines) -> ModuleTree:
        """
        Parse a SPICE file and return a dictionary that contains all found modules pointing to lists of their submodules.
        The SPICE file must not contain multiline statements.

        :param s: A SPICE file without any multiline statements
        :return: A dictionary whose keys are all found modules and whose values are the list of submodules
        """
        pass

    @staticmethod
    def reverse_module_tree(m: ModuleTree) -> ModuleTree:
        """
        Reverse a module tree dictionary so that the values are now the list of direct parent modules instead of submodules.

        :param m: A dictionary whose keys are SpiceModule strings and whose values are a list of submodules
        :return: A dictionary with the same keys whose values are a list of the modules' direct parents
        """
        pass

    @staticmethod
    def remove_multilines(s: str) -> SpiceWithoutMultilines:
        """
        Remove all multiline statements from the given SPICE source.

        :param s: The SPICE source
        :return: SPICE source without multiline statements
        """
        # Multilines in spice start with a + character
        multiline_pattern = r"(\r?\n\+\s*)"

        return SpiceWithoutMultilines(re.sub(multiline_pattern, " ", s, flags=re.DOTALL))



