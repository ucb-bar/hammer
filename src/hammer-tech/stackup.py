#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  stackup.py
#  Data structures to represent technology stackup options
#
#  See LICENSE for licence details.

from enum import Enum
from typing import Any, Callable, Iterable, List, NamedTuple, Optional, Tuple, Dict
from hammer_utils import reverse_dict

class RoutingDirection(Enum):
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
        try:
            return RoutingDirection.__mapping()[input_str]
        except KeyError:
            raise ValueError("Invalid routing direction: " + str(input_str))

    def __str__(self) -> str:
        return reverse_dict(RoutingDirection.__mapping())[self]

    def opposite(self) -> "RoutingDirection":
        if self == RoutingDirection.Vertical:
            return RoutingDirection.Horizontal
        elif self == RoutingDirection.Horizontal:
            return RoutingDirection.Vertical
        else:
            return self

# Note to maintainers: This is mirrored in schema.json- don't change one without the other

# A tuple of wire width limit and spacing for generating a piecewise linear rule for spacing based on wire width
# width_at_least: Any wires larger than this must obey the minSpacing rule
# min_spacing: The minimum spacing for this bin. If a wire is wider than multiple entries, the worst-case (larger) minSpacing wins.
class WidthSpacingTuple(NamedTuple('WidthSpacingTuple', [
    ('width_at_least', float),
    ('min_spacing', float)
])):
    __slots__ = ()

    @staticmethod
    def from_setting(d: dict) -> "WidthSpacingTuple":
        w = float(d["width_at_least"])
        s = float(d["min_spacing"])
        assert w >= 0.0
        assert s > 0.0
        return WidthSpacingTuple(
            width_at_least=w,
            min_spacing=s
        )

    @staticmethod
    def from_list(l: List[dict]) -> List["WidthSpacingTuple"]:
        out = sorted(list(map(lambda x: WidthSpacingTuple.from_setting(x), l)), key=lambda x: x.width_at_least)
        s = 0.0
        for wst in out:
            assert wst.min_spacing >= s
            s = wst.min_spacing
        return out


# A metal layer and some basic info about it
# name: M1, M2, etc.
# index: The order in the stackup (lower is closer to the substrate)
# direction: The preferred routing direction of this metal layer, or "redistribution" for non-routing top-level redistribution metals like Aluminum
# min_width: The minimum wire width for this layer
# pitch: The minimum cross-mask pitch for this layer (NOT same-mask pitch for multiply-patterned layers)
# offset: The routing track offset from the origin for the first track in this layer (0 = first track is on an axis)
# power_strap_widths_and_spacings: A list of WidthSpacingTuples that specify the minimum spacing rules for an infinitely long wire of variying width
class Metal(NamedTuple('Metal', [
    ('name', str),
    ('index', int),
    ('direction', "RoutingDirection"),
    ('min_width', float),
    ('pitch', float),
    ('offset', float),
    ('power_strap_widths_and_spacings', List[WidthSpacingTuple])
])):
    __slots__ = ()

    # TODO this is assuming that a manufacturing grid is 0.001
    def grid_unit(self) -> float:
        return 0.001

    # TODO internally represent numbers as integers or fixed-point to obviate the need for this
    # ucb-bar/hammer#319
    def snap(self, x: float) -> float:
        return float(round(x / self.grid_unit())) * self.grid_unit()

    @staticmethod
    def from_setting(d: dict) -> "Metal":
        return Metal(
            name=str(d["name"]),
            index=int(d["index"]),
            direction=RoutingDirection.from_str(d["direction"]),
            min_width=float(d["min_width"]),
            pitch=float(d["pitch"]),
            offset=float(d["offset"]),
            power_strap_widths_and_spacings=WidthSpacingTuple.from_list(d["power_strap_widths_and_spacings"])
        )

    # Get the minimum spacing for a provided width
    def get_spacing_for_width(self, width: float) -> float:
        spacing = 0.0
        for wst in self.power_strap_widths_and_spacings:
            if width >= wst.width_at_least:
                spacing = max(spacing, wst.min_spacing)
            else:
                # The list is sorted so we can early-out
                return spacing
        return spacing

    # Derive the minimum spacing for a maximally-sized wire given a desired pitch.
    # Use this when the wire width is unknown, but you know the pitch.
    # This calculation essentially plots the wire width on the X axis and the minimum pitch on the Y axis.
    # You'll see discontinuites at the width-spacing table entries. If the desired pitch falls on a sloped
    # line (i.e. > min width for entry N but less than min width for entry N+1), pick that spacing. If
    # the desired pitch falls on a vertical line, pick the maximum width entry for N, which is the
    # entry for N+1 minus delta (2 grid units), and then the spacing will be larger than the min spacing.
    def min_spacing_from_pitch(self, pitch: float) -> float:
        ws = self.power_strap_widths_and_spacings
        spacing = ws[0].min_spacing
        for first, second in zip(ws[:-1], ws[1:]):
            if pitch >= (second.min_spacing + second.width_at_least):
                spacing = second.min_spacing
            elif pitch >= (first.min_spacing + second.width_at_least):
                # we are asking for a pitch that is width-constrained
                width = self.snap(second.width_at_least - (self.grid_unit()*2))
                spacing = self.snap(pitch - width)
        return spacing

    # This method will return the maximum width a wire can be to consume a given number of routing tracks.
    # This assumes the neighbors of the wide wire are minimum-width routes.
    # i.e. T W T
    # T = thin / min-width
    # W = wide
    # Returns width, spacing and start
    # See min_spacing_from_pitch documentation for an explanation of the calculation.
    def get_width_spacing_start_twt(self, tracks: int) -> Tuple[float, float, float]:
        ws = self.power_strap_widths_and_spacings
        spacing = ws[0].min_spacing
        # the T W T pattern contains one wires (W) and 2 spaces (S2)
        s2w = self.snap((tracks + 1) * self.pitch - self.min_width)
        width = self.snap(s2w - spacing*2)
        for first, second in zip(ws[:-1], ws[1:]):
            if s2w >= (second.min_spacing*2 + second.width_at_least):
                spacing = second.min_spacing
                width = self.snap(s2w - spacing*2)
            elif s2w >= (first.min_spacing*2 + second.width_at_least):
                # we are asking for a pitch that is width-constrained
                width = self.snap(second.width_at_least - (self.grid_unit()*2))
                spacing = self.snap((s2w - width)/2.0)
        assert (int(self.min_width / self.grid_unit()) % 2 == 0), "Assuming all min widths are even here, if not fix me"
        assert (int(width / self.grid_unit()) % 2 == 0), "This calculation should always produce an even width"
        start = self.snap(self.min_width/2.0 + spacing)
        return (width, spacing, start)

    # This method will return the maximum width a wire can be to consume a given number of routing tracks
    # This assumes one neighbor is a min width wire, and the other is the same size as this (mirrored)
    # i.e. T W W T
    # T = thin / min-width
    # W = wide
    # Returns width, spacing, and start
    # See min_spacing_from_pitch documentation for an explanation of the calculation
    # force_even: True to force the strap width to be an even multiple of the grid unit
    def get_width_spacing_start_twwt(self, tracks: int, force_even: bool = False) -> Tuple[float, float, float]:
        ws = self.power_strap_widths_and_spacings
        spacing = ws[0].min_spacing
        # the T W W T pattern contains two wires (W2) and 3 spaces (S3)
        s3w2 = self.snap(((2*tracks) + 1) * self.pitch - self.min_width)
        width = self.snap((s3w2 - spacing*3)/2.0)
        for first, second in zip(ws[:-1], ws[1:]):
            if s3w2 >= (second.min_spacing*3 + second.width_at_least*2):
                spacing = second.min_spacing
                width = self.snap((s3w2 - spacing*3)/2.0)
            elif s3w2 >= (first.min_spacing*3 + second.width_at_least*2):
                # we are asking for a pitch that is width-constrained
                width = self.snap(second.width_at_least - (self.grid_unit()*1))
                spacing = self.snap((s3w2 - width*2)/3.0)
        assert (int(self.min_width / self.grid_unit()) % 2 == 0), "Assuming all min widths are even here, if not fix me"
        start = self.snap(self.min_width/2.0 + spacing)
        if force_even and (int(width / self.grid_unit()) % 2 == 1):
            width = self.snap(width - self.grid_unit())
            start = self.snap(start + self.grid_unit())
        return (width, spacing, start)

    # TODO implement M W X* W M style wires, where X is slightly narrower than W and centered on-grid

# For now a stackup is just a list of metals with a meaningful keyword name
# TODO add vias, etc. when we need them
class Stackup(NamedTuple('Stackup', [
    ('name', str),
    ('metals', List[Metal])
])):
    __slots__ = ()

    @staticmethod
    def from_setting(d: dict) -> "Stackup":
        return Stackup(
            name=str(d["name"]),
            metals=list(map(lambda x: Metal.from_setting(x), list(d["metals"])))
        )


    def get_metal(self, name: str) -> "Metal":
        for m in self.metals:
            if m.name == name:
                return m
        raise ValueError("Metal named %s is not defined in stackup %s" % (name, self.name))

