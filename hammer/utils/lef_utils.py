#  lef_utils.py
#  Misc LEF utilities
#  TODO: use a LEF library when this becomes complex enough.
#
#  See LICENSE for licence details.

import re
from decimal import Decimal
from typing import List, Optional, Tuple

__all__ = ['LEFUtils']


class LEFUtils:
    @staticmethod
    def get_sizes(source: str) -> List[Tuple[str, Decimal, Decimal]]:
        """
        Get the sizes of all macros in the given LEF source file.

        :param source: LEF file source, Unix line endings
        :return: List of all macros' sizes in the form of (macro name, width, height).
        """
        lines = source.split("\n")

        output = []  # type: List[Tuple[str, Decimal, Decimal]]

        in_propertydefinitions = False  # type: bool
        in_macro = None  # type: Optional[str]
        found_size = False  # type: bool
        for line in lines:
            # Check for PROPERTYDEFINITIONS statement
            regex = r"^\s*PROPERTYDEFINITIONS"
            regex_search = re.search(regex, line)

            if regex_search:
                if in_macro:
                    raise ValueError("Found PROPERTYDEFINITIONS inside MACRO")
                if in_propertydefinitions:
                    raise ValueError("Found PROPERTYDEFINITIONS inside PROPERTYDEFINITIONS")
                else:
                    in_propertydefinitions = True

            # Just wait for the end of PROPERTYDEFINITIONS
            if in_propertydefinitions:
                # Check for "END PROPERTYDEFINITIONS"
                regex = "END PROPERTYDEFINITIONS"
                if re.search(regex, line) is not None:
                    # END found
                    in_propertydefinitions = False
                continue

            # Check for MACRO statement
            regex = r"MACRO\s+([a-zA-Z0-9_]+)"
            regex_search = re.search(regex, line)

            if regex_search:
                macro_name = str(regex_search.group(1))
                if in_macro is not None:
                    raise ValueError(
                        "Found new MACRO statement {n} while parsing MACRO block {c}".format(n=macro_name, c=in_macro))
                else:
                    in_macro = macro_name
                    found_size = False

            # If not in MACRO block, skip
            if in_macro is None:
                continue

            # Check for "END <my_macro>"
            regex = "END " + re.escape(in_macro)
            if re.search(regex, line) is not None:
                # END found
                in_macro = None
                continue

            # Check for SIZE
            regex = r"SIZE\s+([\d\.]+)\s+[bB][yY]\s+([\d\.]+)\s*;"
            regex_search = re.search(regex, line)

            if regex_search:
                if found_size:
                    raise ValueError("Found two SIZE statements in MACRO block for {m}".format(m=in_macro))
                width = Decimal(regex_search.group(1))
                height = Decimal(regex_search.group(2))
                found_size = True

                # Add size to output
                output.append((in_macro, width, height))
                continue

        if in_macro is not None:
            raise ValueError("Unexpected end of file in MACRO block {m}".format(m=in_macro))

        return output
