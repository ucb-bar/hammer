#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for Hammer IR constraints.
#
#  See LICENSE for licence details.

import hammer_config
from decimal import Decimal
from hammer_utils import add_dicts
from hammer_tech import MacroSize
from hammer_vlsi import DelayConstraint, ClockPort, DummyHammerTool, PinAssignment, PinAssignmentError, \
    PinAssignmentSemiAutoError, PlacementConstraint, PlacementConstraintType, Margins, \
    BumpAssignment, BumpsDefinition, BumpsPinNamingScheme, DecapConstraint
from hammer_vlsi.units import TimeValue, CapacitanceValue

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
  group: "ClkGrp"
        """
        self.check_src(src, ClockPort(
            name="my_port",
            period=TimeValue("50 ns"),
            path="Top/clock",
            uncertainty=TimeValue("1 ns"),
            generated=True,
            source_path="Top/pll/out",
            divisor=2,
            group="ClkGrp"
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
            divisor=None,
            group=None
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
            divisor=None,
            group=None
        ))

class BumpsTest(unittest.TestCase):
    def test_bump_naming(self) -> None:
        assignments = [
            BumpAssignment(name="foo",no_connect=False,x=Decimal(1),y=Decimal(1),group=None,custom_cell=None),
            BumpAssignment(name="bar",no_connect=False,x=Decimal(3),y=Decimal(1),group=None,custom_cell=None),
            BumpAssignment(name="baz",no_connect=True,x=Decimal(4),y=Decimal(1),group=None,custom_cell=None),
            BumpAssignment(name="qux",no_connect=False,x=Decimal(22),y=Decimal(204),group=None,custom_cell=None),
            BumpAssignment(name="quux",no_connect=False,x=Decimal(204),y=Decimal(204),group=None,custom_cell=None),
            BumpAssignment(name="alice",no_connect=False,x=Decimal(2),y=Decimal(204),group=None,custom_cell=None),
            BumpAssignment(name="bob",no_connect=False,x=Decimal(204),y=Decimal(22),group=None,custom_cell=None),
            BumpAssignment(name="VDD",no_connect=False,x=Decimal(203),y=Decimal(21),group=None,custom_cell=None),
            BumpAssignment(name="VSS",no_connect=False,x=Decimal(202),y=Decimal(20),group=None,custom_cell=None)
        ]
        definition = BumpsDefinition(x=204,y=204,pitch=Decimal("1.23"),cell="bumpcell",assignments=assignments)

        for a in assignments:
            if a.name == "foo":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "KD203")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "KD204")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "KD203")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "KD204")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "1")
            elif a.name == "bar":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "KD201")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "KD202")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "KD201")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "KD202")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "2")
            elif a.name == "baz":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "KD200")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "KD201")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "KD200")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "KD201")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "3")
            elif a.name == "qux":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "A182")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "A183")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "A182")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "A183")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "4")
            elif a.name == "quux":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "A0")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "A1")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "A000")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "A001")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "5")
            elif a.name == "alice":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "A202")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "A203")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "A202")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "A203")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "6")
            elif a.name == "bob":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "JC0")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "JC1")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "JC000")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "JC001")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "7")
            elif a.name == "VDD":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "JD1")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "JD2")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "JD001")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "JD002")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "8")
            elif a.name == "VSS":
                self.assertEqual(BumpsPinNamingScheme.A0.name_bump(definition, a), "JE2")
                self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, a), "JE3")
                self.assertEqual(BumpsPinNamingScheme.A00.name_bump(definition, a), "JE002")
                self.assertEqual(BumpsPinNamingScheme.A01.name_bump(definition, a), "JE003")
                self.assertEqual(BumpsPinNamingScheme.Index.name_bump(definition, a), "9")

        assignments = [
            BumpAssignment(name="foo",no_connect=False,x=Decimal(1),y=Decimal(1),group=None,custom_cell=None)
        ]
        definition = BumpsDefinition(x=420,y=420,pitch=Decimal("1.23"),cell="bumpcell",assignments=assignments)
        self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, assignments[0]), "YY420")

        definition = BumpsDefinition(x=421,y=421,pitch=Decimal("1.23"),cell="bumpcell",assignments=assignments)
        self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, assignments[0]), "AAA421")

        definition = BumpsDefinition(x=8420,y=8420,pitch=Decimal("1.23"),cell="bumpcell",assignments=assignments)
        self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, assignments[0]), "YYY8420")

        definition = BumpsDefinition(x=8421,y=8421,pitch=Decimal("1.23"),cell="bumpcell",assignments=assignments)
        self.assertEqual(BumpsPinNamingScheme.A1.name_bump(definition, assignments[0]), "AAAA8421")

    def test_bump_sort(self) -> None:
        assignments = [
            BumpAssignment(name="foo",no_connect=False,x=Decimal(1),y=Decimal(1),group=None,custom_cell=None),
            BumpAssignment(name="bar",no_connect=False,x=Decimal(3),y=Decimal(1),group=None,custom_cell=None),
            BumpAssignment(name="baz",no_connect=True,x=Decimal(4),y=Decimal(1),group=None,custom_cell=None),
            BumpAssignment(name="qux",no_connect=False,x=Decimal(22),y=Decimal(204),group=None,custom_cell=None),
            BumpAssignment(name="quux",no_connect=False,x=Decimal(204),y=Decimal(204),group=None,custom_cell=None),
            BumpAssignment(name="alice",no_connect=False,x=Decimal(2),y=Decimal(204),group=None,custom_cell=None),
            BumpAssignment(name="bob",no_connect=False,x=Decimal(204),y=Decimal(22),group=None,custom_cell=None),
            BumpAssignment(name="VDD",no_connect=False,x=Decimal(203),y=Decimal(21),group=None,custom_cell=None),
            BumpAssignment(name="VSS",no_connect=False,x=Decimal(202),y=Decimal(20),group=None,custom_cell=None)
        ]
        definition = BumpsDefinition(x=204,y=204,pitch=Decimal("1.23"),cell="bumpcell",assignments=assignments)

        idxs = [0, 3, 6, 2, 1]

        sorted_assignments = BumpsPinNamingScheme.Index.sort_by_name(definition, [assignments[x] for x in idxs])
        self.assertEqual(sorted_assignments, [assignments[x] for x in sorted(idxs)])

        sorted_assignments = BumpsPinNamingScheme.A0.sort_by_name(definition, assignments)
        self.assertEqual(sorted_assignments, [assignments[x] for x in [4, 3, 5, 6, 7, 8, 2, 1, 0]])


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


class DecapConstraintTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        """
        Test that converting to and from dict works.
        """
        orig = DecapConstraint(
            target="capacitance",
            density=None,
            capacitance=CapacitanceValue("2 pF"),
            x=Decimal(100),
            y=Decimal(200),
            width=Decimal(300),
            height=Decimal(400)
        )
        copied = DecapConstraint.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)

        orig = DecapConstraint(
            target="density",
            density=Decimal(0.5),
            capacitance=None,
            x=None,
            y=None,
            width=None,
            height=None
        )
        copied = DecapConstraint.from_dict(orig.to_dict())
        self.assertEqual(orig, copied)

    def test_invalid_target(self) -> None:
        """
        Test that invalid target is caught properly.
        """
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="cap",
                density=None,
                capacitance=CapacitanceValue("2 pF"),
                x=Decimal(100),
                y=Decimal(200),
                width=Decimal(300),
                height=Decimal(400)
            )

        with self.assertRaises(ValueError):
            DecapConstraint(
                target="dense",
                density=Decimal(0.5),
                capacitance=None,
                x=None,
                y=None,
                width=None,
                height=None
            )
        # Test that the error is raised with the dict as well.
        with self.assertRaises(ValueError):
            DecapConstraint.from_dict({
                "target": "",
                "density": 0.5
            })

    def test_invalid_density(self) -> None:
        """
        Test that density is specified properly
        """
        # Target is density but capacitance specified
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="density",
                density=None,
                capacitance=CapacitanceValue("2 pF"),
                x=None,
                y=None,
                width=None,
                height=None
            )

        # Desired density less than 0
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="density",
                density=Decimal(-50),
                capacitance=None,
                x=None,
                y=None,
                width=None,
                height=None
            )

        # Desired density greater than 1
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="density",
                density=Decimal(50),
                capacitance=None,
                x=None,
                y=None,
                width=None,
                height=None
            )

        # Area incorrectly specified
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="density",
                density=Decimal(50),
                capacitance=None,
                x=Decimal(100),
                y=Decimal(200),
                width=None,
                height=None
            )

    def test_invalid_capacitance(self) -> None:
        """
        Test that capacitance is specified properly
        """
        # Target is capacitance but density specified
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="capacitance",
                density=Decimal(0.5),
                capacitance=None,
                x=None,
                y=None,
                width=None,
                height=None
            )

        # Capacitance area incorrectly specified
        with self.assertRaises(ValueError):
            DecapConstraint(
                target="capacitance",
                density=None,
                capacitance=CapacitanceValue("2 pF"),
                x=Decimal(100),
                y=Decimal(200),
                width=None,
                height=None
            )


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

class PlacementConstraintTest(unittest.TestCase):

    def test_dummy(self) -> None:
        d = {"type": "dummy",
             "path": "dummy",
             "x": Decimal(4),
             "y": Decimal(6),
             "width": Decimal(10),
             "height": Decimal(20),
             "orientation": "r0"}
        tc = PlacementConstraint.from_dict(d)
        self.assertEqual(tc.type, PlacementConstraintType.Dummy)
        self.assertEqual(tc.path, "dummy")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(10))
        self.assertEqual(tc.height, Decimal(20))
        self.assertEqual(tc.orientation, "r0")
        with self.assertRaises(ValueError):
            m = {"margins": Margins.empty().to_dict()}
            # This should assert because margins are not allowed
            tc = PlacementConstraint.from_dict(add_dicts(d, m))

    def test_placement(self) -> None:
        d = {"type": "placement",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "width": Decimal(10),
             "height": Decimal(20),
             "orientation": "r0"}
        tc = PlacementConstraint.from_dict(d)
        self.assertEqual(tc.type, PlacementConstraintType.Placement)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(10))
        self.assertEqual(tc.height, Decimal(20))
        self.assertEqual(tc.orientation, "r0")
        with self.assertRaises(ValueError):
            m = {"margins": Margins.empty().to_dict()}
            # This should assert because margins are not allowed
            tc = PlacementConstraint.from_dict(add_dicts(d, m))

    def test_toplevel(self) -> None:
        d = {"type": "toplevel",
             "path": "path/to/placement",
             "x": Decimal(0),
             "y": Decimal(0),
             "width": Decimal(1000),
             "height": Decimal(2000)}
        with self.assertRaises(ValueError):
            # This should assert because margins are required
            tc = PlacementConstraint.from_dict(d)

        # Add margins
        m = {"margins": Margins.empty().to_dict()}
        tc = PlacementConstraint.from_dict(add_dicts(d, m))
        self.assertEqual(tc.type, PlacementConstraintType.TopLevel)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(0))
        self.assertEqual(tc.y, Decimal(0))
        self.assertEqual(tc.width, Decimal(1000))
        self.assertEqual(tc.height, Decimal(2000))

    def test_hardmacro(self) -> None:
        d = {"type": "hardmacro",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "width": Decimal(10),
             "height": Decimal(20),
             "orientation": "mx"}
        tc = PlacementConstraint.from_dict(d)
        self.assertEqual(tc.type, PlacementConstraintType.HardMacro)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(10))
        self.assertEqual(tc.height, Decimal(20))
        self.assertEqual(tc.orientation, "mx")
        with self.assertRaises(ValueError):
            m = {"margins": Margins.empty().to_dict()}
            # This should assert because margins are not allowed
            tc = PlacementConstraint.from_dict(add_dicts(d, m))

    def test_hierarchical(self) -> None:
        d = {"type": "hierarchical",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "master": "foo",
             "orientation": "mx"}
        with self.assertRaises(ValueError):
            # This should assert because width and height are missing
            tc = PlacementConstraint.from_dict(d)
        d.update({
             "width": Decimal(10),
             "height": Decimal(20)})
        tc = PlacementConstraint.from_dict(d)
        self.assertEqual(tc.type, PlacementConstraintType.Hierarchical)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(10))
        self.assertEqual(tc.height, Decimal(20))
        self.assertEqual(tc.master, "foo")
        self.assertEqual(tc.orientation, "mx")
        with self.assertRaises(ValueError):
            m = {"margins": Margins.empty().to_dict()}
            # This should assert because margins are not allowed
            tc = PlacementConstraint.from_dict(add_dicts(d, m))

    def test_obstruction(self) -> None:
        d = {"type": "obstruction",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "width": Decimal(10),
             "height": Decimal(20),
             "orientation": "mx"}
        with self.assertRaises(ValueError):
            # This should assert because we are missing obs_types
            tc = PlacementConstraint.from_dict(d)

        d.update({"obs_types": ["place"]})
        tc = PlacementConstraint.from_dict(d)
        self.assertEqual(tc.type, PlacementConstraintType.Obstruction)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(10))
        self.assertEqual(tc.height, Decimal(20))
        self.assertEqual(tc.orientation, "mx")
        with self.assertRaises(ValueError):
            m = {"margins": Margins.empty().to_dict()}
            # This should assert because margins are not allowed
            tc = PlacementConstraint.from_dict(add_dicts(d, m))

    def test_invalid(self) -> None:
        d = {"type": "foobar",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "width": Decimal(10),
             "height": Decimal(20),
             "orientation": "mx"}
        with self.assertRaises(ValueError):
            tc = PlacementConstraint.from_dict(d)

    def test_master_hardmacro(self) -> None:
        d = {"type": "hardmacro",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "master": "foo",
             "orientation": "mx"}

        masters = [MacroSize.from_setting(x) for x in [
            {"name": "foo", "library": "none", "width": "1234", "height": "2345"},
            {"name": "bar", "library": "none", "width": "2222", "height": "4444"}
        ]]

        tc = PlacementConstraint.from_masters_and_dict(masters, d)
        self.assertEqual(tc.type, PlacementConstraintType.HardMacro)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(1234))
        self.assertEqual(tc.height, Decimal(2345))
        self.assertEqual(tc.orientation, "mx")
        self.assertEqual(tc.master, "foo")

    def test_master_hierarchical(self) -> None:
        d = {"type": "hierarchical",
             "path": "path/to/placement",
             "x": Decimal(4),
             "y": Decimal(6),
             "master": "bar",
             "orientation": "mx"}

        masters = [MacroSize.from_setting(x) for x in [
            {"name": "foo", "library": "none", "width": "1234", "height": "2345"},
            {"name": "bar", "library": "none", "width": "2222", "height": "4444"}
        ]]

        with self.assertRaises(ValueError):
            # This should assert because width and height are missing
            tc = PlacementConstraint.from_dict(d)

        tc = PlacementConstraint.from_masters_and_dict(masters, d)
        self.assertEqual(tc.type, PlacementConstraintType.Hierarchical)
        self.assertEqual(tc.path, "path/to/placement")
        self.assertEqual(tc.x, Decimal(4))
        self.assertEqual(tc.y, Decimal(6))
        self.assertEqual(tc.width, Decimal(2222))
        self.assertEqual(tc.height, Decimal(4444))
        self.assertEqual(tc.orientation, "mx")
        self.assertEqual(tc.master, "bar")

if __name__ == '__main__':
    unittest.main()
