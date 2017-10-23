#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  generate_properties.py
#  
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
#  Helper script to generate properties for hammer-vlsi tool classes.

from collections import namedtuple
import sys

InterfaceVar = namedtuple("InterfaceVar", 'name type desc')

def generate_from_list(template, lst):
    return map(lambda var: template.format(var_name=var.name, var_type=var.type, var_desc=var.desc), lst)

def main(args):
    template = """
@property
def {var_name}(self) -> {var_type}:
    \"""
    Get the {var_desc}.

    :return: The {var_desc}.
    \"""
    try:
        return self._{var_name}
    except AttributeError:
        raise ValueError("Nothing set for the {var_desc} yet")

@{var_name}.setter
def {var_name}(self, value: {var_type}) -> None:
    \"""Set the {var_desc}.\"""
    if not isinstance(value, {var_type}):
        raise TypeError("{var_name} must be a {var_type}")
    self._{var_name} = value # type: {var_type}
"""

    HammerSynthesisTool_inputs = [
        InterfaceVar("input_files", "Iterable[str]", "input collection of source RTL files (e.g. *.v)"),
        InterfaceVar("top_module", "str", "top-level module")
    ]
    HammerSynthesisTool_outputs = [
        InterfaceVar("output_files", "Iterable[str]", "output collection of mapped (post-synthesis) RTL files")
        # TODO: model CAD junk
    ]

    output = []
    output.append("### Inputs ###")
    output.extend(generate_from_list(template, HammerSynthesisTool_inputs))
    output.append("")
    output.append("### Outputs ###")
    output.extend(generate_from_list(template, HammerSynthesisTool_outputs))
    print("\n".join(output))
 
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
