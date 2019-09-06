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
:mod:`gdsii.library` --- interface to a GDSII library
=====================================================

This module contains class that represents a GDSII library.

.. moduleauthor:: Eugeniy Meshcheryakov <eugen@debian.org>
"""
from __future__ import absolute_import
from . import exceptions, record, structure, tags, _records
from datetime import datetime

_HEADER = _records.SimpleRecord('version', tags.HEADER)
_BGNLIB = _records.TimestampsRecord('mod_time', 'acc_time', tags.BGNLIB)
_LIBDIRSIZE = _records.SimpleOptionalRecord('libdirsize', tags.LIBDIRSIZE)
_SRFNAME = _records.OptionalWholeRecord('srfname', tags.SRFNAME)
_LIBSECUR = _records.ACLRecord('acls', tags.LIBSECUR)
_LIBNAME = _records.StringRecord('name', tags.LIBNAME)
_REFLIBS = _records.OptionalWholeRecord('reflibs', tags.REFLIBS)
_FONTS = _records.OptionalWholeRecord('fonts', tags.FONTS)
_ATTRTABLE = _records.OptionalWholeRecord('attrtable', tags.ATTRTABLE)
_GENERATIONS = _records.SimpleOptionalRecord('generations', tags.GENERATIONS)
_FORMAT = _records.FormatRecord('format', 'masks', tags.FORMAT)
_UNITS = _records.UnitsRecord('logical_unit', 'physical_unit', tags.UNITS)

class Library(list):
    """
    GDSII library class. This class is derived from :class:`list` and can contain
    one one more instances of :class:`gdsii.structure.Structure`.

    GDS syntax for the library:
        .. productionlist::
            library: HEADER
                   : BGNLIB
                   : [LIBDIRSIZE]
                   : [SRFNAME]
                   : [LIBSECUR]
                   : LIBNAME
                   : [REFLIBS]
                   : [FONTS]
                   : [ATTRTABLE]
                   : [GENERATIONS]
                   : [`format`]
                   : UNITS
                   : {`structure`}*
                   : ENDLIB
            format: FORMAT
                  : [MASK+ ENDMASKS]
    """
    _gds_objs = (_HEADER, _BGNLIB, _LIBDIRSIZE, _SRFNAME, _LIBSECUR, _LIBNAME, _REFLIBS,
            _FONTS, _ATTRTABLE, _GENERATIONS, _FORMAT, _UNITS)

    def __init__(self, version, name, physical_unit, logical_unit, mod_time=None,
            acc_time=None):
        """
        Initialize the library.
        `mod_time` and `acc_time` are set to current UTC time by default.
        """
        list.__init__(self)
        self.version = version
        self.name = name
        self.physical_unit = physical_unit
        self.logical_unit = logical_unit
        self.mod_time = mod_time if mod_time is not None else datetime.utcnow()
        self.acc_time = acc_time if acc_time is not None else datetime.utcnow()
        self._init_optional()

    def _init_optional(self):
        """Initialize optional attributes to None."""
        self.libdirsize = None
        self.srfname = None
        self.acls = None
        self.reflibs = None
        self.fonts = None
        self.attrtable = None
        self.generations = None
        self.format = None
        self.masks = None

    @classmethod
    def load(cls, stream):
        """
        Load a GDS library from a file.

        :param stream: a :class:`file` or file-like object opened for reading in binary mode.
        :returns: a new library.
        """
        self = cls.__new__(cls)
        list.__init__(self)
        self._init_optional()

        gen = record.Reader(stream)

        gen.read_next()
        for obj in self._gds_objs:
            obj.read(self, gen)

        # read structures starting with BGNSTR or ENDLIB
        rec = gen.current
        while True:
            if rec.tag == tags.BGNSTR:
                self.append(structure.Structure._load(gen))
                rec = gen.read_next()
            elif rec.tag == tags.ENDLIB:
                break
            else:
                raise exceptions.FormatError('unexpected tag where BGNSTR or ENDLIB are expected: %d', rec.tag)
        return self

    def save(self, stream):
        """
        Save the library into a file.

        :param stream: a :class:`file` or file-like object opened for writing in binary mode.
        """
        for obj in self._gds_objs:
            obj.save(self, stream)
        for struc in self:
            struc._save(stream)
        record.Record(tags.ENDLIB).save(stream)

    def __repr__(self):
        return '<Library: %s>' % self.name.decode()
