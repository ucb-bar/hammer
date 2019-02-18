#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for Hammer IR constraints.
#
#  See LICENSE for licence details.

from typing import Dict, Tuple, List, Optional, Union

from hammer_vlsi import DelayConstraint
from hammer_vlsi.units import TimeValue

import unittest


class DelayConstraintTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        """
        Test that converting to and from dict works.
        """
        orig = DelayConstraint(
            name="mypin",
            clock="clock",
            direction="input",
            delay=TimeValue("20 ns")
        )
        copied = DelayConstraint.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)

        orig = DelayConstraint(
            name="pin_2",
            clock="clock_20MHz",
            direction="output",
            delay=TimeValue("0.3 ns")
        )
        copied = DelayConstraint.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)


    def test_invalid_direction(self) -> None:
        """
        Test that invalid directions are caught properly.
        """
        with self.assertRaises(ValueError):
            DelayConstraint(
                name="mypin",
                clock="clock",
                direction="bad",
                delay=TimeValue("20 ns")
            )

        with self.assertRaises(ValueError):
            DelayConstraint(
                name="mypin",
                clock="clock",
                direction="inputt",
                delay=TimeValue("20 ns")
            )

        with self.assertRaises(ValueError):
            DelayConstraint(
                name="mypin",
                clock="clock",
                direction="inputoutput",
                delay=TimeValue("20 ns")
            )

        with self.assertRaises(ValueError):
            DelayConstraint(
                name="mypin",
                clock="clock",
                direction="",
                delay=TimeValue("20 ns")
            )

        # Test that the error is raised with the dict as well.
        with self.assertRaises(ValueError):
            DelayConstraint.from_dict({
                "name": "mypin",
                "clock": "clock",
                "direction": "",
                "delay": "20 ns"
            })


if __name__ == '__main__':
     unittest.main()
