#  units.py
#  Unit classes/functions for hammer_vlsi.
#
#  See LICENSE for licence details.

from abc import abstractmethod
import sys
try:
    from abc import ABC  # pylint: disable=ungrouped-imports
except ImportError:
    if sys.version_info.major == 3 and sys.version_info.minor < 4:
        # Python compatibility: 3.3
        # Python 3.3 and below don't have abc.ABC
        import abc  # pylint: disable=ungrouped-imports
        ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})  # type: ignore

from typing import Optional, TypeVar

from hammer.utils import get_or_else

_TT = TypeVar('_TT', bound='ValueWithUnit')

class ValueWithUnit(ABC):
    """Represents some particular value that has units (e.g. "10 ns", "2000 um", "25 C", etc).
    """

    # From https://stackoverflow.com/a/10970888
    _prefix_table = {
        'y': 1e-24,  # yocto
        'z': 1e-21,  # zepto
        'a': 1e-18,  # atto
        'f': 1e-15,  # femto
        'p': 1e-12,  # pico
        'n': 1e-9,  # nano
        'u': 1e-6,  # micro
        'm': 1e-3,  # milli
        'c': 1e-2,  # centi
        'd': 1e-1,  # deci
        '':  1,    # <no prefix>
        'k': 1e3,  # kilo
        'M': 1e6,  # mega
        'G': 1e9,  # giga
        'T': 1e12,  # tera
        'P': 1e15,  # peta
        'E': 1e18,  # exa
        'Z': 1e21,  # zetta
        'Y': 1e24,  # yotta
    }

    @property
    @abstractmethod
    def unit(self) -> str:
        """Get the base unit for values (e.g. "s", "m", "V", etc).
        Meant to be overridden by subclasses."""

    @property
    @abstractmethod
    def unit_type(self) -> str:
        """Get the base unit type for values. (e.g. for "s", this would be "time")
        Meant to be overridden by subclasses."""

    @property
    @abstractmethod
    def default_prefix(self) -> str:
        """Get the default prefix for values.
        (e.g. for time, specifying "n" would mean "0.25" would be interpreted as "0.25 ns".)
        Meant to be overridden by subclasses."""

    def __init__(self, value: str, prefix: Optional[str] = None) -> None:
        """
        Create a value from parsing the given string.
        :param value: Value encoded in the given string.
        :param prefix: If value does not have a prefix (e.g. "0.25"), then use
                       the given prefix, or the default prefix defined by the
                       class if one is not specified.
        """
        import re

        default_prefix = get_or_else(prefix, self.default_prefix)

        regex = r"^(-?[\d.]+) *(.*){}$".format(re.escape(self.unit))
        match = re.search(regex, value)
        if match is None:
            try:
                num = str(float(value))
                self._value_prefix = default_prefix
            except ValueError:
                raise ValueError("Malformed {type} value {value}".format(type=self.unit_type,
                                                                         value=value))
        else:
            num = match.group(1)
            self._value_prefix = match.group(2)

        if num.count('.') > 1 or len(self._value_prefix) > 1:
            raise ValueError("Malformed {type} value {value}".format(type=self.unit_type,
                                                                     value=value))

        if self._value_prefix not in self._prefix_table:
            raise ValueError("Bad prefix for {value}".format(value=value))

        self._value = float(num)  # type: float
        # Preserve the prefix too to preserve precision
        self._prefix = self._prefix_table[self._value_prefix]  # type: float

    @property
    def value_prefix(self) -> str:
        """Get the prefix string of this value."""
        return self._value_prefix

    @property
    def value(self) -> float:
        """Get the actual value of this value. (e.g. 10 ns -> 1e-9)"""
        return self._value * self._prefix

    def value_in_units(self, prefix: str, round_zeroes: bool = True) -> float:
        """Get this value in the given prefix. e.g. "ns", "mV", etc.
        """
        # e.g. extract "n" from "ns" or blank if it's blank (e.g. "V" -> "")
        letter_prefix = ""
        if prefix != self.unit:
            letter_prefix = "" if prefix == "" else prefix[0]

        retval = self._value * (self._prefix / self._prefix_table[letter_prefix])
        if round_zeroes:  # pylint: disable=no-else-return
            return round(retval, 3)
        else:
            return retval

    def str_value_in_units(self, prefix: str, round_zeroes: bool = True) -> str:
        """Get this value in the given prefix but including the units.
        e.g. return "5 ns".

        :param prefix: Prefix for the resulting value - e.g. "ns".
        :param round_zeroes: True to round 1.00000001 etc to 1 within 3 decimal places.
        """
        # %g removes trailing zeroes
        return "%g" % (self.value_in_units(prefix, round_zeroes)) + " " + prefix

    # Comparison operators.
    # Note that mypy doesn't properly support type checking on equality
    # operators so the type of __eq__ is object :(
    # As a result, the operators' (e.g. __eq__) 'other' type can't be _TT.
    # Therefore, we implement the operators themselves separately and then wrap
    # them in the special operators.
    # See https://github.com/python/mypy/issues/1271
    # Disable useless pylint checks for the following methods.
    # pylint: disable=unidiomatic-typecheck

    def eq(self: _TT, other: _TT) -> bool:  # pylint: disable=invalid-name
        """
        Compare equality of this value with another.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return self.value_in_units(self.default_prefix) == other.value_in_units(self.default_prefix)

    def __eq__(self: _TT, other: object) -> bool:
        """
        Compare equality of this value with another.
        The types must match.
        """
        return self.eq(other)  # type: ignore

    def ne(self: _TT, other: _TT) -> bool:  # pylint: disable=invalid-name
        """
        Compare inequality of this value with another.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return not self.eq(other)

    def __ne__(self: _TT, other: object) -> bool:
        """
        Compare inequality of this value with another.
        The types must match.
        """
        return self.ne(other)  # type: ignore

    def __lt__(self: _TT, other: _TT) -> bool:
        """
        Check if self is less than other.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return self.value < other.value

    def __le__(self: _TT, other: _TT) -> bool:
        """
        Check if self is less than or equal to other.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return self.value <= other.value

    def __gt__(self: _TT, other: _TT) -> bool:
        """
        Check if self is greater than other.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return self.value > other.value

    def __ge__(self: _TT, other: _TT) -> bool:
        """
        Check if self is greater than or equal to other.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return self.value >= other.value

    def __add__(self: _TT, other: _TT) -> _TT:
        """
        Add other and self.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return type(self)(str(self.value + other.value),"")

    def __sub__(self: _TT, other: _TT) -> _TT:
        """
        Subtract other from self.
        The types must match.
        """
        if type(self) != type(other):
            raise TypeError("Types do not match")
        return type(self)(str(self.value - other.value),"")

    def __div__(self: _TT, other: float) -> _TT:
        """
        Divide self by a float or an integer.
        """
        raise NotImplementedError()

    # Some python nonsense
    def __truediv__(self: _TT, other: float) -> _TT:
        return type(self)(str(self.value / other),"")

    def __mul__(self: _TT, other: float) -> _TT:
        """
        Multiply self by a float or an integer.
        """
        return type(self)(str(self.value * other),"")


class TimeValue(ValueWithUnit):
    """Time value - e.g. "4 ns".
    Parses time values from strings.
    """

    @property
    def default_prefix(self) -> str:
        """Default prefix: ns"""
        return "n"

    @property
    def unit(self) -> str:
        return "s"

    @property
    def unit_type(self) -> str:
        return "time"


class VoltageValue(ValueWithUnit):
    """Voltage value - e.g. "0.95 V", "950 mV".
    """

    @property
    def default_prefix(self) -> str:
        """Default is plain volts (e.g. "0.1" -> 0.1 V)."""
        return ""

    @property
    def unit(self) -> str:
        return "V"

    @property
    def unit_type(self) -> str:
        return "voltage"


class TemperatureValue(ValueWithUnit):
    """Temperature value in Celsius - e.g. "25 C", "125 C".
    Mainly used for specifying corners for MMMC.
    """

    @property
    def default_prefix(self) -> str:
        """Default is plain degrees Celsius (e.g. "25" -> "25 C")."""
        return ""

    @property
    def unit(self) -> str:
        return "C"

    @property
    def unit_type(self) -> str:
        return "voltage"


class CapacitanceValue(ValueWithUnit):
    """Capacitance value - e.g. "5 fF", "10 nF".
    """

    @property
    def default_prefix(self) -> str:
        """Default prefix: fF"""
        return "f"

    @property
    def unit(self) -> str:
        return "F"

    @property
    def unit_type(self) -> str:
        return "capacitance"
