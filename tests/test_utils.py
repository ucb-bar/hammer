#  Utility tests for hammer-vlsi.
#
#  See LICENSE for licence details.

from typing import Dict, Tuple, List, Optional, Union, cast
from decimal import Decimal

from hammer.utils import (topological_sort, get_or_else, optional_map, assert_function_type, check_function_type,
                          gcd, lcm, lcm_grid, coerce_to_grid, check_on_grid, um2mm)

import pytest


class TestUtils:
    def test_topological_sort(self) -> None:
        """
        Test that topological sort works properly.
        """

        # tuple convention: (outgoing, incoming)
        graph = {
            "1": (["4"], []),
            "2": (["4"], []),
            "3": (["5", "6"], []),
            "4": (["7", "5"], ["1", "2"]),
            "5": (["8"], ["4", "3"]),
            "6": ([], ["3"]),
            "7": (["8"], ["4"]),
            "8": ([], ["7", "5"])
        }  # type: Dict[str, Tuple[List[str], List[str]]]

        assert topological_sort(graph, ["1", "2", "3"]) == ["1", "2", "3", "4", "6", "7", "5", "8"]

    def test_get_or_else(self) -> None:
        assert get_or_else(None, "default") == "default"
        assert get_or_else(None, "") == ""
        assert get_or_else("Hello World", "default") == "Hello World"
        assert get_or_else("Hello World", "") == "Hello World"

    def test_optional_map(self) -> None:
        num_to_str = lambda x: str(x) + "_str"
        str_to_num = lambda x: int(x) * 10
        assert optional_map(None, num_to_str) is None
        assert optional_map(10, num_to_str) == "10_str"
        assert optional_map(0, num_to_str) == "0_str"
        assert optional_map(None, str_to_num) is None
        assert optional_map("88", str_to_num) == 880
        assert not optional_map("88", str_to_num) == "880"
        assert optional_map("42", str_to_num) == 420

    def test_coerce_to_grid(self) -> None:
        assert coerce_to_grid(1.23, Decimal("0.1")) == Decimal("1.2")
        assert coerce_to_grid(1.23, Decimal("0.01")) == Decimal("1.23")
        assert coerce_to_grid(1.227, Decimal("0.01")) == Decimal("1.23")
        assert coerce_to_grid(200, Decimal("10")) == Decimal("200")
        assert coerce_to_grid(1.0/3.0, Decimal("0.001")) == Decimal("0.333")

    def test_check_on_grid(self) -> None:
        assert check_on_grid(Decimal("1.23"), Decimal("0.01"))
        assert not check_on_grid(Decimal("1.23"), Decimal("0.1"))
        assert check_on_grid(Decimal("1.20"), Decimal("0.1"))
        assert check_on_grid(Decimal("1.20"), Decimal("0.03"))
        assert not check_on_grid(Decimal("1.20"), Decimal("0.07"))
        assert check_on_grid(Decimal("2000"), Decimal("10"))
        assert not check_on_grid(Decimal("2000"), Decimal("13"))

    def test_gcd(self) -> None:
        assert gcd(1,2,3) == 1
        assert gcd(4,6,8) == 2
        assert gcd(3,6) == 3
        assert gcd(17) == 17
        assert gcd(1033, 1999) == 1
        assert gcd(1024, 4096) == 1024

    def test_lcm(self) -> None:
        assert lcm(1,2,3) == 6
        assert lcm(4,6,8) == 24
        assert lcm(3,6) == 6
        assert lcm(17) == 17
        assert lcm(1033, 1999) == 2064967
        assert lcm(1024, 4096) == 4096

    def test_lcm_grid(self) -> None:
        unit = Decimal("0.001")
        assert lcm_grid(unit, Decimal("1.234")) == Decimal("1.234")
        assert lcm_grid(unit, Decimal("0.09"), Decimal("0.08")) == Decimal("0.72")
        assert lcm_grid(unit, Decimal("0.003"), Decimal("0.005"), Decimal("0.11")) == Decimal("0.33")
        assert lcm_grid(unit, Decimal("0.245"), Decimal("0.013"), Decimal("0.002")) == Decimal("6.37")

    def test_check_function_type(self) -> None:
        def test1(x: int) -> str:
            return str(x + 5)

        assert_function_type(test1, [int], str)

        def test2(a: int, b: float) -> None:
            print("{a}{b}".format(a=a, b=b))

        assert_function_type(test2, [int, float], None)  # type: ignore

        def test3(a: int, b: int) -> List[int]:
            return [a, b]

        assert_function_type(test3, [int, int], List[int])

        def test4(a: int, b: int) -> List[int]:
            return [a, b]

        assert_function_type(test4, [int, int], List[int])

        # Check that dict == typing.Dict, etc.
        def test5(a: int) -> dict:
            return {"a": a}

        assert_function_type(test5, [int], Dict)

        # Check that dict == typing.Dict, etc.
        def test6(a: int) -> Optional[dict]:
            return {"a": a}

        # Possible mypy bug
        assert_function_type(test6, [int], cast(type, Optional[dict]))

        # Check that Union types get handled properly.
        def test7(a: Union[int, float]) -> Union[bool, str]:
            return str(a)

        # Possible mypy bug
        assert_function_type(test7, [cast(type, Union[int, float])], cast(type, Union[bool, str]))

        # Check that stringly-typed annotations work.
        def test8(a: "int") -> "list":
            return [a + a]

        assert_function_type(test8, ["int"], "list")  # type: ignore
        assert_function_type(test8, ["int"], list)  # type: ignore
        assert_function_type(test8, [int], "list")  # type: ignore
        assert_function_type(test8, [int], list)

        # Check that untyped arguments don't crash.
        def test9(x) -> str:
            return str(x)

        test9_return = check_function_type(test9, [int], str)
        assert test9_return is not None
        assert "incorrect signature" in test9_return

        with pytest.raises(TypeError):
            # Different # of arguments
            assert_function_type(test1, [int, int], str)
        with pytest.raises(TypeError):
            # Different return type
            assert_function_type(test1, [int], bool)
        with pytest.raises(TypeError):
            # Different argument type
            assert_function_type(test1, [str], str)
        with pytest.raises(TypeError):
            # Different # of arguments and different return type
            assert_function_type(test3, [int], bool)
        with pytest.raises(TypeError):
            # Entirely different
            assert_function_type(test3, [], dict)

    def test_um2mm(self) -> None:
        assert Decimal("1.234") == um2mm(Decimal("1234"), 3)
        assert Decimal("1.235") == um2mm(Decimal("1234.5"), 3)
        assert Decimal("1.23") == um2mm(Decimal("1230"), 3)
        assert Decimal("1.23") == um2mm(Decimal("1230"), 2)
        assert Decimal("0.01") == um2mm(Decimal("5"), 2)
        assert Decimal("0") == um2mm(Decimal("4"), 2)
        assert Decimal("40") == um2mm(Decimal("41235"), -1)
