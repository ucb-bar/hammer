#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  units.py
#  Unit classes/functions for hammer_vlsi.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from abc import ABC, abstractmethod


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
        'm': 1e-3,  # mili
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

    def __init__(self, value: str, default_prefix: str = 'n') -> None:
        """Create a time value from parsing the given string.
        Default prefix: n- (e.g. "ns", "nV", etc)
        """
        import re

        regex = r"^([\d.]+) *(.*){}$".format(re.escape(self.unit))
        m = re.search(regex, value)
        if m is None:
            try:
                num = str(float(value))
                prefix = default_prefix
            except ValueError:
                raise ValueError("Malformed {type} value {value}".format(type=self.unit_type, value=value))
        else:
            num = m.group(1)
            prefix = m.group(2)

        if num.count('.') > 1 or len(prefix) > 1:
            raise ValueError("Malformed {type} value {value}".format(type=self.unit_type, value=value))

        if prefix not in self._prefix_table:
            raise ValueError("Bad prefix for {value}".format(value=value))

        self._value = float(num)  # type: float
        # Preserve the prefix too to preserve precision
        self._prefix = self._prefix_table[prefix]  # type: float

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
        if round_zeroes:
            return round(retval, 2)
        else:
            return retval

    def str_value_in_units(self, prefix: str, round_zeroes: bool = True) -> str:
        """Get this value in the given prefix but including the units.
        e.g. return "5 ns".

        :param prefix: Prefix for the resulting value - e.g. "ns".
        :param round_zeroes: True to round 1.00000001 etc to 1 within 2 decimal places.
        """
        # %g removes trailing zeroes
        return "%g" % (self.value_in_units(prefix, round_zeroes)) + " " + prefix


class TimeValue(ValueWithUnit):
    """Time value - e.g. "4 ns".
    Parses time values from strings.
    """

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
    def unit(self) -> str:
        return "C"

    @property
    def unit_type(self) -> str:
        return "voltage"
