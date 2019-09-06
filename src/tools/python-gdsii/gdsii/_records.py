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
from __future__ import absolute_import
from . import record, tags

class AbstractRecord(object):
    def __init__(self, variable):
        self.variable = variable

    def read(self, instance, gen):
        raise NotImplementedError

    def save(self, instance, stream):
        raise NotImplementedError

    def __repr__(self):
        return '<property: %s>'%self.variable

class SecondVar(object):
    """Class that simplifies second property support."""
    def __init__(self, variable2):
        self.variable2 = variable2

class SimpleRecord(AbstractRecord):
    def __init__(self, variable, gds_record):
        AbstractRecord.__init__(self, variable)
        self.gds_record = gds_record

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        rec.check_size(1)
        setattr(instance, self.variable, rec.data[0])
        gen.read_next()

    def save(self, instance, stream):
        record.Record(self.gds_record, (getattr(instance, self.variable),)).save(stream)

class SimpleOptionalRecord(SimpleRecord):
    def optional_read(self, instance, unused_gen, rec):
        """
        Called when optional tag is found. `rec` contains that tag.
        `gen` is advanced to next record befor calling this function.
        """
        rec.check_size(1)
        setattr(instance, self.variable, rec.data[0])

    def read(self, instance, gen):
        rec = gen.current
        if rec.tag == self.gds_record:
            gen.read_next()
            self.optional_read(instance, gen, rec)

    def save(self, instance, stream):
        data = getattr(instance, self.variable, None)
        if data is not None:
            record.Record(self.gds_record, (data,)).save(stream)

class OptionalWholeRecord(SimpleOptionalRecord):
    """Class for records that need to store all data (not data[0])."""
    def optional_read(self, instance, unused_gen, rec):
        setattr(instance, self.variable, rec.data)

    def save(self, instance, stream):
        data = getattr(instance, self.variable, None)
        if data is not None:
            record.Record(self.gds_record, data).save(stream)

class PropertiesRecord(AbstractRecord):
    def read(self, instance, gen):
        rec = gen.current
        props = []
        while rec.tag == tags.PROPATTR:
            rec.check_size(1)
            propattr = rec.data[0]
            rec = gen.read_next()
            rec.check_tag(tags.PROPVALUE)
            props.append((propattr, rec.data))
            rec = gen.read_next()
        setattr(instance, self.variable, props)

    def save(self, instance, stream):
        props = getattr(instance, self.variable)
        if props:
            for (propattr, propvalue) in props:
                record.Record(tags.PROPATTR, (propattr,)).save(stream)
                record.Record(tags.PROPVALUE, propvalue).save(stream)

class XYRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        setattr(instance, self.variable, rec.points)
        gen.read_next()

    def save(self, instance, stream):
        pts = getattr(instance, self.variable)
        record.Record(self.gds_record, points=pts).save(stream)

class StringRecord(SimpleRecord):
    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        setattr(instance, self.variable, rec.data)
        gen.read_next()

    def save(self, instance, stream):
        record.Record(self.gds_record, getattr(instance, self.variable)).save(stream)

class ColRowRecord(AbstractRecord, SecondVar):
    def __init__(self, variable1, variable2):
        AbstractRecord.__init__(self, variable1)
        SecondVar.__init__(self, variable2)

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(tags.COLROW)
        rec.check_size(2)
        cols, rows = rec.data
        setattr(instance, self.variable, cols)
        setattr(instance, self.variable2, rows)
        gen.read_next()

    def save(self, instance, stream):
        col = getattr(instance, self.variable)
        row = getattr(instance, self.variable2)
        record.Record(tags.COLROW, (col, row)).save(stream)

class TimestampsRecord(SimpleRecord, SecondVar):
    def __init__(self, variable1, variable2, gds_record):
        SimpleRecord.__init__(self, variable1, gds_record)
        SecondVar.__init__(self, variable2)

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        mod_time, acc_time = rec.times
        setattr(instance, self.variable, mod_time)
        setattr(instance, self.variable2, acc_time)
        gen.read_next()

    def save(self, instance, stream):
        mod_time = getattr(instance, self.variable)
        acc_time = getattr(instance, self.variable2)
        record.Record(self.gds_record, times=(mod_time, acc_time)).save(stream)

class STransRecord(OptionalWholeRecord):
    mag = SimpleOptionalRecord('mag', tags.MAG)
    angle = SimpleOptionalRecord('angle', tags.ANGLE)

    def optional_read(self, instance, gen, rec):
        setattr(instance, self.variable, rec.data)
        self.mag.read(instance, gen)
        self.angle.read(instance, gen)

    def save(self, instance, stream):
        data = getattr(instance, self.variable, None)
        if data is not None:
            OptionalWholeRecord.save(self, instance, stream)
            self.mag.save(instance, stream)
            self.angle.save(instance, stream)

class ACLRecord(SimpleOptionalRecord):
    def optional_read(self, instance, unused_gen, rec):
        setattr(instance, self.variable, rec.acls)

    def save(self, instance, stream):
        data = getattr(instance, self.variable, None)
        if data:
            record.Record(self.gds_record, acls=data).save(stream)

class FormatRecord(SimpleOptionalRecord, SecondVar):
    def __init__(self, variable1, variable2, gds_record):
        SimpleOptionalRecord.__init__(self, variable1, gds_record)
        SecondVar.__init__(self, variable2)

    def optional_read(self, instance, gen, rec):
        SimpleOptionalRecord.optional_read(self, instance, gen, rec)
        cur_rec = gen.curent
        if cur_rec.tag == tags.MASK:
            masks = []
            while cur_rec.tag == tags.MASK:
                masks.append(cur_rec.data)
                cur_rec = gen.read_next()
            cur_rec.check_tag(tags.ENDMASKS)
            setattr(instance, self.variable2, masks)
            gen.read_next()

    def save(self, instance, stream):
        fmt = getattr(instance, self.variable, None)
        if fmt is not None:
            SimpleOptionalRecord.save(self, instance, stream)
            masks = getattr(instance, self.variable2, None)
            if masks:
                for mask in masks:
                    record.Record(tags.MASK, mask).save(stream)
                record.Record(tags.ENDMASKS).save(stream)

class UnitsRecord(SimpleRecord, SecondVar):
    def __init__(self, variable1, variable2, gds_record):
        SimpleRecord.__init__(self, variable1, gds_record)
        SecondVar.__init__(self, variable2)

    def read(self, instance, gen):
        rec = gen.current
        rec.check_tag(self.gds_record)
        rec.check_size(2)
        unit1, unit2 = rec.data
        setattr(instance, self.variable, unit1)
        setattr(instance, self.variable2, unit2)
        gen.read_next()

    def save(self, instance, stream):
        unit1 = getattr(instance, self.variable)
        unit2 = getattr(instance, self.variable2)
        record.Record(self.gds_record, (unit1, unit2)).save(stream)
