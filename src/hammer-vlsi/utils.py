#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  utils.py
#  Misc utils/functions for hammer_vlsi.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

import copy
from typing import List, Any, Set


def deepdict(x: dict) -> dict:
    """
    Deep copy a dictionary. This is needed because dict() by itself only makes a shallow copy.
    See https://stackoverflow.com/questions/5105517/deep-copy-of-a-dict-in-python
    Convenience function.
    :param x: Dictionary to copy
    :return: Deep copy of the dictionary provided by copy.deepcopy().
    """
    return copy.deepcopy(x)

def deeplist(x: list) -> list:
    """
    Deep copy a list. This is needed because list() by itself only makes a shallow copy.
    See https://stackoverflow.com/questions/5105517/deep-copy-of-a-dict-in-python
    Convenience function.
    :param x: List to copy
    :return: Deep copy of the list provided by copy.deepcopy().
    """
    return copy.deepcopy(x)


def add_lists(a: List[str], b: List[str]) -> List[str]:
    """Helper method: join two lists together while type checking."""
    assert isinstance(a, List)
    assert isinstance(b, List)
    return a + b


def in_place_unique(items: List[Any]) -> None:
    """
    "Fast" in-place uniquification of a list.
    :param items: List to be uniquified.
    """
    seen = set()  # type: Set[Any]
    i = 0
    # We will be all done when i == len(items)
    while i < len(items):
        item = items[i]
        if item in seen:
            # Delete and keep index pointer the same.
            del items[i]
            continue
        else:
            seen.add(item)
            i += 1
