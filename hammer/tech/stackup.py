#  Data structures to represent technology stackup options.
#
#  See LICENSE for licence details.

from decimal import Decimal
from enum import Enum
from functools import partial
from typing import Any, List, Tuple, Optional

from pydantic import BaseModel, root_validator

from hammer.utils import coerce_to_grid
from hammer.logging import HammerVLSILoggingContext


class RoutingDirection(str, Enum):
    """
    Represents a preferred routing direction for a metal layer.
    Note that this represents a *preferred* direction, not a DRC rule.
    """
    Vertical = "vertical"
    Horizontal = "horizontal"
    Redistribution = "redistribution"

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


class WidthSpacingTuple(BaseModel):
    """
    A tuple of wire width limit and spacing for generating a piecewise linear rule
    for spacing based on wire width.

    width_at_least: Any wires larger than this must obey the minSpacing rule.
    min_spacing: The minimum spacing for this bin.
                 If a wire is wider than multiple entries, the worst-case (larger)
                 minSpacing wins.
    """
    width_at_least: Decimal
    min_spacing: Decimal

    @staticmethod
    def from_setting(grid_unit: Decimal, d: dict) -> "WidthSpacingTuple":
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


class Metal(BaseModel):
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
           for multiple-patterned layers).
    offset: The routing track offset from the origin for the first track in this layer.
            (0 = first track is on an axis).
    power_strap_widths_and_spacings: A list of WidthSpacingTuples that specify the minimum
                                     spacing rules for an infinitely long wire of variying width.
    power_strap_width_table: A list of allowed metal widths in the technology.
                             Widths smaller than the last number must be quantized to a value in the table.
    grid_unit: The fixed-point decimal value of a minimum grid unit (e.g. 1nm = 0.001).
               For most technologies, this comes from the technology plugin and is the same for all layers.
    """
    name: str
    index: int
    direction: RoutingDirection
    min_width: Decimal
    max_width: Optional[Decimal]
    pitch: Decimal
    offset: Decimal
    power_strap_widths_and_spacings: List[WidthSpacingTuple]
    power_strap_width_table: List[Decimal] = []
    # Note: grid_unit is not currently parsed as part of the Metal data structure!
    # See #379
    grid_unit: Decimal

    class Config:
        use_enum_values = True

    @root_validator(pre=True)
    def widths_must_snap_to_grid(cls, values):
        grid_unit = Decimal(str(values.get("grid_unit")))
        for field in ["min_width", "pitch", "offset"]:
            raw_value = Decimal(str(values.get(field)))
            snapped_value = coerce_to_grid(raw_value, grid_unit)
            if raw_value != snapped_value:
                raise ValueError(f"{field} ({raw_value}) is not aligned to the grid_unit ({grid_unit})")
        if values.get("power_strap_width_table"):
            for width in values.get("power_strap_width_table"):
                width = Decimal(str(width))
                snapped_width = coerce_to_grid(width, grid_unit)
                if width != snapped_width:
                    raise ValueError(f"Width {width} in power_strap_width_table is not aligned to the grid_unit ({grid_unit})")
        if values.get("max_width") is not None:
            max_width = Decimal(str(values.get("max_width")))
            snapped_width = coerce_to_grid(max_width, grid_unit)
            if max_width != snapped_width:
                raise ValueError(f"max_width {max_width} is not aligned to the grid unit ({grid_unit})")
        return values

    @staticmethod
    def from_setting(grid_unit: Decimal, d: dict) -> "Metal":
        """
        Return a Metal object from a dict with keys "name", "index", "direction", "min_width", "max_width", "pitch", "offset", "power_strap_widths_and_spacings", and "power_strap_width_table"

        :param grid_unit: The manufacturing grid unit in um
        :param d: A dict containing the keys "name", "index", "direction", "min_width", "max_width", "pitch", "offset", "power_strap_widths_and_spacings", and "power_strap_width_table"
        """
        return Metal(
            grid_unit=grid_unit,
            name=str(d["name"]),
            index=int(d["index"]),
            direction=RoutingDirection(d["direction"]),
            min_width=coerce_to_grid(d["min_width"], grid_unit),
            max_width=coerce_to_grid(d["max_width"], grid_unit) if "max_width" in d and d["max_width"] is not None else None,
            pitch=coerce_to_grid(d["pitch"], grid_unit),
            offset=coerce_to_grid(d["offset"], grid_unit),
            power_strap_widths_and_spacings=WidthSpacingTuple.from_list(grid_unit, d["power_strap_widths_and_spacings"]),
            power_strap_width_table=Metal.power_strap_widths_from_list(grid_unit, d["power_strap_width_table"] if "power_strap_width_table" in d and d["power_strap_width_table"] else [])
        )

    @staticmethod
    def power_strap_widths_from_list(grid_unit: Decimal, l: List[Any]) -> List[Decimal]:
        """
        Read and cocerce wire widths from the technology LEF width table.
        """
        return sorted(map(lambda w: coerce_to_grid(w, grid_unit), map(float, l)))

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
        if self.max_width and self.max_width > 0.0 and width > self.max_width:
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

    def quantize_to_width_table(self, width: Decimal, layer: str, logger: Optional[HammerVLSILoggingContext]) -> Decimal:
        """
        Compare a desired width to the width table, if specified for a technology.
        Will return the allowable width smaller than or equal to the desired width,
        except if the desired width is greater than or equal to the last width in the width table.
        Issues a logger warning for the user if the returned width was quantized.
        """
        width_table = self.power_strap_width_table
        if len(width_table) == 0:
            qwidth = width
        else:
            for i, w in enumerate(width_table):
                if width > w:
                    # The last entry in table is special: width can be greater
                    # than or equal to this number.
                    if i == len(width_table) - 1:
                        qwidth = width
                        break
                    else:
                        continue
                elif width == w:
                    qwidth = w
                    break
                else:
                    if logger is not None:
                        logger.warning("The desired power strap width {dw} on {lay} was quantized down to {fw} based on the technology's width table. Please check your power grid.".format(dw=str(width), lay=layer, fw=str(width_table[i-1])))
                    qwidth = width_table[i-1]
                    break
        return qwidth

    def get_width_spacing_start_twt(self,
                                    tracks: int,
                                    logger: Optional[HammerVLSILoggingContext]
                                   ) -> Tuple[Decimal, Decimal, Decimal]:
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
        if self.max_width and self.max_width > 0.0 and width > self.max_width:
            width = self.max_width
            spacing = (s2w - width) / 2

        assert int(self.min_width / self.grid_unit) % 2 == 0, (
            "Assuming all min widths are even here, if not fix me")
        assert int(width / self.grid_unit) % 2 == 0, (
            "This calculation should always produce an even width")
        start = self.min_width / 2 + spacing
        return (self.quantize_to_width_table(width, self.name, logger), spacing, start)

    def get_width_spacing_start_twwt(self, tracks: int, logger: Optional[HammerVLSILoggingContext], force_even: bool = False) -> Tuple[Decimal, Decimal, Decimal]:
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
        if self.max_width and self.max_width > 0.0 and width > self.max_width:
            # If we cannot maximize width, set it to max_width
            width = self.max_width
            spacing = (s3w2 - width * 2) / 3

        assert int(self.min_width / self.grid_unit) % 2 == 0, "Assuming all min widths are even here, if not fix me"
        start = self.min_width / 2 + spacing
        if force_even and int(width / self.grid_unit) % 2 == 1:
            width = width - self.grid_unit
            start = start + self.grid_unit
        return (self.quantize_to_width_table(width, self.name, logger), spacing, start)

    # TODO implement M W X* W M style wires, where X is slightly narrower
    # than W and centered on-grid.


class Stackup(BaseModel):
    """
    A stackup is a list of metals with a meaningful keyword name (for now).

    TODO: add vias, etc when we need them
    """
    grid_unit: Decimal
    name: str
    metals: List[Metal]

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
