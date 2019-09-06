# -*- coding: utf-8 -*-
#
#   Copyright © 2010 Eugeniy Meshcheryakov <eugen@debian.org>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Lesser General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
:mod:`gdsii.types` --- definitions of GDSII data types
======================================================

This module contains definitions of GDSII data types.
"""

DICT = {
    'NODATA': 0,
    'BITARRAY': 1,
    'INT2': 2,
    'INT4': 3,
    'REAL4': 4, # not used
    'REAL8': 5,
    'ASCII': 6
}

REV_DICT = {}

for (key, value) in DICT.items():
    globals()[key] = value
    REV_DICT[value] = key

del key, value
