#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for Hammer IR constraints.
#
#  See LICENSE for licence details.

import hammer_config
from hammer_vlsi import DelayConstraint, ClockPort, DummyHammerTool
from hammer_vlsi.units import TimeValue

import unittest


class ClockConstraintTest(unittest.TestCase):
    def check_src(self, yaml_src: str, ref_port: ClockPort) -> None:
        """
        Helper method to check if the given source parses to the given port.
        :param yaml_src: YAML config source
        :param ref_port: Reference port
        """
        database = hammer_config.HammerDatabase()
        database.update_project([
            hammer_config.load_config_from_string(yaml_src, is_yaml=True)
        ])
        tool = DummyHammerTool()
        tool.set_database(database)
        ports = tool.get_clock_ports()
        self.assertEqual(len(ports), 1)
        port = ports[0]
        self.assertEqual(port, ref_port)

    def test_read_config(self) -> None:
        """
        Test that reading it from config works.
        """
        src = """
vlsi.inputs.clocks:
- name: "my_port"
  period: "50 ns"
  path: "Top/clock"
  uncertainty: "1 ns"
  generated: true
  source_path: "Top/pll/out"
  divisor: 2
        """
        self.check_src(src, ClockPort(
            name="my_port",
            period=TimeValue("50 ns"),
            path="Top/clock",
            uncertainty=TimeValue("1 ns"),
            generated=True,
            source_path="Top/pll/out",
            divisor=2
        ))

    def test_optional_generated(self) -> None:
        """
        Test that the generated attribute is optional and that there is
        no effect if it is false.
        """
        src = """
vlsi.inputs.clocks:
- name: "my_port"
  period: "50 ns"
  path: "Top/clock"
  uncertainty: "1 ns"
  source_path: "Top/pll/out"
  divisor: 2
        """
        self.check_src(src, ClockPort(
            name="my_port",
            period=TimeValue("50 ns"),
            path="Top/clock",
            uncertainty=TimeValue("1 ns"),
            generated=None,
            source_path=None,
            divisor=None
        ))
        src2 = """
vlsi.inputs.clocks:
- name: "my_port"
  period: "50 ns"
  path: "Top/clock"
  uncertainty: "1 ns"
  generated: false
  source_path: "Top/pll/out"
  divisor: 2
        """
        self.check_src(src2, ClockPort(
            name="my_port",
            period=TimeValue("50 ns"),
            path="Top/clock",
            uncertainty=TimeValue("1 ns"),
            generated=False,
            source_path=None,
            divisor=None
        ))


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
