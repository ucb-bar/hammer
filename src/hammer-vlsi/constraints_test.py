#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for Hammer IR constraints.
#
#  See LICENSE for licence details.

import hammer_config
from hammer_vlsi import DelayConstraint, ClockPort, DummyHammerTool, PinAssignment, PinAssignmentError, \
    PinAssignmentSemiAutoError
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


class PinAssignmentTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        """
        Test that converting to and from dict works.
        """
        orig = PinAssignment.create(
            pins="mypin",
            side="left",
            layers=["M3"],
            preplaced=False,
            width=20.5
        )
        copied = PinAssignment.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)

        orig = PinAssignment.create(
            pins="mysig",
            preplaced=True
        )
        copied = PinAssignment.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)

        orig = PinAssignment.create(
            pins="mypower",
            side="internal",
            layers=["M6"],
            location=(100.0, 200.0),
            width=15.0,
            depth=1.0
        )
        copied = PinAssignment.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)

    def test_invalid_side(self) -> None:
        """
        Test that invalid sides get caught.
        """
        with self.assertRaises(PinAssignmentError):
            PinAssignment.from_dict({
                "pins": "mypin",
                "side": "outerspace",
                "layer": ["M4"]
            })

        with self.assertRaises(PinAssignmentError):
            PinAssignment.from_dict({
                "pins": "mypin",
                "side": "",
                "layer": ["M4"]
            })

    def test_incomplete_pin(self) -> None:
        """
        Test that incomplete pins get caught.
        """
        with self.assertRaises(PinAssignmentError):
            PinAssignment.from_dict({
                "pins": "tumbleweed"
            })

    def test_semi_auto(self) -> None:
        """
        Test that semi-auto features are gated appropriately.
        """
        # Vanilla feature should just work
        PinAssignment.from_dict({
            "pins": "mypin",
            "side": "left",
            "layers": ["M4", "M5"]
        })

        # Examples of various pin constraints that need semi_auto.
        custom_width = {
            "pins": "ibias",
            "side": "bottom",
            "layers": ["M5"],
            "width": 20.0
        }
        custom_depth = {
            "pins": "ibias2",
            "side": "bottom",
            "layers": ["M3", "M5"],
            "depth": 20.0
        }
        custom_location = {
            "pins": "ibias2",
            "side": "bottom",
            "layers": ["M3", "M5"],
            "location": (10.0, 0.0)
        }
        internal = {
            "pins": "box",
            "side": "internal",
            "layers": ["M6"],
            "width": 20.0,
            "depth": 25.0
        }
        pins = [custom_width, custom_depth, custom_location, internal]
        for p in pins:
            # It should raise an error without semi_auto
            with self.assertRaises(PinAssignmentSemiAutoError):
                PinAssignment.from_dict(p, semi_auto=False)
            # ...and work fine with semi_auto.
            PinAssignment.from_dict(p, semi_auto=True)


if __name__ == '__main__':
    unittest.main()
