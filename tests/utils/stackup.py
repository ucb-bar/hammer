from decimal import Decimal
from typing import List, Dict, Any

from hammer.tech.stackup import Metal, WidthSpacingTuple, Stackup
from hammer.tech import Site
from hammer.utils import coerce_to_grid


class StackupTestHelper:
    @staticmethod
    def mfr_grid() -> Decimal:
        return Decimal("0.001")

    @staticmethod
    def index_to_min_width_fn(index: int) -> float:
        assert index > 0
        return 0.05 * (1 if (index < 3) else (2 if (index < 5) else 5))

    @staticmethod
    def index_to_min_pitch_fn(index: int) -> float:
        return (StackupTestHelper.index_to_min_width_fn(index) * 9) / 5

    @staticmethod
    def index_to_offset_fn(index: int) -> float:
        return 0.04

    @staticmethod
    def create_wst_list(index: int, grid_unit: Decimal) -> List[WidthSpacingTuple]:
        base_w = StackupTestHelper.index_to_min_width_fn(index)
        base_s = StackupTestHelper.index_to_min_pitch_fn(index) - base_w
        return [WidthSpacingTuple(
            width_at_least=coerce_to_grid(x * base_w * 3, grid_unit),
            min_spacing=coerce_to_grid((x+1) * base_s, grid_unit)
        ) for x in range(5)]

    @staticmethod
    def create_w_tbl(index: int, entries: int, grid_unit: Decimal) -> List[Decimal]:
        """
        Create a width table (power_strap_width_table).
        """
        min_w = StackupTestHelper.index_to_min_width_fn(index)
        raw_widths = list(map(lambda x: min_w*x, range(1, 4 * entries + 1, 4)))
        return [coerce_to_grid(width, grid_unit) for width in raw_widths]

    @staticmethod
    def create_test_metal(index: int, grid_unit: Decimal) -> Metal:
        return Metal(
            name="M{}".format(index),
            index=index,
            direction="vertical" if (index % 2 == 1) else "horizontal",
            min_width=coerce_to_grid(StackupTestHelper.index_to_min_width_fn(index), grid_unit),
            pitch=coerce_to_grid(StackupTestHelper.index_to_min_pitch_fn(index), grid_unit),
            offset=coerce_to_grid(StackupTestHelper.index_to_offset_fn(index), grid_unit),
            power_strap_widths_and_spacings=StackupTestHelper.create_wst_list(index, grid_unit),
            power_strap_width_table=StackupTestHelper.create_w_tbl(index, 1, grid_unit),
            grid_unit=grid_unit
        )

    @staticmethod
    def create_test_stackup(num_metals: int, grid_unit: Decimal) -> Stackup:
        return Stackup(
            grid_unit=grid_unit,
            name="StackupWith{}Metals".format(num_metals),
            metals=[StackupTestHelper.create_test_metal(x+1, grid_unit) for x in range(num_metals)]
        )

    @staticmethod
    def create_test_site(grid_unit: Decimal) -> Site:
        # Make a 9-track horizontal std cell core site
        return Site(
            name="CoreSite",
            y=StackupTestHelper.create_test_metal(1, grid_unit).pitch * 9,
            x=StackupTestHelper.create_test_metal(2, grid_unit).pitch
        )

    @staticmethod
    def create_test_stackup_list() -> List[Stackup]:
        grid_unit = StackupTestHelper.mfr_grid()
        stackups = [StackupTestHelper.create_test_stackup(x, grid_unit) for x in range(5, 8)]
        return stackups
