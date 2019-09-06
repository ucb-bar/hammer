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
:mod:`gdsii.record` --- GDSII record I/O
========================================

This module contains classes for low-level GDSII I/O.

.. moduleauthor:: Eugeniy Meshcheryakov <eugen@debian.org>
"""
from __future__ import absolute_import
from . import exceptions, tags, types
from datetime import datetime
import math
import struct

__all__ = [
    'Record',
    'Reader'
]

_RECORD_HEADER_FMT = struct.Struct('>HH')

def _parse_nodata(data):
    """Parse :const:`NODATA` data type. Does nothing."""

def _parse_bitarray(data):
    """
    Parse :const:`BITARRAY` data type.

        >>> _parse_bitarray(b'ab') # ok, 2 bytes
        24930
        >>> _parse_bitarray(b'abcd') # too long
        Traceback (most recent call last):
            ...
        IncorrectDataSize: BITARRAY
        >>> _parse_bitarray('') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: BITARRAY
    """
    if len(data) != 2:
        raise exceptions.IncorrectDataSize('BITARRAY')
    (val,) = struct.unpack('>H', data)
    return val

def _parse_int2(data):
    """
    Parse INT2 data type.

        >>> _parse_int2(b'abcd') # ok, even number of bytes
        (24930, 25444)
        >>> _parse_int2(b'abcde') # odd number of bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT2
        >>> _parse_int2(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT2
    """
    data_len = len(data)
    if not data_len or (data_len % 2):
        raise exceptions.IncorrectDataSize('INT2')
    return struct.unpack('>%dh' % (data_len//2), data)

def _parse_int4(data):
    """
    Parse INT4 data type.

        >>> _parse_int4(b'abcd')
        (1633837924,)
        >>> _parse_int4(b'abcdef') # not divisible by 4
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT4
        >>> _parse_int4(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: INT4
    """
    data_len = len(data)
    if not data_len or (data_len % 4):
        raise exceptions.IncorrectDataSize('INT4')
    return struct.unpack('>%dl' % (data_len//4), data)

def _int_to_real(num):
    """
    Convert REAL8 from internal integer representation to Python reals.

    Zeroes:
        >>> print(_int_to_real(0x0))
        0.0
        >>> print(_int_to_real(0x8000000000000000)) # negative
        0.0
        >>> print(_int_to_real(0xff00000000000000)) # denormalized
        0.0

    Others:
        >>> print(_int_to_real(0x4110000000000000))
        1.0
        >>> print(_int_to_real(0xC120000000000000))
        -2.0
    """
    sgn = -1 if 0x8000000000000000 & num else 1
    mant = num & 0x00ffffffffffffff
    exp = (num >> 56) & 0x7f
    return math.ldexp(sgn * mant, 4 * (exp - 64) - 56)

def _parse_real8(data):
    """
    Parse REAL8 data type.

        >>> _parse_real8(struct.pack('>3Q', 0x0, 0x4110000000000000, 0xC120000000000000))
        (0.0, 1.0, -2.0)
        >>> _parse_real8(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: REAL8
        >>> _parse_real8(b'abcd') # not divisible by 8
        Traceback (most recent call last):
            ...
        IncorrectDataSize: REAL8
    """
    data_len = len(data)
    if not data_len or (data_len % 8):
        raise exceptions.IncorrectDataSize('REAL8')
    ints = struct.unpack('>%dQ' % (data_len//8), data)
    return tuple(_int_to_real(n) for n in ints)

def _parse_ascii(data):
    r"""
    Parse ASCII data type.

        >>> _parse_ascii(b'') # zero bytes
        Traceback (most recent call last):
            ...
        IncorrectDataSize: ASCII
        >>> _parse_ascii(b'abcde') == b'abcde'
        True
        >>> _parse_ascii(b'abcde\0') == b'abcde' # strips trailing NUL
        True
    """
    if not len(data):
        raise exceptions.IncorrectDataSize('ASCII')
    # XXX cross-version compatibility
    if data[-1:] == b'\0':
        return data[:-1]
    return data

_PARSE_FUNCS = {
    types.NODATA: _parse_nodata,
    types.BITARRAY: _parse_bitarray,
    types.INT2: _parse_int2,
    types.INT4: _parse_int4,
    types.REAL8: _parse_real8,
    types.ASCII: _parse_ascii
}

def _pack_nodata(data):
    """
    Pack NODATA tag data. Should always return empty string::

       >>> packed = _pack_nodata([])
       >>> packed == b''
       True
       >>> len(packed)
       0
    """
    return b''

def _pack_bitarray(data):
    """
    Pack BITARRAY tag data.

        >>> packed = _pack_bitarray(123)
        >>> packed == struct.pack('>H', 123)
        True
        >>> len(packed)
        2
    """
    return struct.pack('>H', data)

def _pack_int2(data):
    """
    Pack INT2 tag data.

        >>> _pack_int2([1, 2, -3]) == struct.pack('>3h', 1, 2, -3)
        True
        >>> packed = _pack_int2((1, 2, 3))
        >>> packed == struct.pack('>3h', 1, 2, 3)
        True
        >>> len(packed)
        6
    """
    size = len(data)
    return struct.pack('>{0}h'.format(size), *data)

def _pack_int4(data):
    """
    Pack INT4 tag data.

        >>> _pack_int4([1, 2, -3]) == struct.pack('>3l', 1, 2, -3)
        True
        >>> packed = _pack_int4((1, 2, 3))
        >>> packed == struct.pack('>3l', 1, 2, 3)
        True
        >>> len(packed)
        12
    """
    size = len(data)
    return struct.pack('>{0}l'.format(size), *data)

def _real_to_int(fnum):
    """
    Convert REAL8 from Python real to internal integer representation.

        >>> '0x%016x' % _real_to_int(0.0)
        '0x0000000000000000'
        >>> print(_int_to_real(_real_to_int(1.0)))
        1.0
        >>> print(_int_to_real(_real_to_int(-2.0)))
        -2.0
        >>> print(_int_to_real(_real_to_int(1e-9)))
        1e-09
    """
    # first convert number to IEEE double and split it in parts
    (ieee,) = struct.unpack('=Q', struct.pack('=d', fnum))
    sign = ieee & 0x8000000000000000
    ieee_exp = (ieee >> 52) & 0x7ff
    ieee_mant = ieee & 0xfffffffffffff

    if ieee_exp == 0:
        # zero or denormals
        # TODO maybe handle denormals
        return 0

    # substract exponent bias
    unb_ieee_exp = ieee_exp - 1023
    # add leading one and move to GDSII position
    ieee_mant_full = (ieee_mant + 0x10000000000000) << 3

    # convert exponent to 16-based, +1 for differences in presentation
    # of mantissa (1.xxxx in EEEE and 0.1xxxxx in GDSII
    exp16, rest = divmod(unb_ieee_exp + 1, 4)
    # compensate exponent converion
    if rest:
        rest = 4 - rest
        exp16 += 1
    ieee_mant_comp = ieee_mant_full >> rest

    # add GDSII exponent bias
    exp16_biased = exp16 + 64

    # try to fit everything
    if exp16_biased < -14:
        return 0 # number is too small. FIXME is it possible?
    elif exp16_biased < 0:
        ieee_mant_comp = ieee_mant_comp >> (exp16_biased * 4)
        exp16_biased = 0
    elif exp16_biased > 0x7f:
        raise exceptions.FormatError('number is to big for REAL8')

    return sign | (exp16_biased << 56) | ieee_mant_comp

def _pack_real8(data):
    """
    Pack REAL8 tag data.

        >>> packed = _pack_real8([0, 1, -1, 0.5, 1e-9])
        >>> len(packed)
        40
        >>> list(map(str, _parse_real8(packed)))
        ['0.0', '1.0', '-1.0', '0.5', '1e-09']
    """
    size = len(data)
    return struct.pack('>{0}Q'.format(size), *[_real_to_int(num) for num in data])

def _pack_ascii(data):
    r"""
    Pack ASCII tag data.

        >>> _pack_ascii(b'abcd') == b'abcd'
        True
        >>> _pack_ascii(b'abc') == b'abc\0'
        True
    """
    size = len(data)
    if size % 2:
        return data + b'\0'
    return data

_PACK_FUNCS = {
    types.NODATA: _pack_nodata,
    types.BITARRAY: _pack_bitarray,
    types.INT2: _pack_int2,
    types.INT4: _pack_int4,
    types.REAL8: _pack_real8,
    types.ASCII: _pack_ascii
}

class Record(object):
    """
    Class for representing a GDSII record with attached data.
    Example::

        >>> r = Record(tags.STRNAME, 'my_structure')
        >>> '%04x' % r.tag
        '0606'
        >>> r.tag_name
        'STRNAME'
        >>> r.tag_type
        6
        >>> r.tag_type_name
        'ASCII'
        >>> r.data
        'my_structure'

        >>> r = Record(0xffff, 'xxx') # Unknown tag type
        >>> r.tag_name
        '0xffff'
        >>> r.tag_type_name
        '0xff'
    """
    __slots__ = ['tag', 'data']

    def __init__(self, tag, data=None, points=None, times=None, acls=None):
        """Initialize with tag and parsed data."""
        self.tag = tag
        if data is not None:
            self.data = data
        elif points is not None:
            new_data = []
            # TODO make it faster
            for point in points:
                new_data.append(point[0])
                new_data.append(point[1])
            self.data = new_data
        elif times is not None:
            mod_time = times[0]
            acc_time = times[1]
            self.data = (
                mod_time.year - 1900,
                mod_time.month,
                mod_time.day,
                mod_time.hour,
                mod_time.minute,
                mod_time.second,
                acc_time.year - 1900,
                acc_time.month,
                acc_time.day,
                acc_time.hour,
                acc_time.minute,
                acc_time.second
            )
        elif acls is not None:
            new_data = []
            for acl in acls:
                new_data.extend(acl)
            self.data = new_data
        else:
            self.data = None

    def check_tag(self, tag):
        """
        Checks if current record has the same tag as the given one.
        Raises :exc:`MissingRecord` exception otherwise. For example::

            >>> rec = Record(tags.STRNAME, b'struct')
            >>> rec.check_tag(tags.STRNAME)
            >>> rec.check_tag(tags.DATATYPE)
            Traceback (most recent call last):
                ...
            MissingRecord: Wanted: 3586, got: STRNAME
        """
        if self.tag != tag:
            raise exceptions.MissingRecord('Wanted: %s, got: %s'%(tag, self.tag_name))

    def check_size(self, size):
        """
        Checks if data size equals to the given size.
        Raises :exc:`DataSizeError` otherwise. For example::

            >>> rec = Record(tags.DATATYPE, (0,))
            >>> rec.check_size(1)
            >>> rec.check_size(5)
            Traceback (most recent call last):
                ...
            DataSizeError: 3586
        """
        if len(self.data) != size:
            raise exceptions.DataSizeError(self.tag)

    @classmethod
    def read(cls, stream):
        """
        Read a GDSII record from file.

        :param stream: GDS file opened for reading in binary mode
        :returns: a new :class:`Record` instance
        :raises: :exc:`UnsupportedTagType` if data cannot be parsed
        :raises: :exc:`EndOfFileError` if end of file is reached
        """
        header = stream.read(4)
        if not header or len(header) != 4:
            raise exceptions.EndOfFileError
        data_size, tag = _RECORD_HEADER_FMT.unpack(header)
        if data_size < 4:
            raise exceptions.IncorrectDataSize('data size is too small')
        if data_size % 2:
            raise exceptions.IncorrectDataSize('data size is odd')

        data_size -= 4 # substract header size

        data = stream.read(data_size)
        if len(data) != data_size:
            raise exceptions.EndOfFileError

        tag_type = tags.type_of_tag(tag)
        try:
            parse_func = _PARSE_FUNCS[tag_type]
        except KeyError:
            raise exceptions.UnsupportedTagType(tag_type)
        return cls(tag, parse_func(data))

    def save(self, stream):
        """
        Save record to a GDS file.

        :param stream: file opened for writing in binary mode
        :raises: :exc:`UnsupportedTagType` if tag type is not supported
        :raises: :exc:`FormatError` on incorrect data sizes, etc
        :raises: whatever :func:`struct.pack` can raise
        """
        tag_type = self.tag_type
        try:
            pack_func = _PACK_FUNCS[tag_type]
        except KeyError:
            raise exceptions.UnsupportedTagType(tag_type)
        packed_data = pack_func(self.data)
        record_size = len(packed_data) + 4
        if record_size > 0xFFFF:
            raise exceptions.FormatError('data size is too big')
        header = _RECORD_HEADER_FMT.pack(record_size, self.tag)
        stream.write(header)
        stream.write(packed_data)

    @property
    def tag_name(self):
        """Tag name, if known, otherwise tag ID formatted as hex number."""
        if self.tag in tags.REV_DICT:
            return tags.REV_DICT[self.tag]
        return '0x%04x' % self.tag

    @property
    def tag_type(self):
        """Tag data type ID."""
        return tags.type_of_tag(self.tag)

    @property
    def tag_type_name(self):
        """Tag data type name, if known, and formatted number otherwise."""
        tag_type = tags.type_of_tag(self.tag)
        if tag_type in types.REV_DICT:
            return types.REV_DICT[tag_type]
        return '0x%02x' % tag_type

    @property
    def points(self):
        """
        Convert data to list of points. Useful for :const:`XY` record.
        Raises :exc:`DataSizeError` if data size is incorrect.
        For example::

            >>> r = Record(tags.XY, [0, 1, 2, 3])
            >>> r.points
            [(0, 1), (2, 3)]
            >>> r = Record(tags.XY, []) # not allowed
            >>> r.points
            Traceback (most recent call last):
                ...
            DataSizeError: 4099
            >>> r = Record(tags.XY, [1, 2, 3]) # odd number of coordinates
            >>> r.points
            Traceback (most recent call last):
                ...
            DataSizeError: 4099
        """
        data_size = len(self.data)
        if not data_size or (data_size % 2):
            raise exceptions.DataSizeError(self.tag)
        return [(self.data[i], self.data[i+1]) for i in range(0, data_size, 2)]

    @property
    def times(self):
        """
        Convert data to tuple ``(modification time, access time)``.
        Useful for :const:`BGNLIB` and :const:`BGNSTR`.

            >>> r = Record(tags.BGNLIB, [100, 1, 1, 1, 2, 3, 110, 8, 14, 21, 10, 35])
            >>> print(r.times[0].isoformat())
            2000-01-01T01:02:03
            >>> print(r.times[1].isoformat())
            2010-08-14T21:10:35
            >>> r = Record(tags.BGNLIB, [100, 1, 1, 1, 2, 3]) # wrong data length
            >>> r.times
            Traceback (most recent call last):
                ...
            DataSizeError: 258
        """
        if len(self.data) != 12:
            raise exceptions.DataSizeError(self.tag)
        return (datetime(self.data[0]+1900, *self.data[1:6]),
                datetime(self.data[6]+1900, *self.data[7:12]))

    @property
    def acls(self):
        """
        Convert data to list of acls ``(GID, UID, ACCESS)``.
        Useful for :const:`LIBSECUR`.

            >>> r = Record(tags.LIBSECUR, [1, 2, 3, 4, 5, 6])
            >>> r.acls
            [(1, 2, 3), (4, 5, 6)]
            >>> r = Record(tags.LIBSECUR, [1, 2, 3, 4]) # wrong data size
            >>> r.acls
            Traceback (most recent call last):
                ...
            DataSizeError: 15106
        """
        if len(self.data) % 3:
            raise exceptions.DataSizeError(self.tag)
        return list(zip(self.data[::3], self.data[1::3], self.data[2::3]))

    @classmethod
    def iterate(cls, stream):
        """
        Generator function for iterating over all records in a GDSII file.
        Yields :class:`Record` objects.

        :param stream: GDS file opened for reading in binary mode
        """
        last = False
        while not last:
            rec = cls.read(stream)
            if rec.tag == tags.ENDLIB:
                last = True
            yield rec

class Reader(object):
    """Class for buffered reading of Records"""
    __slots__  = ('current', 'stream')

    def __init__(self, stream):
        self.stream = stream

    def read_next(self):
        """Read and return next record from stream."""
        self.current = Record.read(self.stream)
        return self.current

if __name__ == '__main__':
    import doctest
    doctest.testmod(optionflags=doctest.IGNORE_EXCEPTION_DETAIL)
