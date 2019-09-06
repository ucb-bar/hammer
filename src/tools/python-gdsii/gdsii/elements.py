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
:mod:`gdsii.elements` -- interface to GDSII elements
====================================================

This module contains definitions for classes representing
various GDSII elements. Mapping between GDSII elements and
classes is given in the following table:

   +-------------------+-------------------+
   | GDSII Record      | Class             |
   +===================+===================+
   | :const:`AREF`     | :class:`ARef`     |
   +-------------------+-------------------+
   | :const:`BOUNDARY` | :class:`Boundary` |
   +-------------------+-------------------+
   | :const:`BOX`      | :class:`Box`      |
   +-------------------+-------------------+
   | :const:`NODE`     | :class:`Node`     |
   +-------------------+-------------------+
   | :const:`PATH`     | :class:`Path`     |
   +-------------------+-------------------+
   | :const:`SREF`     | :class:`SRef`     |
   +-------------------+-------------------+
   | :const:`TEXT`     | :class:`Text`     |
   +-------------------+-------------------+

This module implements the following GDS syntax:
    .. productionlist::
        element: `aref` |
               : `boundary` |
               : `box` |
               : `node` |
               : `path` |
               : `sref` |
               : `text`
Additional definitions:
    .. productionlist::
        properties: `property`*
        property: PROPATTR
                : PROPVALUE
        strans: STRANS
              : [MAG]
              : [ANGLE]

.. moduleauthor:: Eugeniy Meshcheryakov <eugen@debian.org>
"""
from __future__ import absolute_import
from . import exceptions, record, tags, _records

__all__ = (
    'Boundary',
    'Path',
    'SRef',
    'ARef',
    'Text',
    'Node',
    'Box'
)

_ELFLAGS = _records.OptionalWholeRecord('elflags', tags.ELFLAGS)
_PLEX = _records.SimpleOptionalRecord('plex', tags.PLEX)
_LAYER = _records.SimpleRecord('layer', tags.LAYER)
_DATATYPE = _records.SimpleRecord('data_type', tags.DATATYPE)
_PATHTYPE = _records.SimpleOptionalRecord('path_type', tags.PATHTYPE)
_WIDTH = _records.SimpleOptionalRecord('width', tags.WIDTH)
_BGNEXTN = _records.SimpleOptionalRecord('bgn_extn', tags.BGNEXTN)
_ENDEXTN = _records.SimpleOptionalRecord('end_extn', tags.ENDEXTN)
_XY = _records.XYRecord('xy', tags.XY)
_SNAME = _records.StringRecord('struct_name', tags.SNAME)
_STRANS = _records.STransRecord('strans', tags.STRANS)
_COLROW = _records.ColRowRecord('cols', 'rows')
_TEXTTYPE = _records.SimpleRecord('text_type', tags.TEXTTYPE)
_PRESENTATION = _records.OptionalWholeRecord('presentation', tags.PRESENTATION)
_STRING = _records.StringRecord('string', tags.STRING)
_NODETYPE = _records.SimpleRecord('node_type', tags.NODETYPE)
_BOXTYPE = _records.SimpleRecord('box_type', tags.BOXTYPE)
_PROPERTIES = _records.PropertiesRecord('properties')

class _Base(object):
    """Base class for all GDSII elements."""

    # dummy descriptors to silence pyckecker, should be set in derived classes
    _gds_tag = None
    _gds_objs = None
    __slots__ = ()

    def __init__(self):
        """Initialize the element."""
        self._init_optional()

    def _init_optional(self):
        """Initialize optional attributes to None."""
        raise NotImplementedError

    @classmethod
    def _load(cls, gen):
        """
        Load an element from file using given generator `gen`.

        :param gen: :class:`pygdsii.record.Record` generator
        :returns: new element of class defined by `gen`
        """
        element_class = cls._tag_to_class_map[gen.current.tag]
        if not element_class:
            raise exceptions.FormatError('unexpected element tag')
        # do not call __init__() during reading from file
        # __init__() should require some arguments
        new_element = element_class._read_element(gen)
        return new_element

    @classmethod
    def _read_element(cls, gen):
        """Read element using `gen` generator."""
        self = cls.__new__(cls)
        self._init_optional()
        gen.read_next()
        for obj in self._gds_objs:
            obj.read(self, gen)
        gen.current.check_tag(tags.ENDEL)
        gen.read_next()
        return self

    def _save(self, stream):
        record.Record(self._gds_tag).save(stream)
        for obj in self._gds_objs:
            obj.save(self, stream)
        record.Record(tags.ENDEL).save(stream)

class Boundary(_Base):
    """
    Class for :const:`BOUNDARY` GDSII element.

    GDS syntax:
        .. productionlist::
            boundary: BOUNDARY
                     : [ELFLAGS]
                     : [PLEX]
                     : LAYER
                     : DATATYPE
                     : XY
                     : [`properties`]
                     : ENDEL
    """
    _gds_tag = tags.BOUNDARY
    _gds_objs = (_ELFLAGS, _PLEX, _LAYER, _DATATYPE, _XY, _PROPERTIES)
    __slots__ = ('layer', 'data_type', 'xy', 'elflags', 'plex', 'properties')

    def __init__(self, layer, data_type, xy):
        _Base.__init__(self)
        self.layer = layer
        self.data_type = data_type
        self.xy = xy

    def _init_optional(self):
        self.elflags = None
        self.plex = None
        self.properties = None

class Path(_Base):
    """
    Class for :const:`PATH` GDSII element.

    GDS syntax:
        .. productionlist::
            path: PATH
                : [ELFLAGS]
                : [PLEX]
                : LAYER
                : DATATYPE
                : [PATHTYPE]
                : [WIDTH]
                : [BGNEXTN]
                : [ENDEXTN]
                : XY
                : [`properties`]
                : ENDEL
    """
    _gds_tag = tags.PATH
    _gds_objs = (_ELFLAGS, _PLEX, _LAYER, _DATATYPE, _PATHTYPE, _WIDTH,
            _BGNEXTN, _ENDEXTN, _XY, _PROPERTIES)
    __slots__ = ('layer', 'data_type', 'xy', 'elflags', 'plex', 'path_type',
            'width', 'bgn_extn', 'end_extn', 'properties')

    def __init__(self, layer, data_type, xy):
        _Base.__init__(self)
        self.layer = layer
        self.data_type = data_type
        self.xy = xy

    def _init_optional(self):
        self.elflags = None
        self.plex = None
        self.path_type = None
        self.width = None
        self.bgn_extn = None
        self.end_extn = None
        self.properties = None

class SRef(_Base):
    """
    Class for :const:`SREF` GDSII element.

    GDS syntax:
        .. productionlist::
            sref: SREF
                : [ELFLAGS]
                : [PLEX]
                : SNAME
                : [`strans`]
                : XY
                : [`properties`]
                : ENDEL
    """
    _gds_tag = tags.SREF
    _gds_objs = (_ELFLAGS, _PLEX, _SNAME, _STRANS, _XY, _PROPERTIES)
    __slots__ = ('struct_name', 'xy', 'elflags', 'strans', 'mag', 'angle',
            'properties')

    def __init__(self, struct_name, xy):
        _Base.__init__(self)
        self.struct_name = struct_name
        self.xy = xy

    def _init_optional(self):
        self.elflags = None
        self.strans = None
        self.mag = None
        self.angle = None
        self.properties = None

class ARef(_Base):
    """
    Class for :const:`AREF` GDSII element.

    GDS syntax:
        .. productionlist::
            aref: AREF
                : [ELFLAGS]
                : [PLEX]
                : SNAME
                : [`strans`]
                : COLROW
                : XY
                : [`properties`]
                : ENDEL
    """
    _gds_tag = tags.AREF
    _gds_objs = (_ELFLAGS, _PLEX, _SNAME, _STRANS, _COLROW, _XY, _PROPERTIES)
    __slots__ = ('struct_name', 'cols', 'rows', 'xy', 'elflags', 'plex',
            'strans', 'mag', 'angle', 'properties')

    def __init__(self, struct_name, cols, rows, xy):
        _Base.__init__(self)
        self.struct_name = struct_name
        self.cols = cols
        self.rows = rows
        self.xy = xy

    def _init_optional(self):
        self.elflags = None
        self.plex = None
        self.strans = None
        self.mag = None
        self.angle = None
        self.properties = None

class Text(_Base):
    """
    Class for :const:`TEXT` GDSII element.

    GDS syntax:
        .. productionlist::
            text: TEXT
                : [ELFLAGS]
                : [PLEX]
                : LAYER
                : TEXTTYPE
                : [PRESENTATION]
                : [PATHTYPE]
                : [WIDTH]
                : [`strans`]
                : XY
                : STRING
                : [`properties`]
                : ENDEL
    """
    _gds_tag = tags.TEXT
    _gds_objs = (_ELFLAGS, _PLEX, _LAYER, _TEXTTYPE, _PRESENTATION, _PATHTYPE,
            _WIDTH, _STRANS, _XY, _STRING, _PROPERTIES)
    __slots__ = ('layer', 'text_type', 'xy', 'string', 'elflags', 'plex',
            'presentation', 'path_type', 'width', 'strans', 'mag', 'angle',
            'properties')

    def __init__(self, layer, text_type, xy, string):
        _Base.__init__(self)
        self.layer = layer
        self.text_type = text_type
        self.xy = xy
        self.string = string

    def _init_optional(self):
        self.elflags = None
        self.plex = None
        self.presentation = None
        self.path_type = None
        self.width = None
        self.strans = None
        self.mag = None
        self.angle = None
        self.properties = None

class Node(_Base):
    """
    Class for :const:`NODE` GDSII element.

    GDS syntax:
        .. productionlist::
            node: NODE
                : [ELFLAGS]
                : [PLEX]
                : LAYER
                : NODETYPE
                : XY
                : [`properties`]
                : ENDEL
    """
    _gds_tag = tags.NODE
    _gds_objs = (_ELFLAGS, _PLEX, _LAYER, _NODETYPE, _XY, _PROPERTIES)
    __slots__ = ('layer', 'node_type', 'xy', 'elflags', 'plex', 'properties')

    def __init__(self, layer, node_type, xy):
        _Base.__init__(self)
        self.layer = layer
        self.node_type = node_type
        self.xy = xy

    def _init_optional(self):
        self.elflags = None
        self.plex = None
        self.properties = None

class Box(_Base):
    """
    Class for :const:`BOX` GDSII element.

    GDS syntax:
        .. productionlist::
            box: BOX
               : [ELFLAGS]
               : [PLEX]
               : LAYER
               : BOXTYPE
               : XY
               : [`properties`]
               : ENDEL
    """
    _gds_tag = tags.BOX
    _gds_objs = (_ELFLAGS, _PLEX, _LAYER, _BOXTYPE, _XY, _PROPERTIES)
    __slots__ = ('layer', 'box_type', 'xy', 'elflags', 'plex', 'properties')

    def __init__(self, layer, box_type, xy):
        _Base.__init__(self)
        self.layer = layer
        self.box_type = box_type
        self.xy = xy

    def _init_optional(self):
        self.elflags = None
        self.plex = None
        self.properties = None

_all_elements = (Boundary, Path, SRef, ARef, Text, Node, Box)

_Base._tag_to_class_map = (lambda: dict(((cls._gds_tag, cls) for cls in _all_elements)))()
