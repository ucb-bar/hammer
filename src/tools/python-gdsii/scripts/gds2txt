#! /usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2010 Eugeniy Meshcheryakov <eugen@debian.org>
# This file is licensed under GNU Lesser General Public License version 3 or later.
"""Demonstration program for basic gdsii reading function."""
from __future__ import print_function
from gdsii import types
from gdsii.record import Record
import sys

def show_data(rec):
    """Shows data in a human-readable format."""
    if rec.tag_type == types.ASCII:
        return '"%s"' % rec.data.decode() # TODO escape
    elif rec.tag_type == types.BITARRAY:
        return str(rec.data)
    return ', '.join('{0}'.format(i) for i in rec.data)

def main(name):
    with open(name, 'rb') as a_file:
        for rec in Record.iterate(a_file):
            if rec.tag_type == types.NODATA:
                print(rec.tag_name)
            else:
                print('%s: %s' % (rec.tag_name, show_data(rec)))

def usage(prog):
    print('Usage: %s <file.gds>' % prog)

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        main(sys.argv[1])
    else:
        usage(sys.argv[0])
        sys.exit(1)
    sys.exit(0)
