#  lef_utils.py
#  Misc LEF utilities
#  TODO: use a LEF library when this becomes complex enough.
#
#  See LICENSE for licence details.

import re
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Union

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

    @staticmethod
    def get_metals(source: str) -> List[Dict]:
        """
        Parse a tech LEF to extract Metal fields.
        Note: list(map(lambda m: Metal.model_validate(m), LEFUtils.get_metals(tlef_path)))
        is required to convert this into a list of Metals (we can't import stackups classes here)
        """
        metals = []
        def is_float(string):
            try:
                float(string)
                return True
            except ValueError:
                return False

        def get_min_from_line(line):
            words = line.split()
            nums = [float(w) for w in words if is_float(w)]
            return min(nums)

        with open(source, 'r') as f:
            metal_name = None
            metal_index = 0
            lines = f.readlines()
            idx = -1
            while idx < len(lines):
                idx += 1
                if idx == len(lines) - 1: break
                line = lines[idx]
                if '#' in line: line = line[:line.index('#')]
                words = line.split()
                if line.startswith('LAYER') and len(words) > 1:
                    if lines[idx+1].strip().startswith('TYPE ROUTING'):
                        metal_name = words[1]
                        metal_index += 1
                        metal = {}
                        metal["name"] = metal_name
                        metal["index"] = metal_index  # type: ignore

                if metal_name is not None:
                    line = line.strip()
                    if line.startswith("DIRECTION"):
                        metal["direction"] = words[1].lower()
                    if line.startswith("PITCH"):
                        metal["pitch"] = get_min_from_line(line)
                    if line.startswith("OFFSET"):
                        metal["offset"] = get_min_from_line(line)
                    if line.startswith("WIDTH"):
                        metal["min_width"] = get_min_from_line(line)
                    if line.startswith("SPACINGTABLE"):
                        metal["power_strap_widths_and_spacings"] = []  # type: ignore
                        while ';' not in line:
                            idx += 1
                            if idx == len(lines) - 1: break
                            line = lines[idx].strip()
                            if '#' in line: line = line[:line.index('#')]
                            words = line.split()
                            d = {}
                            if line.startswith("WIDTH"):
                                d["width_at_least"] = float(words[1])
                                d["min_spacing"] = float(words[2])
                                metal["power_strap_widths_and_spacings"].append(d.copy())  # type: ignore
                    #width table is a bit more complex
                    metal["power_strap_width_table"] = []  # type: ignore
                    # definition on one line
                    if "WIDTHTABLE" in line:
                        # definition on one line
                        if "LEF58_WIDTHTABLE" in line:
                            metal["power_strap_width_table"] = list(filter(lambda s: is_float(s), line.split()))
                        # multiple tables, only want routing direction one
                        if not any(s in line for x in ["ORTHOGONAL", "WRONGDIRECTION"]):
                            metal["power_strap_width_table"] = list(filter(lambda s: is_float(s), line.split()))

                    if line.startswith("END"):
                        # TODO: grid_unit is not currently parsed as part of the Metal data structure!
                        # See #379
                        metal["grid_unit"] = 0.001  # type: ignore
                        metals.append(metal.copy())
                        metal_name = None

        return metals
