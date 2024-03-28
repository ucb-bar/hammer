#  Tests for unit classes.
#
#  See LICENSE for licence details.

import numpy as np
import pytest

import hammer.vlsi as hammer_vlsi


class TestVoltageValue:
    """
    Test voltages and other features of ValueWithUnits.
    """
    def test_voltage(self) -> None:
        """
        Test that voltages generally work as expected.
        """
        v8m = hammer_vlsi.units.VoltageValue("888 mV")
        v8 = hammer_vlsi.units.VoltageValue("0.888 V")
        assert np.allclose(v8m.value, 0.888)
        assert np.allclose(v8.value, 0.888)

        v105 = hammer_vlsi.units.VoltageValue("1.05 V")
        assert np.allclose(v105.value_in_units("mV"), 1050)

        v4 = hammer_vlsi.units.VoltageValue("400 mV")
        assert v4.str_value_in_units("V") == "0.4 V"

    def test_compare(self) -> None:
        """
        Test that comparison operators work properly.
        """
        value_125_mV = hammer_vlsi.units.VoltageValue("125 mV")
        value_125_mV2 = hammer_vlsi.units.VoltageValue("0.125")
        value_250_mV = hammer_vlsi.units.VoltageValue("250 mV")
        value_111_uV = hammer_vlsi.units.VoltageValue("111 uV")

        # Equality
        assert value_125_mV == value_125_mV2
        assert value_125_mV2 == value_125_mV
        assert not value_250_mV == value_125_mV
        assert value_250_mV != value_125_mV

        # Less than
        assert value_125_mV <= value_125_mV
        assert value_125_mV < value_250_mV
        assert value_125_mV2 < value_250_mV

        # Greater than
        assert value_125_mV >= value_125_mV
        assert value_125_mV > value_111_uV
        assert value_125_mV2 > value_111_uV

        # Check that comparing against the wrong type leads to TypeError
        with pytest.raises(TypeError):
            value_125_mV == "125 mV"  # type: ignore
        with pytest.raises(TypeError):
            value_125_mV2 == hammer_vlsi.units.TimeValue("0.125")  # type: ignore
        with pytest.raises(TypeError):
            value_125_mV < 1  # type: ignore
        with pytest.raises(TypeError):
            value_125_mV > 0.111  # type: ignore

    def test_negatives(self) -> None:
        """
        Test that negative values work properly.
        """
        positive = hammer_vlsi.units.VoltageValue("1 V")
        zero = hammer_vlsi.units.VoltageValue("0")
        negative = hammer_vlsi.units.VoltageValue("-200 mV")
        assert positive > zero
        assert zero > negative
        assert negative < zero
        assert negative < positive

    def test_math(self) -> None:
        """
        Test that math on voltages works properly.
        """
        onemV = hammer_vlsi.units.VoltageValue("1mV")
        zero = hammer_vlsi.units.VoltageValue("0")
        assert onemV - zero == onemV
        assert onemV + zero == onemV
        halfmV = hammer_vlsi.units.VoltageValue("0.5mV")
        assert onemV - halfmV == halfmV
        assert halfmV + halfmV == onemV
        oneV = hammer_vlsi.units.VoltageValue("1V")
        assert oneV/1000 == onemV
        assert onemV*1000 == oneV
        assert onemV*0 == zero
        assert oneV*0 == zero


class TestTimeValue:
    def test_read_and_write(self) -> None:
        """
        Test that we can parse and emit time values.
        """
        tv = hammer_vlsi.units.TimeValue("1000 ns")
        assert tv.str_value_in_units("ns") == "1000 ns"
        assert tv.str_value_in_units("us") == "1 us"
        assert tv.value_in_units("ps") == 1000000.0

    def test_default_prefix(self) -> None:
        """
        Test that we can parse and emit time values.
        """
        tv = hammer_vlsi.units.TimeValue("1000")
        assert tv.value_in_units("ns") == 1000
        tv2 = hammer_vlsi.units.TimeValue("42", "m")
        assert tv2.value_in_units("ms") == 42
        assert tv2.value_in_units("", round_zeroes=False) == 0.042

    def test_errors(self) -> None:
        """
        Test that errors get caught.
        """

        def bad_1():
            hammer_vlsi.units.TimeValue("bugaboo")

        def bad_2():
            hammer_vlsi.units.TimeValue("1.1.1.1 ps")

        def bad_3():
            hammer_vlsi.units.TimeValue("420 xs")

        def bad_4():
            hammer_vlsi.units.TimeValue("12 noobs")

        def bad_5():
            hammer_vlsi.units.TimeValue("666......")

        def bad_6():
            hammer_vlsi.units.TimeValue("--12 ps")

        def bad_7():
            hammer_vlsi.units.TimeValue("15-45 ps")

        pytest.raises(ValueError, bad_1)
        pytest.raises(ValueError, bad_2)
        pytest.raises(ValueError, bad_3)
        pytest.raises(ValueError, bad_4)
        pytest.raises(ValueError, bad_5)
        pytest.raises(ValueError, bad_6)
        pytest.raises(ValueError, bad_7)


class TestTemperatureValue:
    def test_temperature(self) -> None:
        t125 = hammer_vlsi.units.TemperatureValue("125 C")
        assert np.allclose(t125.value, 125)

        t40 = hammer_vlsi.units.TemperatureValue("40 C")
        assert np.allclose(t40.value, 40)

        t28_5 = hammer_vlsi.units.TemperatureValue("28.5 C")
        assert np.allclose(t28_5.value, 28.5)

        t25 = hammer_vlsi.units.TemperatureValue("25 C")
        assert np.allclose(t25.value, 25)
        assert np.allclose(t25.value_in_units("C"), 25)
        assert t25.str_value_in_units("C") == "25 C"


class TestCapacitanceValue:
    def test_capacitance(self) -> None:
        c5 = hammer_vlsi.units.CapacitanceValue("5 fF")
        assert np.allclose(c5.value, 5e-15)

        c1000 = hammer_vlsi.units.CapacitanceValue("1000 fF")
        assert np.allclose(c1000.value_in_units("pF"), 1)
        assert c1000.str_value_in_units("fF") == "1000 fF"
        assert c1000.str_value_in_units("pF") == "1 pF"
