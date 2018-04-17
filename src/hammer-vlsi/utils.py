#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  utils.py
#  Misc utils/functions for hammer_vlsi.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

import copy


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
