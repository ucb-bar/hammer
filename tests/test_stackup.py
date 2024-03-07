from decimal import Decimal

from hammer.tech.stackup import Metal
from utils.stackup import StackupTestHelper

import json
import pytest


class TestStackup:
    """
    Tests for the stackup APIs in stackup.py.
    """

    def test_wire_parsing_from_json(self) -> None:
        """
        Test that wires can be parsed correctly from JSON.
        """
        grid_unit = StackupTestHelper.mfr_grid()
        metal = StackupTestHelper.create_test_metal(3, grid_unit)
        direct_metal = Metal.from_setting(grid_unit, StackupTestHelper.create_test_metal(3, grid_unit).model_dump())
        json_string: str = metal.model_dump_json()
        json_metal = Metal.from_setting(grid_unit, json.loads(json_string))  # type: Metal
        assert direct_metal == json_metal

    def test_twt_wire(self) -> None:
        """
        Test that a T W T wire is correctly sized.
        This will pass if the wide wire does not have a spacing DRC violation
        to surrounding minimum-sized wires and is within a single unit grid.
        This method is not allowed to round the wire, so simply adding a
        manufacturing grid should suffice to "fail" DRC.
        """
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # Try with 1 track (this should return a minimum width wire)
            w, s, o = m.get_width_spacing_start_twt(1, logger=None)
            assert w == m.min_width
            assert s == m.pitch - w

            # e.g. 2 tracks:
            # | | | |
            # T  W  T
            # e.g. 4 tracks:
            # | | | | | |
            # T  --W--  T
            for num_tracks in range(2,40):
                w, s, o = m.get_width_spacing_start_twt(num_tracks, logger=None)
                # Check that the resulting spacing is the min spacing
                assert s >= m.get_spacing_for_width(w)
                # Check that there is no DRC
                assert m.pitch * (num_tracks + 1) >= m.min_width + s*2 + w
                # Check that if we increase the width slightly we get a DRC violation
                w = w + (m.grid_unit * 2)
                s = m.get_spacing_for_width(w)
                assert m.pitch * (num_tracks + 1) < m.min_width + s*2 + w

    def test_twwt_wire(self) -> None:
        """
        Test that a T W W T wire is correctly sized.
        This will pass if the wide wire does not have a spacing DRC violation
        to surrounding minimum-sized wires and is within a single unit grid.
        This method is not allowed to round the wire, so simply adding a
        manufacturing grid should suffice to "fail" DRC.
        """
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # Try with 1 track (this should return a minimum width wire)
            w, s, o = m.get_width_spacing_start_twwt(1, logger=None)
            assert w == m.min_width
            assert s == m.pitch - w

            # e.g. 2 tracks:
            # | | | | | |
            # T  W   W  T
            # e.g. 4 tracks:
            # | | | | | | | | | |
            # T  --W--   --W--  T
            for num_tracks in range(2,40):
                w, s, o = m.get_width_spacing_start_twwt(num_tracks, logger=None)
                # Check that the resulting spacing is the min spacing
                assert s >= m.get_spacing_for_width(w)
                # Check that there is no DRC
                assert m.pitch * (2 * num_tracks + 1) >= m.min_width + s*3 + w*2
                # Check that if we increase the width slightly we get a DRC violation
                w = w + (m.grid_unit*2)
                s = m.get_spacing_for_width(w)
                assert m.pitch * (2 * num_tracks + 1) < m.min_width + s*3 + w*2


    def test_min_spacing_for_width(self) -> None:
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # generate some widths:
            for x in ["1.0", "2.0", "3.4", "4.5", "5.25", "50.2"]:
                # coerce to a manufacturing grid, this is just a test data point
                w = Decimal(x) * m.min_width
                s = m.get_spacing_for_width(w)
                for wst in m.power_strap_widths_and_spacings:
                    if w >= wst.width_at_least:
                        assert s >= wst.min_spacing

    # https://docs.pytest.org/en/latest/example/markers.html
    @pytest.mark.long
    def test_get_spacing_from_pitch(self) -> None:
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # generate some widths:
            for x in range(0, 100000, 5):
                # Generate a test data point
                p = (m.grid_unit * x) + m.pitch
                s = m.min_spacing_from_pitch(p)
                w = p - s
                # Check that we don't violate DRC
                assert p >= w + m.get_spacing_for_width(w)
                # Check that the wire is as large as possible by growing it
                w = w + (m.grid_unit*2)
                assert p < w + m.get_spacing_for_width(w)

    def test_quantize_to_width_table(self) -> None:
        # Generate two metals (index 1) and add more entries to width table of one of them
        # Only 0.05, 0.25, 0.45, 0.65, 0.85+ allowed -> check quantization against metal without width table
        # TODO: improve this behaviour in a future PR
        grid_unit = StackupTestHelper.mfr_grid()
        metal = StackupTestHelper.create_test_metal(1, grid_unit)
        metal.power_strap_width_table = StackupTestHelper.create_w_tbl(1, 5, grid_unit)
        q_metal = Metal.from_setting(StackupTestHelper.mfr_grid(), metal.model_dump())
        nq_metal = Metal.from_setting(StackupTestHelper.mfr_grid(), StackupTestHelper.create_test_metal(1, grid_unit).model_dump())
        for num_tracks in range(1, 20):
            # twt case
            wq, sq, oq = q_metal.get_width_spacing_start_twt(num_tracks, logger=None)
            wnq, snq, onq = nq_metal.get_width_spacing_start_twt(num_tracks, logger=None)
            if wnq < Decimal('0.25'):
                assert wq == Decimal('0.05')
            elif wnq < Decimal('0.45'):
                assert wq == Decimal('0.25')
            elif wnq < Decimal('0.65'):
                assert wq == Decimal('0.45')
            elif wnq < Decimal('0.85'):
                assert wq == Decimal('0.65')
            else:
                assert wq == wnq
            # twwt case
            wq, sq, oq = q_metal.get_width_spacing_start_twwt(num_tracks, logger=None)
            wnq, snq, onq = nq_metal.get_width_spacing_start_twwt(num_tracks, logger=None)
            if wnq < Decimal('0.25'):
                assert wq == Decimal('0.05')
            elif wnq < Decimal('0.45'):
                assert wq == Decimal('0.25')
            elif wnq < Decimal('0.65'):
                assert wq == Decimal('0.45')
            elif wnq < Decimal('0.85'):
                assert wq == Decimal('0.65')
            else:
                assert wq == wnq
