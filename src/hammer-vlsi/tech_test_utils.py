#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Helper and utility classes for testing hammer_tech.
#
#  See LICENSE for licence details.

# TODO: move this file out of hammer_vlsi.
# See issue #318.

import unittest
from typing import Optional

import hammer_tech


class HasGetTech(unittest.TestCase):
    """
    Helper mix-in that adds the convenience function get_tech.
    """

    def get_tech(self, tech_opt: Optional[hammer_tech.HammerTechnology]) -> hammer_tech.HammerTechnology:
        """
        Get the technology from the input parameter or raise an assertion.
        :param tech_opt: Result of HammerTechnology.load_from_dir()
        :return: Technology library or assertion will be raised.
        """
        self.assertTrue(tech_opt is not None, "Technology must be loaded")
        assert tech_opt is not None  # type checking
        return tech_opt
