#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from typing import Dict, Tuple, List

from hammer_utils import topological_sort

import unittest


class UtilsTest(unittest.TestCase):
    def test_topological_sort(self) -> None:
        """
        Test that topological sort works properly.
        """

        # tuple convention: (outgoing, incoming)
        graph = {
            "1": (["4"], []),
            "2": (["4"], []),
            "3": (["5", "6"], []),
            "4": (["7", "5"], ["1", "2"]),
            "5": (["8"], ["4", "3"]),
            "6": ([], ["3"]),
            "7": (["8"], ["4"]),
            "8": ([], ["7", "5"])
        }  # type: Dict[str, Tuple[List[str], List[str]]]

        self.assertEqual(topological_sort(graph, ["1", "2", "3"]), ["1", "2", "3", "4", "6", "7", "5", "8"])


if __name__ == '__main__':
     unittest.main()
