#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Verilog-related tests for hammer-vlsi.
#
#  See LICENSE for licence details.

from typing import Iterable, Tuple, Any

from hammer_utils import VerilogUtils

import unittest


class VerilogUtilsTest(unittest.TestCase):
    # Samples
    universal = """
module reset
  (
   input clock,  // achoo
   input reset1, // dolor sit amet
   output reset2 // lorem ipsum
   );

   // stuff

endmodule

module universal_1
  #(
    parameter
    MS = 123_456_789,
    BOB = 123_456
    )
  (
   input            clock, reset, p,
   output reg       vache,
   output reg [7:0] datas
   );

reg [2:0] foo, bar; // dolor sit amet

endmodule

module universal_2
  #(
    parameter
    MS = 123_456_789,
    BOB = 123_456
    )
  (
   input            clock, reset, p,
   output reg       vache,
   output reg [7:0] datas
   );

reg [2:0] foo, bar; // dolor sit amet

endmodule
        """

    paths = """
module true_path (
  input clock,
  input reset,
  output reg truth,
  output reg truth2,
  output reg truth3
);

assign reg_truth = 1'd1;
// We don't want any implementations of the module false_path.
// This is the truthful module.

/* single line comment module junk */
/** stars module junk */
/**
  * Multi-line module junk
  */
/*
 * Another multi-line
 * module junk
 */

always @ (posedge clock) begin
    assign reg_truth2 = 1'd0; /* block comment module junk */
    assign reg_truth3 = 1'd0; // line comment module junk
end

endmodule

module neutral_path
(
  input in,
  output out
);
assign out = in;
endmodule
        """

    def test_contains_module(self) -> None:
        """
        Test contains_module.
        """
        self.assertTrue(VerilogUtils.contains_module(self.universal, "universal_1"))
        self.assertTrue(VerilogUtils.contains_module(self.universal, "universal_2"))
        self.assertTrue(VerilogUtils.contains_module(self.universal, "reset"))
        self.assertFalse(VerilogUtils.contains_module(self.universal, "parameter"))
        self.assertFalse(VerilogUtils.contains_module(self.universal, "input"))

        self.assertTrue(VerilogUtils.contains_module(self.paths, "true_path"))
        self.assertFalse(VerilogUtils.contains_module(self.paths, "false_path"))
        self.assertFalse(VerilogUtils.contains_module(self.paths, "junk"))
        self.assertFalse(VerilogUtils.contains_module(self.universal, "clock"))
        self.assertFalse(VerilogUtils.contains_module(self.universal, "endmodule"))

    def test_remove_module(self) -> None:
        """
        Test remove_module.
        """

        def sublists_generator(x: list) -> Iterable[Tuple[Any, list]]:
            """Generate sublists and removed elements where one element is excluded one at a time.
            e.g. given [1, 2, 3], return [(1, [2, 3]), (2, [1, 3]), (3, [1, 2])]
            """
            for i in range(len(x)):
                copy = list(x)
                elem = copy.pop(i)  # remove this index
                yield (elem, copy)

        for (elem, remaining_modules) in sublists_generator(["reset", "universal_1", "universal_2"]):
            removed = VerilogUtils.remove_module(self.universal, elem)

            self.assertFalse(VerilogUtils.contains_module(removed, elem))
            for remaining in remaining_modules:
                self.assertTrue(VerilogUtils.contains_module(removed, remaining))

        for (elem, remaining_modules) in sublists_generator(["true_path", "neutral_path"]):
            removed = VerilogUtils.remove_module(self.paths, elem)

            self.assertFalse(VerilogUtils.contains_module(removed, elem))
            for remaining in remaining_modules:
                self.assertTrue(VerilogUtils.contains_module(removed, remaining))


if __name__ == '__main__':
    unittest.main()
