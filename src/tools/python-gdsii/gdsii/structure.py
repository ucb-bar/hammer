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
:mod:`gdsii.structure` --- interface to a GDSII structure
=========================================================

This module contains class that represents a GDSII structure.

.. moduleauthor:: Eugeniy Meshcheryakov <eugen@debian.org>
"""
from __future__ import absolute_import
from . import elements, record, tags, _records
from datetime import datetime

_STRNAME = _records.StringRecord('name', tags.STRNAME)
_BGNSTR = _records.TimestampsRecord('mod_time', 'acc_time', tags.BGNSTR)
_STRCLASS = _records.SimpleOptionalRecord('strclass', tags.STRCLASS)

class Structure(list):
    """
    GDSII structure class. This class is derived for :class:`list` and can
    contain one or more elements from :mod:`gdsii.elements`.

    GDS syntax for the structure:
        .. productionlist::
            structure: BGNSTR
                     : STRNAME
                     : [STRCLASS]
                     : {`element`}*
                     : ENDSTR
    """
    _gds_objs = (_BGNSTR, _STRNAME, _STRCLASS)

    def __init__(self, name, mod_time=None, acc_time=None):
        """
        Initialize the structure.
        `mod_time` and `acc_time` are set to current UTC time by default.
        """
        list.__init__(self)
        self.name = name
        self.mod_time = mod_time if mod_time is not None else datetime.utcnow()
        self.acc_time = acc_time if acc_time is not None else datetime.utcnow()

    def _init_optional(self):
        """Initialize optional attributes to None."""
        self.strclass = None

    @classmethod
    def _load(cls, gen):
        self = cls.__new__(cls)
        list.__init__(self)
        self._init_optional()

        for obj in self._gds_objs:
            obj.read(self, gen)

        # read elements till ENDSTR
        while gen.current.tag != tags.ENDSTR:
            self.append(elements._Base._load(gen))
        return self

    def _save(self, stream):
        for obj in self._gds_objs:
            obj.save(self, stream)
        for elem in self:
            elem._save(stream)
        record.Record(tags.ENDSTR).save(stream)

    def __repr__(self):
        return '<Structure: %s>' % self.name.decode()
