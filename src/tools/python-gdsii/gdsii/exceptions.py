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
:mod:`gdsii.exceptions` --- GDSII exceptions
============================================

This module contains exception classes used in `python-gdsii`.
"""
__all__ = ('FormatError', 'EndOfFileError', 'IncorrectDataSize',
        'UnsupportedTagType', 'MissingRecord', 'DataSizeError')

class FormatError(Exception):
    """Base class for all GDSII exceptions."""

class EndOfFileError(FormatError):
    """Raised on unexpected end of file."""

class IncorrectDataSize(FormatError):
    """Raised if data size is incorrect."""

class UnsupportedTagType(FormatError):
    """Raised on unsupported tag type."""

class MissingRecord(FormatError):
    """Raised when required record is not found."""

class DataSizeError(FormatError):
    """Raised when data size is incorrect for a given record."""
