#  constraints.py
#  Data structures for various types of Hammer IR constraints.
#
#  See LICENSE for licence details.

# pylint: disable=bad-continuation
from dataclasses import dataclass, field
from decimal import Decimal
import math
import operator
import string
from enum import Enum
from functools import reduce
from typing import NamedTuple, Optional, Any, Union, cast

from hammer.utils import reverse_dict, get_or_else, add_dicts
from hammer.tech import MacroSize
from .units import TimeValue, VoltageValue, TemperatureValue, CapacitanceValue


# Struct that holds various paths related to ILMs.
class ILMStruct(NamedTuple('ILMStruct', [
    ('dir', str),
    ('data_dir', str),
    ('module', str),
    ('lef', str),
    ('gds', str),
    ('netlist', str),
    ('sim_netlist', Optional[str]),
    ('sdcs', list[str])
])):
    __slots__ = ()

    def to_setting(self) -> dict:
        output = {
            "dir": self.dir,
            "data_dir": self.data_dir,
            "module": self.module,
            "lef": self.lef,
            "gds": self.gds,
            "netlist": self.netlist,
            "sdcs": self.sdcs
        }
        if self.sim_netlist is not None:
            output.update({"sim_netlist": self.sim_netlist})
        return output

    @staticmethod
    def from_setting(ilm: dict) -> "ILMStruct":
        return ILMStruct(
            dir=str(ilm["dir"]),
            data_dir=str(ilm["data_dir"]),
            module=str(ilm["module"]),
            lef=str(ilm["lef"]),
            gds=str(ilm["gds"]),
            netlist=str(ilm["netlist"]),
            sim_netlist=ilm.get("sim_netlist"),
            sdcs=list(map(str, ilm["sdcs"]))
        )


# Transliterated-ish from SRAMGroup in MDF
# TODO: Convert this is to use the HammerIR library once #330 is resolved
class SRAMParameters(NamedTuple('SRAMParameters', [
    ('name', str),
    ('family', str),
    ('depth', int),
    ('width', int),
    ('mask', bool),
    ('vt', str),
    ('mux', int)
])):
    __slots__ = ()

    @staticmethod
    def from_setting(d: dict) -> "SRAMParameters":
        # pylint: disable=missing-docstring
        return SRAMParameters(
            name=str(d["name"]),
            family=str(d["family"]),
            depth=int(d["depth"]),
            width=int(d["width"]),
            mask=bool(d["mask"]),
            vt=str(d["vt"]),
            mux=int(d["mux"])
        )


@dataclass
class Supply:
    """Supply constraint defined in defaults.yml."""

    name: str
    pins: Optional[list[str]]
    tie: Optional[str]
    weight: Optional[str]
    voltage: Optional[str]
    interacts: Optional[list[str]] = field(default_factory=list)
    domain: Optional[str] = "AO"


class PinAssignmentError(ValueError):
    """Exception raised from parsing an invalid PinAssignment object."""


class PinAssignmentSemiAutoError(PinAssignmentError):
    """Exception raised from parsing a PinAssignment that requires semi-auto features without explicitly enabing
    them."""


class PinAssignmentPreplacedError(PinAssignmentError):
    """Exception raised from parsing a preplaced pin with extraneous information."""

    def __init__(self, pin: "PinAssignment") -> None:
        self.pin = pin

    def __str__(self) -> str:
        return f"Pins {self.pin.pins} assigned as a preplaced pin with layers or side. Assuming pins are preplaced pins and ignoring layers and side."


class PinAssignment(NamedTuple('PinAssignment', [
    ('pins', str),
    ('side', Optional[str]),
    ('layers', Optional[list[str]]),
    ('preplaced', bool),
    ('location', Optional[tuple[float, float]]),
    ('width', Optional[float]),
    ('depth', Optional[float])
])):
    __slots__ = ()

    def __new__(cls, pins: str, side: Optional[str] = None, layers: Optional[list[str]] = None,
                preplaced: Optional[bool] = None,
                location: Optional[tuple[float, float]] = None, width: Optional[float] = None,
                depth: Optional[float] = None) -> "PinAssignment":
        return super().__new__(cls, pins, side, layers, get_or_else(preplaced, False), location, width, depth)

    @staticmethod
    def create(pins: str, side: Optional[str] = None, layers: Optional[list[str]] = None,
                preplaced: Optional[bool] = None,
                location: Optional[tuple[float, float]] = None, width: Optional[float] = None,
                depth: Optional[float] = None) -> "PinAssignment":
        """
        Static method that works around the fact that mypy gets very confused at
        the custom constructor above that defines default arguments.
        """
        return PinAssignment(pins, side, layers, get_or_else(preplaced, False), location, width, depth)

    @staticmethod
    def from_dict(raw_assign: dict[str, Any], semi_auto: bool = True) -> "PinAssignment":
        pins = str(raw_assign["pins"])  # type: str

        side = None  # type: Optional[str]
        if "side" in raw_assign:
            raw_side = raw_assign["side"]  # type: str
            assert isinstance(raw_side, str), "side must be a str"

            if raw_side in ("top", "bottom", "right", "left", "internal"):
                side = raw_side
                if side == "internal" and not semi_auto:
                    raise PinAssignmentSemiAutoError("side set to internal")
            else:
                raise PinAssignmentError(
                    f"Pins {pins} have invalid side {raw_side}. Assuming pins will be handled by CAD tool.")

        preplaced = raw_assign.get("preplaced", False)  # type: bool
        assert isinstance(preplaced, bool), "preplaced must be a bool"

        location = None  # type: Optional[tuple[float, float]]
        if "location" in raw_assign:
            location_raw = raw_assign["location"]  # type: Union[list[float], tuple[float, float]]
            assert len(location_raw) == 2, "location must be a Optional[Tuple[float, float]]"
            assert isinstance(location_raw[0], float), "location must be a Optional[Tuple[float, float]]"
            assert isinstance(location_raw[1], float), "location must be a Optional[Tuple[float, float]]"
            location = (location_raw[0], location_raw[1])
        if not semi_auto and location is not None:
            raise PinAssignmentSemiAutoError("location requires semi_auto")

        width = raw_assign.get("width", None)  # type: Optional[float]
        if width is not None:
            assert isinstance(width, float), "width must be a float"
        if not semi_auto and width is not None:
            raise PinAssignmentSemiAutoError("width requires semi_auto")

        depth = raw_assign.get("depth", None)  # type: Optional[float]
        if depth is not None:
            assert isinstance(depth, float), "depth must be a float"
        if not semi_auto and depth is not None:
            raise PinAssignmentSemiAutoError("depth requires semi_auto")

        layers = None  # type: Optional[list[str]]
        if "layers" in raw_assign:
            raw_layers = raw_assign["layers"]  # type: list[str]
            assert isinstance(raw_layers, list), "layers must be a List[str]"
            for layer in "layers":
                assert isinstance(layer, str), "layers must be a List[str]"
            layers = raw_layers

        if preplaced:
            should_be_none = reduce(operator.and_, map(lambda x: x is None, [side, location, width, depth]))
            if len(get_or_else(layers, cast(list[str], []))) > 0 or not should_be_none:
                raise PinAssignmentPreplacedError(
                    PinAssignment(pins=pins, side=None, layers=[], preplaced=preplaced, location=None, width=None,
                                  depth=None))
        else:
            if len(get_or_else(layers, cast(list[str], []))) == 0 or side is None:
                raise PinAssignmentError(
                    f"Pins {pins} assigned without layers or side. Assuming pins will be handled by CAD tool.")
        return PinAssignment(
            pins=pins,
            side=side,
            layers=layers,
            preplaced=preplaced,
            location=location,
            width=width,
            depth=depth
        )

    def to_dict(self) -> dict:
        base = {
            "pins": self.pins,
            "preplaced": self.preplaced
        }  # type: dict[str, Any]
        if self.side is not None:
            base['side'] = self.side
        if self.layers is not None:
            base['layers'] = self.layers
        if self.location is not None:
            base['location'] = self.location
        if self.width is not None:
            base['width'] = self.width
        if self.depth is not None:
            base['depth'] = self.depth
        return base


BumpAssignment = NamedTuple('BumpAssignment', [
    ('name', Optional[str]),
    ('no_connect', Optional[bool]),
    ('x', Decimal),
    ('y', Decimal),
    ('group', Optional[str]),
    ('custom_cell', Optional[str])
])

BumpsDefinition = NamedTuple('BumpsDefinition', [
    ('x', int),
    ('y', int),
    ('pitch_x', Decimal),
    ('pitch_y', Decimal),
    ('global_x_offset', Decimal),
    ('global_y_offset', Decimal),
    ('cell', str),
    ('assignments', list[BumpAssignment])
])

class BumpsPinNamingScheme(Enum):
    A0 = 0
    A1 = 1
    A00 = 2
    A01 = 3
    Index = 4

    @classmethod
    def __mapping(cls) -> dict[str, "BumpsPinNamingScheme"]:
        return {
            "A0": BumpsPinNamingScheme.A0,
            "A1": BumpsPinNamingScheme.A1,
            "A00": BumpsPinNamingScheme.A00,
            "A01": BumpsPinNamingScheme.A01,
            "index": BumpsPinNamingScheme.Index
        }

    @staticmethod
    def from_str(input_str: str) -> "BumpsPinNamingScheme":
        try:
            return BumpsPinNamingScheme.__mapping()[input_str]
        except KeyError as exc:
            raise ValueError(f"Invalid bumps pin naming scheme: {input_str}") from exc

    def __str__(self) -> str:
        return reverse_dict(BumpsPinNamingScheme.__mapping())[self]

    def sort_by_name(self, definition: BumpsDefinition, assignments: list[BumpAssignment]) -> list[BumpAssignment]:
        """
        Sort a list of bump assignments for a given bump definition by their name in a human-readable way.

        :param definition: The bumps definition
        :param assignments: The list of bump assignments which may or may not be equivalent to definition.assignments
        :return: A sorted list of bump assignments
        """
        bpns = BumpsPinNamingScheme
        if self == bpns.Index:
            def sortkey(assignment: BumpAssignment) -> int:
                # It's possible that the assignments list here is not the same as the definition list,
                # so we need to figure out what the actual name is before sorting
                return int(self.name_bump(definition, assignment))
            return sorted(assignments, key=sortkey)
        elif self in [bpns.A0, bpns.A1, bpns.A00, bpns.A01]:
            def sortkey(assignment: BumpAssignment) -> int:
                # This deterministically names bumps, so we can just figure out the order by looking
                # at x and y
                return int(definition.x * (definition.y - assignment.y) + (definition.x - assignment.x + 1))
            return sorted(assignments, key=sortkey)
        else:
            assert False, "Should not get here; a developer messed up."

    def name_bump(self, definition: BumpsDefinition, assignment: BumpAssignment) -> str:
        # Skip I, O, Q, S, X, and Z
        skips = list('IOQSXZ')
        letters = [x for x in list(string.ascii_uppercase) if x not in skips]
        radix = len(letters)
        # Sanity check
        assert radix == 20

        col = int(assignment.x)
        row = int(assignment.y)


        bpns = BumpsPinNamingScheme
        if self == bpns.Index:
            # This raises a ValueError if the entry is not in the list, which shouldn't happen except to devs
            return str(definition.assignments.index(assignment) + 1)

        elif self in [bpns.A0, bpns.A1, bpns.A00, bpns.A01]:

            if Decimal(col) != assignment.x or Decimal(row) != assignment.y:
                raise ValueError(f"This bump naming scheme does not support fractional x and y assignments: x={assignment.x}, y={assignment.y}. Implement this, or increase the pitch and use blowouts.")

            # Top right in GDS-land is A0 or A1 (this is top-left in board-land)
            col = definition.x - col
            row = definition.y - row

            row_str = str(letters[row % radix])
            row = row // radix
            # This math gets funky, because leading letters are worth 1 more digit (blank is 0 for leadings, but A is 0 for non-leading digits)
            while row > 0:
                row = row - 1
                row_str = str(letters[row % radix]) + row_str
                row = row // radix

            col_offs = 0
            pad_zero = False

            if self == BumpsPinNamingScheme.A0:
                pass
            elif self == BumpsPinNamingScheme.A1:
                col_offs = 1
            elif self == BumpsPinNamingScheme.A00:
                pad_zero = True
            elif self == BumpsPinNamingScheme.A01:
                col_offs = 1
                pad_zero = True
            else:
                assert False, "should not get here"

            # Add the offset for A1 and A01
            col = col + col_offs

            # calculate the number of zeros we need
            max_value = definition.x - 1 + col_offs
            num_digits = math.ceil(math.log(max_value)/math.log(10))

            col_str = str(col)
            # use the zero padding if applicable
            if pad_zero:
                col_str = ("{:0" + str(num_digits) + "d}").format(col)

            return row_str + col_str
        else:
            assert False, "Should not get here; a developer messed up"

ClockPort = NamedTuple('ClockPort', [
    ('name', str),
    ('period', Optional[TimeValue]),
    ('path', Optional[str]),
    ('uncertainty', Optional[TimeValue]),
    ('generated', Optional[bool]),
    ('source_path', Optional[str]),
    ('divisor', Optional[int]),
    ('group', Optional[str])
])

OutputLoadConstraint = NamedTuple('OutputLoadConstraint', [
    ('name', str),
    ('load', CapacitanceValue)
])


class DelayConstraint(NamedTuple('DelayConstraint', [
    ('name', str),
    ('clock', str),
    ('direction', str),
    ('delay', TimeValue),
    ('corner', Optional[str])
])):
    __slots__ = ()

    def __new__(cls, name: str, clock: str, direction: str, delay: TimeValue, corner: Optional[str]) -> "DelayConstraint":
        if direction not in ("input", "output"):
            raise ValueError(f"Invalid direction {direction} for a delay constraint")
        if corner is not None:
            if corner not in ("setup", "hold"):
                raise ValueError(f"Invalid corner {corner} for a delay constraint")
        return super().__new__(cls, name, clock, direction, delay, corner)

    @staticmethod
    def from_dict(delay_src: dict[str, Any]) -> "DelayConstraint":
        direction = str(delay_src["direction"])
        corner = None  # type: Optional[str]
        if "corner" in delay_src:
            corner = str(delay_src["corner"])
        return DelayConstraint(
            name=str(delay_src["name"]),
            clock=str(delay_src["clock"]),
            direction=direction,
            delay=TimeValue(delay_src["delay"]),
            corner=corner
        )

    def to_dict(self) -> dict:
        output = {
            "name": self.name,
            "clock": self.clock,
            "direction": self.direction,
            "delay": self.delay.str_value_in_units("ns", round_zeroes=False)
        }
        if self.corner is not None:
            output.update({"corner": self.corner})
        return output

class DecapConstraint(NamedTuple('DecapConstraint', [
    ('target', str),
    ('density', Optional[Decimal]),
    ('capacitance', Optional[CapacitanceValue]),
    ('x', Optional[Decimal]),
    ('y', Optional[Decimal]),
    ('width', Optional[Decimal]),
    ('height', Optional[Decimal])
])):
    __slots__ = ()

    def __new__(cls,
            target: str,
            density: Optional[Decimal],
            capacitance: Optional[CapacitanceValue],
            x: Optional[Decimal],
            y: Optional[Decimal],
            width: Optional[Decimal],
            height: Optional[Decimal]) -> "DecapConstraint":
        if target not in ("capacitance", "density"):
            raise ValueError(f"Invalid target {target}")
        if target == "density" and density is None:
            raise ValueError("Need to specify decap density")
        if density is not None:
            if density > Decimal(1) or density < Decimal(0):
                raise ValueError("Density must be between 0 and 1, inclusive")
        if target == "capacitance" and capacitance is None:
            raise ValueError("Need to specify decap capacitance")
        all_none = all(x is None for x in (x, y, width, height))
        all_specified = all(x is not None for x in (x, y, width, height))
        if not (all_none or all_specified):
            raise ValueError("Decap x, y, width, and height must all be specified")
        return super().__new__(cls, target, density, capacitance, x, y, width, height)

    @staticmethod
    def from_dict(decap_src: dict[str, Any]) -> "DecapConstraint":
        density = None  # type: Optional[Decimal]
        if "density" in decap_src:
            density = Decimal(str(decap_src["density"]))
        capacitance = None  # type: Optional[CapacitanceValue]
        if "capacitance" in decap_src:
            capacitance = CapacitanceValue(decap_src["capacitance"])
        x = None  # type: Optional[Decimal]
        if "x" in decap_src:
            x = Decimal(str(decap_src["x"]))
        y = None  # type: Optional[Decimal]
        if "y" in decap_src:
            y = Decimal(str(decap_src["y"]))
        width = None  # type: Optional[Decimal]
        if "width" in decap_src:
            width = Decimal(str(decap_src["width"]))
        height = None  # type: Optional[Decimal]
        if "height" in decap_src:
            height = Decimal(str(decap_src["height"]))
        return DecapConstraint(
            target=str(decap_src["target"]),
            density=density,
            capacitance=capacitance,
            x=x, y=y, width=width, height=height
        )

    def to_dict(self) -> dict:
        output = {"target": self.target}
        if self.density is not None:
            output.update({"density": str(self.density)})
        if self.capacitance is not None:
            output.update({"capacitance": self.capacitance.str_value_in_units("fF")})
        if self.x is not None:
            output.update({"x": str(self.x)})
        if self.y is not None:
            output.update({"y": str(self.y)})
        if self.width is not None:
            output.update({"width": str(self.width)})
        if self.height is not None:
            output.update({"height": str(self.height)})
        return output

class ObstructionType(Enum):
    Place = 1
    Route = 2
    Power = 3

    @classmethod
    def __mapping(cls) -> dict[str, "ObstructionType"]:
        return {
            "place": ObstructionType.Place,
            "route": ObstructionType.Route,
            "power": ObstructionType.Power
        }

    @staticmethod
    def from_str(input_str: str) -> "ObstructionType":
        try:
            return ObstructionType.__mapping()[input_str]
        except KeyError as exc:
            raise ValueError(f"Invalid obstruction type: {input_str}") from exc

    def __str__(self) -> str:
        return reverse_dict(ObstructionType.__mapping())[self]


class PlacementConstraintType(Enum):
    Dummy = 1
    SoftPlacement = 2
    HardPlacement = 3
    TopLevel = 4
    HardMacro = 5
    Hierarchical = 6
    Obstruction = 7
    Overlap = 8
    PowerDomain = 9

    @classmethod
    def __mapping(cls) -> dict[str, "PlacementConstraintType"]:
        return {
            "dummy": PlacementConstraintType.Dummy,
            "placement": PlacementConstraintType.SoftPlacement,
            "soft_placement": PlacementConstraintType.SoftPlacement,
            "hard_placement": PlacementConstraintType.HardPlacement,
            "toplevel": PlacementConstraintType.TopLevel,
            "hardmacro": PlacementConstraintType.HardMacro,
            "hierarchical": PlacementConstraintType.Hierarchical,
            "obstruction": PlacementConstraintType.Obstruction,
            "overlap": PlacementConstraintType.Overlap,
            "powerdomain": PlacementConstraintType.PowerDomain
        }

    @staticmethod
    def from_str(input_str: str) -> "PlacementConstraintType":
        try:
            return PlacementConstraintType.__mapping()[input_str]
        except KeyError as exc:
            raise ValueError(f"Invalid placement constraint type: {input_str}") from exc

    def __str__(self) -> str:
        return reverse_dict(PlacementConstraintType.__mapping())[self]


# For the top-level chip size constraint, set the margin from core area to left/bottom/right/top.
class Margins(NamedTuple('Margins', [
    ('left', Decimal),
    ('bottom', Decimal),
    ('right', Decimal),
    ('top', Decimal)
])):

    @staticmethod
    def from_dict(d: dict) -> "Margins":
        return Margins(
            left=Decimal(str(d["left"])),
            bottom=Decimal(str(d["bottom"])),
            right=Decimal(str(d["right"])),
            top=Decimal(str(d["top"]))
        )

    @staticmethod
    def empty() -> "Margins":
        return Margins(
            left=Decimal(0),
            bottom=Decimal(0),
            right=Decimal(0),
            top=Decimal(0)
        )

    def to_dict(self) -> dict:
        return {
            "left": str(self.left),
            "bottom": str(self.bottom),
            "right": str(self.right),
            "top": str(self.top)
        }


class PlacementConstraint(NamedTuple('PlacementConstraint', [
    ('path', str),
    ('type', PlacementConstraintType),
    ('x', Decimal),
    ('y', Decimal),
    ('width', Decimal),
    ('height', Decimal),
    ('master', Optional[str]),
    ('create_physical', Optional[bool]),
    ('orientation', Optional[str]),
    ('margins', Optional[Margins]),
    ('top_layer', Optional[str]),
    ('layers', Optional[list[str]]),
    ('obs_types', Optional[list[ObstructionType]]),
    ('power_domain', Optional[str])
])):
    __slots__ = ()


    @staticmethod
    def _get_master(constraint_type: PlacementConstraintType, constraint: dict) -> Optional[str]:
        """
        A helper method to retrieve the master key from a constraint dict. This is broken out into its own function because it's
        used in multiple methods. The master key is mandatory for Hierarchical constraint, optional for HardMacro constraints,
        and disallowed otherwise.

        :param constraint_type: A PlacementConstraintType object describing the type of constraint
        :param constraint: A dict that may or may not contain a master key
        :return: The value pointed to by master or None, if allowed by the constraint type
        """
        # This field is mandatory for Hierarchical constraints
        # This field is optional for HardMacro constraints
        # This field is disallowed otherwise
        master = None  # type: Optional[str]
        if "master" in constraint:
            if constraint_type not in [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro, PlacementConstraintType.Overlap]:
                raise ValueError(f"Constraints other than Hierarchical, HardMacro, and Overlap must not contain master: {constraint}")
            master = str(constraint["master"])
        else:
            if constraint_type == PlacementConstraintType.Hierarchical:
                raise ValueError(f"Hierarchical constraints must contain master: {constraint}")
        return master

    @staticmethod
    def from_masters_and_dict(masters: list[MacroSize], constraint: dict) -> "PlacementConstraint":
        """
        Create a PlacementConstraint tuple from a constraint dict and a list of masters. This method differs from from_dict by
        allowing the width and height to be auto-filled from a list of masters for the Hierarchical and HardMacro constraint types.

        :param masters: A list of MacroSize tuples containing cell macro definitions
        :param constraint: A dict containing information to be parsed into a PlacementConstraint tuple
        :return: A PlacementConstraint tuple
        """

        constraint_type = PlacementConstraintType.from_str(str(constraint["type"]))
        master = PlacementConstraint._get_master(constraint_type, constraint)

        checked_types = [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro, PlacementConstraintType.Overlap]
        width_check = None  # type: Optional[Decimal]
        height_check = None  # type: Optional[Decimal]
        # Get the "Master" values
        if constraint_type == PlacementConstraintType.Hierarchical:
            # This should be true given the code above, but sanity check anyway
            assert master is not None
            matches = [x for x in masters if x.name == master]
            if len(matches) > 0:
                width_check = Decimal(str(matches[0].width))
                height_check = Decimal(str(matches[0].height))
            else:
                raise ValueError(f"Could not find a master for hierarchical cell {master} in masters list.")
        elif constraint_type in [PlacementConstraintType.HardMacro, PlacementConstraintType.Overlap]:
            # TODO(johnwright) for now we're allowing HardMacros to be flexible- checks are performed if the data exists, but otherwise
            # we will "trust" the provided width and height. They aren't actually used, so this is not super important at the moment.
            # ucb-bar/hammer#414
            if master is not None:
                matches = [x for x in masters if x.name == master]
                if len(matches) > 0:
                    width_check = Decimal(str(matches[0].width))
                    height_check = Decimal(str(matches[0].height))
        else:
            assert constraint_type not in checked_types, "Should not get here; update checked_types."

        width = None
        height = None

        if "width" in constraint:
            width = Decimal(str(constraint["width"]))
        else:
            width = width_check

        if "height" in constraint:
            height = Decimal(str(constraint["height"]))
        else:
            height = height_check

        # Perform the check
        if constraint_type in checked_types:
            if height != height_check and height_check is not None:
                raise ValueError(f"Optional height value {height} must equal the master value {height_check} for constraint: {constraint}")
            if width != width_check and width_check is not None:
                raise ValueError(f"Optional width value {width} must equal the master value {width_check} for constraint: {constraint}")

        updated_constraint = constraint
        if width is not None:
            updated_constraint = add_dicts(updated_constraint, {'width': width})
        if height is not None:
            updated_constraint = add_dicts(updated_constraint, {'height': height})

        return PlacementConstraint.from_dict(updated_constraint)

    @staticmethod
    def from_dict(constraint: dict) -> "PlacementConstraint":
        constraint_type = PlacementConstraintType.from_str(str(constraint["type"]))

        ### Margins ###
        # This field is mandatory in TopLevel constraints
        # This field is disallowed otherwise
        margins = None  # type: Optional[Margins]
        if "margins" in constraint:
            if constraint_type != PlacementConstraintType.TopLevel:
                raise ValueError(f"Non-TopLevel constraint must not contain margins: {constraint}")
            margins_dict = constraint["margins"]
            margins = Margins.from_dict(margins_dict)
        else:
            if constraint_type == PlacementConstraintType.TopLevel:
                raise ValueError(f"TopLevel constraint must contain margins: {constraint}")

        ### Orientation ###
        # This field is disallowed in TopLevel constraints
        # This field is optional otherwise
        orientation = None  # type: Optional[str]
        if "orientation" in constraint:
            if constraint_type == PlacementConstraintType.TopLevel:
                raise ValueError(f"Non-TopLevel constraint must not contain orientation: {constraint}")
            orientation = str(constraint["orientation"])

        ### Top layer ###
        # This field is optional in Hierarchical and HardMacro constraints
        # This field is disallowed otherwise
        top_layer = None  # type: Optional[str]
        if "top_layer" in constraint:
            if constraint_type not in [PlacementConstraintType.Hierarchical, PlacementConstraintType.HardMacro]:
                raise ValueError(f"Constraints other than Hierarchical and HardMacro must not contain top_layer: {constraint}")
            top_layer = str(constraint["top_layer"])

        ### Layers ###
        # This field is optional in Obstruction constraints
        # This field is disallowed otherwise
        layers = None  # type: Optional[list[str]]
        if "layers" in constraint:
            if constraint_type != PlacementConstraintType.Obstruction:
                raise ValueError(f"Non-Obstruction constraint must not contain layers: {constraint}")
            layers = []
            for layer in constraint["layers"]:
                layers.append(str(layer))

        ### Obstruction types ###
        # This field is mandatory in Obstruction constraints
        # This field is disallowed otherwise
        obs_types = None  # type: Optional[list[ObstructionType]]
        if "obs_types" in constraint:
            if constraint_type != PlacementConstraintType.Obstruction:
                raise ValueError(f"Non-Obstruction constraint must not contain obs_types: {constraint}")
            obs_types = []
            types = constraint["obs_types"]
            for obs_type in types:
                obs_types.append(ObstructionType.from_str(str(obs_type)))
        else:
            if constraint_type == PlacementConstraintType.Obstruction:
                raise ValueError(f"Obstruction constraint must contain obs_types: {constraint}")

        ### Power Domain ###
        # This field is disallowed in PowerDomain constraints, optional otherwise
        power_domain = None  # type: Optional[str]
        if "power_domain" in constraint:
            if constraint_type == PlacementConstraintType.PowerDomain:
                raise ValueError(f"PowerDomain constraint must not contain power_domain: {constraint}")
            power_domain = str(constraint["power_domain"])

        ### Master ###
        master = PlacementConstraint._get_master(constraint_type, constraint)

        ### Create physical ###
        # This field is optional in HardMacro and Overlap constraints
        # This field is disallowed otherwise
        create_physical = None  # type: Optional[bool]
        if "create_physical" in constraint:
            if constraint_type not in [PlacementConstraintType.HardMacro, PlacementConstraintType.Overlap]:
                raise ValueError(f"Constraints other than HardMacro or Overlap must not specify create_physical: {constraint}")
            if master is None:
                raise ValueError(f"HardMacro or Overlap constraint specifying create_physical must also specify a master: {constraint}")
            create_physical = constraint["create_physical"]
            assert isinstance(create_physical, bool)

        ### Width & height ###
        # These fields are mandatory for Hierarchical, Dummy, Soft/HardPlacement, TopLevel, and Obstruction constraints
        # These fields are optional for HardMacro and Overlap constraints
        # TODO(ucb-bar/hammer#414) make them mandatory for HardMacro and Overlap once there's a more robust way of automatically getting that data into hammer
        # This is not None because we don't want to make width optional for the reason above
        width = Decimal(0)
        if "width" in constraint:
            width = Decimal(str(constraint["width"]))
        else:
            # TODO(ucb-bar/hammer#414) remove this allowance and just raise the error
            if constraint_type not in [PlacementConstraintType.HardMacro, PlacementConstraintType.Overlap]:
                raise ValueError(f"Non-HardMacro or Overlap constraint must contain a width: {constraint}")

        # This is not None because we don't want to make height optional for the reason above
        height = Decimal(0)
        if "height" in constraint:
            height = Decimal(str(constraint["height"]))
        else:
            # TODO(ucb-bar/hammer#414) remove this allowance and just raise the error
            if constraint_type not in [PlacementConstraintType.HardMacro, PlacementConstraintType.Overlap]:
                raise ValueError(f"Non-HardMacro or Overlap constraint must contain a height: {constraint}")

        ### X & Y coordinates ###
        # These fields are mandatory in all constraints
        if "x" not in constraint:
            raise ValueError(f"Constraint must contain an x coordinate: {constraint}")
        if "y" not in constraint:
            raise ValueError(f"Constraint must contain an y coordinate: {constraint}")
        x = Decimal(str(constraint["x"]))
        y = Decimal(str(constraint["y"]))

        return PlacementConstraint(
            path=str(constraint["path"]),
            type=constraint_type,
            x=x,
            y=y,
            width=width,
            height=height,
            master=master,
            create_physical=create_physical,
            orientation=orientation,
            margins=margins,
            top_layer=top_layer,
            layers=layers,
            obs_types=obs_types,
            power_domain=power_domain,
        )

    def to_dict(self) -> dict:
        output = {
            "path": self.path,
            "type": str(self.type),
            "x": str(self.x),
            "y": str(self.y),
            "width": str(self.width),
            "height": str(self.height)
        }  # type: dict[str, Any]
        if self.orientation is not None:
            output.update({"orientation": self.orientation})
        if self.master is not None:
            output.update({"master": self.master})
        if self.create_physical is not None:
            output.update({"create_physical": self.create_physical})
        if self.margins is not None:
            output.update({"margins": self.margins.to_dict()})
        if self.top_layer is not None:
            output.update({"top_layer": self.top_layer})
        if self.layers is not None:
            output.update({"layers": self.layers})
        if self.obs_types is not None:
            output.update({"obs_types": list(map(str, self.obs_types))})
        if self.power_domain is not None:
            output.update({"power_domain": self.power_domain})
        return output


class MMMCCornerType(Enum):
    Setup = 1
    Hold = 2
    Extra = 3

    @staticmethod
    def from_string(input_str: str) -> "MMMCCornerType":
        if input_str == "setup":  # pylint: disable=no-else-return
            return MMMCCornerType.Setup
        elif input_str == "hold":
            return MMMCCornerType.Hold
        elif input_str == "extra":
            return MMMCCornerType.Extra
        else:
            raise ValueError(f"Invalid MMMC corner type '{input_str}'")


MMMCCorner = NamedTuple('MMMCCorner', [
    ('name', str),
    ('type', MMMCCornerType),
    ('voltage', VoltageValue),
    ('temp', TemperatureValue),
])
