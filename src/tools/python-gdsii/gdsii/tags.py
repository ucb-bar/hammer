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
:mod:`gdsii.tags` --- definitions of GDSII tags
===============================================

This module containing definitions of GDSII record tags.

.. moduleauthor:: Eugeniy Meshcheryakov <eugen@debian.org>
"""

DICT = {
    'HEADER': 0x0002,
    'BGNLIB': 0x0102,
    'LIBNAME': 0x0206,
    'UNITS': 0x0305,
    'ENDLIB': 0x0400,
    'BGNSTR': 0x0502,
    'STRNAME': 0x0606,
    'ENDSTR': 0x0700,
    'BOUNDARY': 0x0800,
    'PATH': 0x0900,
    'SREF': 0x0A00,
    'AREF': 0x0B00,
    'TEXT': 0x0C00,
    'LAYER': 0x0D02,
    'DATATYPE': 0x0E02,
    'WIDTH': 0x0F03,
    'XY': 0x1003,
    'ENDEL': 0x1100,
    'SNAME': 0x1206,
    'COLROW': 0x1302,
    'TEXTNODE': 0x1400,
    'NODE': 0x1500,
    'TEXTTYPE': 0x1602,
    'PRESENTATION': 0x1701,
    # SPACING: 0x18??
    'STRING': 0x1906,
    'STRANS': 0x1A01,
    'MAG': 0x1B05,
    'ANGLE': 0x1C05,
    # UINTEGER: 0x1D??
    # USTRING: 0x1E??
    'REFLIBS': 0x1F06,
    'FONTS': 0x2006,
    'PATHTYPE': 0x2102,
    'GENERATIONS': 0x2202,
    'ATTRTABLE': 0x2306,
    'STYPTABLE': 0x2406,
    'STRTYPE': 0x2502,
    'ELFLAGS': 0x2601,
    'ELKEY': 0x2703,
    # LINKTYPE: 0x28??
    # LINKKEYS: 0x29??
    'NODETYPE': 0x2A02,
    'PROPATTR': 0x2B02,
    'PROPVALUE': 0x2C06,
    'BOX': 0x2D00,
    'BOXTYPE': 0x2E02,
    'PLEX': 0x2F03,
    'BGNEXTN': 0x3003,
    'ENDEXTN': 0x3103,
    'TAPENUM': 0x3202,
    'TAPECODE': 0x3302,
    'STRCLASS': 0x3401,
    # RESERVED: 0x3503
    'FORMAT': 0x3602,
    'MASK': 0x3706,
    'ENDMASKS': 0x3800,
    'LIBDIRSIZE': 0x3902,
    'SRFNAME': 0x3A06,
    'LIBSECUR': 0x3B02,
    # Types used only with Custom Plus
    'BORDER': 0x3C00,
    'SOFTFENCE': 0x3D00,
    'HARDFENCE': 0x3E00,
    'SOFTWIRE': 0x3F00,
    'HARDWIRE': 0x4000,
    'PATHPORT': 0x4100,
    'NODEPORT': 0x4200,
    'USERCONSTRAINT': 0x4300,
    'SPACERERROR': 0x4400,
    'CONTACT': 0x4500
}

REV_DICT = {}

for (key, value) in DICT.items():
    globals()[key] = value
    REV_DICT[value] = key

del key, value

def type_of_tag(tag):
    """
    Returns type of a tag.

    :param tag: tag ID
    :type tag: int
    :rtype: int

    Examples:

        >>> type_of_tag(HEADER)
        2
        >>> type_of_tag(MASK)
        6

    """
    return tag & 0xff

if __name__ == '__main__':
    import doctest
    doctest.testmod()
