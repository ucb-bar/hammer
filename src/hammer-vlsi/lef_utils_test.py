#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for LEF utils.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from typing import Iterable, Tuple, Any

from hammer_vlsi import LEFUtils

import unittest


class LEFUtilsTest(unittest.TestCase):
    def test_get_sizes(self) -> None:
        """
        Test get_sizes.
        """
        lef_source = """
VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO my_awesome_macro
  CLASS BLOCK ;
  ORIGIN -0.435 607.525 ;
  FOREIGN my_awesome_macro 0.435 -607.525 ;
  SIZE 810.522 BY 607.525 ;
  SYMMETRY X Y R90 ;
  PIN my_pin
    DIRECTION INOUT ;
    USE SIGNAL ;
    PORT
      LAYER M1 ;
        RECT 42.91 -325.521 43.557 -325.021 ;
    END
  END c0
  OBS
    LAYER M1 ;
      RECT 810.077 -335.587 810.957 -334.707 ;
      RECT 0.435 -76.915 1.315 -76.035 ;
  END
END my_awesome_macro

END LIBRARY"""
        self.assertEqual(LEFUtils.get_sizes(lef_source), [("my_awesome_macro", 810.522, 607.525)])


if __name__ == '__main__':
    unittest.main()
