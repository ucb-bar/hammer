#! /usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2011 Eugeniy Meshcheryakov <eugen@debian.org>
# This file is licensed under GNU Lesser General Public License version 3 or later.
"""Converter from format produced by gds2txt back to GDSII."""
from __future__ import print_function
from gdsii import tags, types
from gdsii.record import Record
import sys
import getopt
import re

def parse_file(ifile, ofile):
    rexp = re.compile(r'^(?P<tag>[^:]+)(:\s*(?P<rest>.*))?$')
    lineno = 1
    for line in ifile:
        stripped = line.strip()
        m = rexp.match(stripped)
        if not m:
            print('Parse error at line {0}'.format(lineno), file=sys.stderr)
            sys.exit(1)
        tag_name = m.group('tag')
        rest = m.group('rest')

        tag = tags.DICT[tag_name]

        tag_type = tags.type_of_tag(tag)

        if tag_type == types.NODATA:
            data = None
        elif tag_type == types.ASCII:
            data = rest[1:-1].encode() # FIXME
        elif tag_type == types.BITARRAY:
            data = int(rest)
        elif tag_type == types.REAL8:
            data = [float(s) for s in rest.split(',')]
        elif tag_type == types.INT2 or tag_type == types.INT4:
            data = [int(s) for s in rest.split(',')]
        else:
            raise Exception('Unsupported type')
        rec = Record(tag, data)
        rec.save(ofile)
        lineno += 1

def main(argv):
    opts, args = getopt.gnu_getopt(argv[1:], 'o:')
    if len(opts) != 1 or opts[0][0] != '-o' or len(args) > 1:
        usage(argv[0])
        sys.exit(2)
    with open(opts[0][1], 'wb') as ofile:
        if len(args) == 0:
            parse_file(sys.stdin, ofile)
        else:
            with open(args[0], 'r') as ifile:
                parse_file(ifile, ofile)

def usage(prog):
    print('Usage: %s -o <file.gds> [<input.txt>]' % prog)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv)
    else:
        usage(sys.argv[0])
        sys.exit(1)
