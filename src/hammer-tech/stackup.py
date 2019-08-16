#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  stackup.py
#  Data structures to represent technology stackup options.
#
#  See LICENSE for licence details.

from enum import Enum
from typing import List, NamedTuple, Tuple, Dict
from hammer_utils import reverse_dict, coerce_to_grid
from decimal import Decimal
from functools import partial

class RoutingDirection(Enum):
    """
    Represents a preferred routing direction for a metal layer.
    Note that this represents a *preferred* direction, not a DRC rule.
    """

    Vertical = 1
    Horizontal = 2
    Redistribution = 3

    @classmethod
    def __mapping(cls) -> Dict[str, "RoutingDirection"]:
        return {
            "vertical": RoutingDirection.Vertical,
            "horizontal": RoutingDirection.Horizontal,
            "redistribution": RoutingDirection.Redistribution
        }

    @staticmethod
    def from_str(input_str: str) -> "RoutingDirection":
        # pylint: disable=missing-docstring
        try:
            return RoutingDirection.__mapping()[input_str]
        except KeyError:
            raise ValueError("Invalid routing direction: " + str(input_str))

    def __str__(self) -> str:
        return reverse_dict(RoutingDirection.__mapping())[self]

    def opposite(self) -> "RoutingDirection":
        """
        Return the opposite routing direction.
        For Redistribution, this returns itself.
        :return: Opposite routing direction
        """
        if self == RoutingDirection.Vertical:
            return RoutingDirection.Horizontal
        elif self == RoutingDirection.Horizontal:
            return RoutingDirection.Vertical
        else:
            return self


class WidthSpacingTuple(NamedTuple('WidthSpacingTuple', [
        ('width_at_least', Decimal),
        ('min_spacing', Decimal)
])):
    """
    A tuple of wire width limit and spacing for generating a piecewise linear rule
    for spacing based on wire width.

    width_at_least: Any wires larger than this must obey the minSpacing rule.
    min_spacing: The minimum spacing for this bin.
                 If a wire is wider than multiple entries, the worst-case (larger)
                 minSpacing wins.

    Note to maintainers: This is mirrored in schema.json - don't change one without the other!
    """
    __slots__ = ()

    @staticmethod
    def from_setting(grid_unit: Decimal, d: dict) -> "WidthSpacingTuple":
        # pylint: disable=missing-docstring
        width_at_least = coerce_to_grid(d["width_at_least"], grid_unit)
        min_spacing = coerce_to_grid(d["min_spacing"], grid_unit)
        assert width_at_least >= 0
        assert min_spacing > 0
        return WidthSpacingTuple(
            width_at_least=width_at_least,
            min_spacing=min_spacing
        )


    @staticmethod
    def from_list(grid_unit: Decimal, l: List[dict]) -> List["WidthSpacingTuple"]:
        out = sorted(list(map(partial(WidthSpacingTuple.from_setting, grid_unit), l)), key=lambda x: x.width_at_least)

        # Check that spacings increase.
        current_spacing = Decimal(0)
        for wst in out:
            assert wst.min_spacing >= current_spacing
            current_spacing = wst.min_spacing
        return out


class Metal(NamedTuple('Metal', [
        ('name', str),
        ('index', int),
        ('direction', RoutingDirection),
        ('min_width', Decimal),
        ('max_width', Decimal),
        ('pitch', Decimal),
        ('offset', Decimal),
        ('power_strap_widths_and_spacings', List[WidthSpacingTuple]),
        # Note: grid_unit is not currently parsed as part of the Metal data structure!
        # See #379
        ('grid_unit', Decimal)
])):
    """
    A metal layer and some basic info about it.

    name: Metal layer name (e.g. M1, M2).
    index: The order in the stackup (lower is closer to the substrate).
    direction: The preferred routing direction of this metal layer, or
               RoutingDirection.Redistribution for non-routing top-level
               redistribution metals like Aluminium.
    min_width: The minimum wire width for this layer.
    max_width: The maximum wire width for this layer.
    pitch: The minimum cross-mask pitch for this layer (NOT same-mask pitch
           for multiply-patterned layers).
    offset: The routing track offset from the origin for the first track in this layer.
            (0 = first track is on an axis).
    power_strap_widths_and_spacings: A list of WidthSpacingTuples that specify the minimum
                                     spacing rules for an infinitely long wire of variying width.
    grid_unit: The fixed-point decimal value of a minimum grid unit (e.g. 1nm = 0.001).
               For most technologies, this comes from the technology plugin and is the same for all layers.
    """
    __slots__ = ()

    @staticmethod
    def from_setting(grid_unit: Decimal, d: dict) -> "Metal":
        """
        Return a Metal object from a dict with keys "name", "index", "direction", "min_width", "max_width", "pitch", "offset", and "power_strap_widths_and_spacings"

        :param grid_unit: The manufacturing grid unit in um
        :param d: A dict containing the keys "name", "index", "direction", "min_width", "max_width", "pitch", "offset", and "power_strap_widths_and_spacings"
        """
        return Metal(
            grid_unit=grid_unit,
            name=str(d["name"]),
            index=int(d["index"]),
            direction=RoutingDirection.from_str(d["direction"]),
            min_width=coerce_to_grid(d["min_width"], grid_unit),
            max_width=coerce_to_grid(d["max_width"], grid_unit),
            pitch=coerce_to_grid(d["pitch"], grid_unit),
            offset=coerce_to_grid(d["offset"], grid_unit),
            power_strap_widths_and_spacings=WidthSpacingTuple.from_list(grid_unit, d["power_strap_widths_and_spacings"])
        )

    def get_spacing_for_width(self, width: Decimal) -> Decimal:
        """
        Get the minimum spacing for a provided width.

        :param width: Width to calculate minimum spacing for.
        :return: Minimum spacing for `width`
        """
        spacing = Decimal(0)
        for wst in self.power_strap_widths_and_spacings:
            if width >= wst.width_at_least:
                spacing = max(spacing, wst.min_spacing)
            else:
                # The list is sorted so we can early-out
                return spacing
        return spacing

    def min_spacing_and_max_width_from_pitch(self, pitch: Decimal) -> Tuple[Decimal, Decimal]:
        """
        Derive the minimum spacing and maximally-sized wire for a
        desired pitch.

        Use this when the wire width is unknown, but you know the pitch.
        This calculation essentially plots the wire width on the X axis
        and the minimum pitch on the Y axis.

        You'll see discontinuites at the width-spacing table entries.
        If the desired pitch falls on a sloped line (i.e. > min width for
        entry N but less than min width for entry N+1), pick that spacing.
        If the desired pitch falls on a vertical line, pick the maximum width
        entry for N, which is the entry for N+1 minus delta (2 grid units),
        and then the spacing will be larger than the min spacing.

        :param pitch: Desired pitch
        :return: Tuple of (minimum spacing, maximally-sized wire)
        """
        widths_and_spacings = self.power_strap_widths_and_spacings
        spacing = widths_and_spacings[0].min_spacing
        for first, second in zip(widths_and_spacings[:-1], widths_and_spacings[1:]):
            if pitch >= (second.min_spacing + second.width_at_least):
                spacing = second.min_spacing
            elif pitch >= (first.min_spacing + second.width_at_least):
                # we are asking for a pitch that is width-constrained
                width = second.width_at_least - (self.grid_unit*2)
                spacing = pitch - width

        width = pitch - spacing
        if self.max_width > 0.0 and width > self.max_width:
            width = self.max_width
        if width < 0:
            raise ValueError("Desired pitch {pitch} is illegal".format(pitch=pitch))
        return spacing, pitch - spacing

    def min_spacing_from_pitch(self, pitch: Decimal) -> Decimal:
        """
        Derive the minimum spacing for a maximally-sized wire given a
        desired pitch.
        See min_spacing_and_max_width_from_pitch for details.

        :param pitch: Desired pitch
        :return: Minimum spacing for said pitch.
        """
        return self.min_spacing_and_max_width_from_pitch(pitch)[0]

    def max_width_from_pitch(self, pitch: Decimal) -> Decimal:
        """
        Derive the maximum wire width for a maximally-sized wire given a
        desired pitch.
        See min_spacing_and_max_width_from_pitch for details.

        :param pitch: Desired pitch
        :return: Maximum wire width for said pitch.
        """
        return self.min_spacing_and_max_width_from_pitch(pitch)[1]

    def get_width_spacing_start_twt(self, tracks: int) -> Tuple[Decimal, Decimal, Decimal]:
        """
        This method will return the maximum width a wire can be in order
        to consume a given number of routing tracks.
        This assumes the neighbors of the wide wire are minimum-width routes.
        i.e. T W T
        T = thin / min-width
        W = wide
        See min_spacing_and_max_width_from_pitch for an explanation of the calculation.

        :param tracks: Number of routing tracks to consume
        :return: Returns tuple of (width, spacing, start)
        """
        widths_and_spacings = self.power_strap_widths_and_spacings
        spacing = widths_and_spacings[0].min_spacing
        # the T W T pattern contains one wires (W) and 2 spaces (S2)
        s2w = (tracks + 1) * self.pitch - self.min_width

        assert int(s2w / self.grid_unit) % 2 == 0, "This calculation should always produce an even s2w"

        width = s2w - spacing*2
        for first, second in zip(widths_and_spacings[:-1], widths_and_spacings[1:]):
            if s2w >= second.min_spacing * 2 + second.width_at_least:
                spacing = second.min_spacing
                width = s2w - spacing * 2
            elif s2w >= first.min_spacing * 2 + second.width_at_least:
                # we are asking for a pitch that is width-constrained
                if int(second.width_at_least / self.grid_unit) % 2 == 0:
                    # even
                    width = second.width_at_least - (self.grid_unit * 2)
                else:
                    # odd
                    width = second.width_at_least - self.grid_unit
                spacing = (s2w - width) / 2
        if self.max_width > 0.0 and width > self.max_width:
            width = self.max_width
            spacing = (s2w - width) / 2

        assert int(self.min_width / self.grid_unit) % 2 == 0, (
            "Assuming all min widths are even here, if not fix me")
        assert int(width / self.grid_unit) % 2 == 0, (
            "This calculation should always produce an even width")
        start = self.min_width / 2 + spacing
        return (width, spacing, start)

    def get_width_spacing_start_twwt(self, tracks: int, force_even: bool = False) -> Tuple[Decimal, Decimal, Decimal]:
        """
        This method will return the maximum width a wire can be in order
        to consume a given number of routing tracks.
        This assumes that the wires are in the following configuration.
        i.e. T W W T
        T = thin / min-width
        W = wide
        See min_spacing_and_max_width_from_pitch for an explanation of the calculation.

        :param tracks: Number of routing tracks to consume
        :param force_even: Forces the width of the wire to be an even multiple of the unit grid
        :return: Returns tuple of (width, spacing, start)
        """
        widths_and_spacings = self.power_strap_widths_and_spacings
        spacing = widths_and_spacings[0].min_spacing
        assert self.pitch - self.min_width == spacing, "Tech plugin is malformed for metal {}, the minimum spacing in the width-spacing list must be the same as (pitch - min_width).".format(self.name)
        # the T W W T pattern contains two wires (W2) and 3 spaces (S3)
        s3w2 = ((2 * tracks) + 1) * self.pitch - self.min_width
        width = (s3w2 - spacing * 3) / 2
        for first, second in zip(widths_and_spacings[:-1], widths_and_spacings[1:]):
            if s3w2 >= second.min_spacing * 3 + second.width_at_least * 2:
                spacing = second.min_spacing
                width = (s3w2 - spacing * 3) / 2
            elif s3w2 >= first.min_spacing * 3 + second.width_at_least * 2:
                # we are asking for a pitch that is width-constrained
                width = second.width_at_least - (self.grid_unit * 1)
                spacing = (s3w2 - width * 2) / 3
        if self.max_width > 0.0 and width > self.max_width:
            # If we cannot maximize width, set it to max_width
            width = self.max_width
            spacing = (s3w2 - width * 2) / 3

        assert int(self.min_width / self.grid_unit) % 2 == 0, "Assuming all min widths are even here, if not fix me"
        start = self.min_width / 2 + spacing
        if force_even and int(width / self.grid_unit) % 2 == 1:
            width = width - self.grid_unit
            start = start + self.grid_unit
        return (width, spacing, start)

    # TODO implement M W X* W M style wires, where X is slightly narrower than W and centered on-grid


class Stackup(NamedTuple('Stackup', [
        ('grid_unit', Decimal),
        ('name', str),
        ('metals', List[Metal])
])):
    """
    A stackup is a list of metals with a meaningful keyword name (for now).

    TODO: add vias, etc when we need them
    """
    __slots__ = ()

    @staticmethod
    def from_setting(grid_unit: Decimal, d: dict) -> "Stackup":
        # pylint: disable=missing-docstring
        return Stackup(
            grid_unit=grid_unit,
            name=str(d["name"]),
            metals=list(map(lambda x: Metal.from_setting(grid_unit, x), list(d["metals"])))
        )

    def get_metal(self, name: str) -> Metal:
        """
        Get a given metal layer by name.

        :param name: Name of the metal layer
        :return: A metal layer object
        """
        for m in self.metals:
            if m.name == name:
                return m
        raise ValueError("Metal named %s is not defined in stackup %s" % (name, self.name))

    def get_metal_by_index(self, index: int) -> Metal:
        """
        Get a given metal layer by index.

        :param index: Index of the metal layer
        :return: A metal layer object
        """
        for m in self.metals:
            if m.index == index:
                return m
        raise ValueError("Metal with index %d is not defined in stackup %s" % (index, self.name))
