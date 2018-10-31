#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for LEF utils.
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

from hammer_utils import LEFUtils

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

        lef_multiple_macros = """
VERSION 5.6 ;
NAMESCASESENSITIVE ON ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "|" ;
PROPERTYDEFINITIONS
 MACRO LEF58_EDGETYPE STRING ;
END PROPERTYDEFINITIONS

UNITS
 DATABASE MICRONS 1000 ;
END UNITS

MACRO MY_CELL_0
 CLASS CORE ;
   SIZE 2.718 BY 3.141 ;
 SYMMETRY X Y ;
 SITE STD_CELL_SITE ;
 PIN A
  DIRECTION INPUT ;
  USE SIGNAL ;
  PORT
   LAYER M1 ;
    RECT 1.000 1.000 1.400 1.400 ;
   END
  ANTENNAGATEAREA 0.008800 ;
 END A
 PIN B
  DIRECTION INPUT ;
  USE SIGNAL ;
  PORT
   LAYER M1 ;
    RECT 0.100 0.100 0.900 0.900 ;
   END
  ANTENNAGATEAREA 0.008800 ;
 END B
  PROPERTY LEF58_EDGETYPE "EDGETYPE LEFT MULTIPLEHEIGHT ; EDGETYPE RIGHT MULTIPLEHEIGHT ;" ;
END MY_CELL_0

MACRO MY_CELL_1
 CLASS CORE ;
   SIZE 3.000 BY 3.000 ;
 SYMMETRY X Y ;
 SITE STD_CELL_SITE ;
 PIN A
  DIRECTION INPUT ;
  USE SIGNAL ;
  PORT
   LAYER M1 ;
    RECT 1.000 1.000 1.400 1.400 ;
   END
  ANTENNAGATEAREA 0.006600 ;
 END A
 PIN B
  DIRECTION INPUT ;
  USE SIGNAL ;
  PORT
   LAYER M1 ;
    RECT 0.100 0.100 0.900 0.900 ;
   END
  ANTENNAGATEAREA 0.006600 ;
 END B
END MY_CELL_1

END LIBRARY
        """
        self.assertEqual(LEFUtils.get_sizes(lef_multiple_macros), [
            ("MY_CELL_0", 2.718, 3.141),
            ("MY_CELL_1", 3.000, 3.000)
        ])


if __name__ == '__main__':
    unittest.main()
