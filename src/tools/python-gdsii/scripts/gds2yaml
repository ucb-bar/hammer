#! /usr/bin/python
# -*- coding: utf-8 -*-
# Copyright © 2010 Eugeniy Meshcheryakov <eugen@debian.org>
# This file is licensed under GNU Lesser General Public License version 3 or later.
from __future__ import print_function
from gdsii.library import Library
from gdsii import elements
import sys
from yaml.dumper import Dumper
from yaml import events

# standard tags
STR = 'tag:yaml.org,2002:str'
TIMESTAMP = 'tag:yaml.org,2002:timestamp'
FLOAT = 'tag:yaml.org,2002:float'
INT = 'tag:yaml.org,2002:int'
SEQ = 'tag:yaml.org,2002:seq'
MAP = 'tag:yaml.org,2002:map'

# non-standard tags
LIBRARY = 'tag:gdsii,2010:library'
STRUCTURE = 'tag:gdsii,2010:structure'

BOUNDARY = 'tag:gdsii,2010:element:boundary'
PATH = 'tag:gdsii,2010:element:path'
SREF = 'tag:gdsii,2010:element:sref'
AREF = 'tag:gdsii,2010:element:aref'
TEXT = 'tag:gdsii,2010:element:text'
NODE = 'tag:gdsii,2010:element:node'
BOX = 'tag:gdsii,2010:element:box'

def emit_string(dumper, prop, tag, value):
    dumper.emit(events.ScalarEvent(None, STR, (True, False), prop))
    dumper.emit(events.ScalarEvent(None, tag, (True, False), value))

def start_named_seq(dumper, name):
    dumper.emit(events.ScalarEvent(None, STR, (True, False), name))
    dumper.emit(events.SequenceStartEvent(None, SEQ, True))

def end_named_seq(dumper):
    dumper.emit(events.SequenceEndEvent())

def simple_dumper(name, tag):
    def dump_fn(dumper, obj):
        value = getattr(obj, name)
        emit_string(dumper, name, tag, str(value))
    return dump_fn

def simple_string_dumper(name):
    def dump_fn(dumper, obj):
        value = getattr(obj, name)
        emit_string(dumper, name, STR, value.decode())
    return dump_fn

def timestamp_dumper(name):
    def dump_fn(dumper, obj):
        value = getattr(obj, name)
        emit_string(dumper, name, TIMESTAMP, value.isoformat(' '))
    return dump_fn

def optional_dumper(name, tag):
    def dump_fn(dumper, obj):
        try:
            value = getattr(obj, name)
        except AttributeError:
            value = None
        if value is not None:
            emit_string(dumper, name, tag, str(value))
    return dump_fn

def optional_flags_dumper(name, tag):
    def dump_fn(dumper, obj):
        try:
            value = getattr(obj, name)
        except AttributeError:
            value = None
        if value is not None:
            emit_string(dumper, name, tag, '0x%x'%value)
    return dump_fn

def xy_dumper(name):
    def dump_fn(dumper, obj):
        points = getattr(obj, name)
        start_named_seq(dumper, name)
        for point in points:
            dumper.emit(events.SequenceStartEvent(None, SEQ, True, flow_style=True))
            dumper.emit(events.ScalarEvent(None, INT, (True, False), str(point[0])))
            dumper.emit(events.ScalarEvent(None, INT, (True, False), str(point[1])))
            dumper.emit(events.SequenceEndEvent())
        end_named_seq(dumper)
    return dump_fn

def properties_dumper(name):
    def dump_fn(dumper, obj):
        properties = getattr(obj, name)
        if (properties):
            start_named_seq(dumper, name)
            for (prop, value) in properties:
                dumper.emit(events.MappingStartEvent(None, MAP, True))
                dumper.emit(events.ScalarEvent(None, INT, (True, False), str(prop)))
                dumper.emit(events.ScalarEvent(None, STR, (True, False), value.decode()))
                dumper.emit(events.MappingEndEvent())
            end_named_seq(dumper)
    return dump_fn

def strans_dumper(name):
    my_dumper = optional_flags_dumper('strans', INT)
    mag = optional_dumper('mag', FLOAT)
    angle = optional_dumper('angle', FLOAT)
    def dump_fn(dumper, obj):
        try:
            value = getattr(obj, name)
        except AttributeError:
            value = None
        if value is not None:
            my_dumper(dumper, obj)
            mag(dumper, obj)
            angle(dumper, obj)
    return dump_fn

elflags = optional_flags_dumper('elflags', INT)
plex = optional_dumper('plex', INT)
layer = simple_dumper('layer', INT)
data_type = simple_dumper('data_type', INT)
path_type = optional_dumper('path_type', INT)
width = optional_dumper('width', INT)
bgn_extn = optional_dumper('bgn_extn', INT)
end_extn = optional_dumper('end_extn', INT)
struct_name = simple_string_dumper('struct_name')
strans = strans_dumper('strans')
cols = simple_dumper('cols', INT)
rows = simple_dumper('rows', INT)
text_type = optional_dumper('text_type', INT)
presentation = optional_flags_dumper('presentation', INT)
string = simple_string_dumper('string')
node_type = simple_dumper('node_type', INT)
box_type = simple_dumper('box_type', INT)
xy = xy_dumper('xy')
properties = properties_dumper('properties')

DUMPERS = (
    (elements.Boundary, BOUNDARY, (elflags, plex, layer, data_type, xy, properties)),
    (elements.Path, PATH, (elflags, plex, layer, data_type, path_type, width, bgn_extn, end_extn, xy, properties)),
    (elements.SRef, SREF, (elflags, plex, struct_name, strans, xy, properties)),
    (elements.ARef, AREF, (elflags, plex, struct_name, strans, cols, rows, xy, properties)),
    (elements.Text, TEXT, (elflags, plex, layer, text_type, presentation, path_type, width, strans, xy, string, properties)),
    (elements.Node, NODE, (elflags, plex, layer, node_type, xy)),
    (elements.Box, BOX, (elflags, plex, layer, box_type, xy, properties))
)

def dump_element(dumper, elem):
    for rec in DUMPERS:
        if isinstance(elem, rec[0]):
            tag = rec[1]
            dumpers = rec[2]
            dumper.emit(events.MappingStartEvent(None, tag, False))
            for fn in dumpers:
                fn(dumper, elem)
            dumper.emit(events.MappingEndEvent())
            break
    else:
        raise Exception('Unsupported element: %s' % str(elem))

name = simple_string_dumper('name')
mod_time = timestamp_dumper('mod_time')
acc_time = timestamp_dumper('acc_time')
strclass = optional_dumper('strclass', INT)

def dump_structure(dumper, struc):
    dumper.emit(events.MappingStartEvent(None, STRUCTURE, False))
    name(dumper, struc)
    mod_time(dumper, struc)
    acc_time(dumper, struc)
    strclass(dumper, struc)
    start_named_seq(dumper, 'elements')
    for elem in struc:
        dump_element(dumper, elem)
    end_named_seq(dumper)
    dumper.emit(events.MappingEndEvent())

physical_unit = simple_dumper('physical_unit', FLOAT)
logical_unit = simple_dumper('logical_unit', FLOAT)
libdirsize = optional_dumper('libdirsize', INT)

def dump_library(dumper, lib):
    dumper.emit(events.StreamStartEvent(encoding='utf-8'))
    dumper.emit(events.DocumentStartEvent(explicit=False))

    dumper.emit(events.MappingStartEvent(None, LIBRARY, False))
    emit_string(dumper, 'version', INT, '0x%x'%lib.version)
    name(dumper, lib)
    mod_time(dumper, lib)
    acc_time(dumper, lib)
    libdirsize(dumper, lib)
    # TODO
    physical_unit(dumper, lib)
    logical_unit(dumper, lib)
    start_named_seq(dumper, 'structures')
    for struc in lib:
        dump_structure(dumper, struc)
    end_named_seq(dumper)
    dumper.emit(events.MappingEndEvent())

    dumper.emit(events.DocumentEndEvent(explicit=False))
    dumper.emit(events.StreamEndEvent())

def main(name):
    with open(name, 'rb') as a_file:
        lib = Library.load(stream=a_file)
    dumper = Dumper(sys.stdout)
    dump_library(dumper, lib)

def usage(prog):
    print('Usage: %s <file.gds>' % prog)

if __name__ == '__main__':
    if (len(sys.argv) > 1):
        main(sys.argv[1])
    else:
        usage(sys.argv[0])
        sys.exit(1)
    sys.exit(0)
