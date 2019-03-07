#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_metrics.py
#
#  Design metrics traits and utilities for hammer-vlsi
#
#  See LICENSE for licence details.

from hammer_utils import add_dicts
from hammer_vlsi import HammerTool
from abc import abstractmethod
from typing import NamedTuple, Optional, List, Any, Dict, Callable, Union, TextIO
from functools import reduce
import yaml

class ModuleSpec(NamedTuple('ModuleSpec', [
    ('path', List[str])
])):
    __slots__ = ()

class PortSpec(NamedTuple('PortSpec', [
    ('path', List[str])
])):
    __slots__ = ()

# TODO document me
IRType = Dict[str, Union[str, List[str]]]

# I would like to call these "to" and "from" but "from" is a keyword in python
class TimingPathSpec(NamedTuple('TimingPathSpec', [
    ('start', Optional[PortSpec]),
    ('end', Optional[PortSpec]),
    ('through', Optional[PortSpec])
])):
    __slots__ = ()

    # TODO assert that one of the 3 values is not None

class CriticalPathEntry(NamedTuple('CriticalPathEntry', [
    ('module', ModuleSpec),
    ('clock', Optional[PortSpec]), # TODO make this connect to HammerIR clock entry somehow (HammerClockSpec??)
    ('target', Optional[float]),
    ('value', Optional[float])
])):
    __slots__ = ()

    @staticmethod
    def from_ir(ir: IRType) -> CriticalPathEntry:
        # Not yet implemented
        pass

class TimingPathEntry(NamedTuple('TimingPathEntry', [
    ('timing_path', TimingPathSpec),
    ('clock', Optional[PortSpec]), # TODO same as above
    ('target', Optional[float]),
    ('value', Optional[float])
])):
    __slots__ = ()

    @staticmethod
    def from_ir(ir: IRType) -> TimingPathEntry:
        # Not yet implemented
        pass

class ModuleAreaEntry(NamedTuple('ModuleAreaEntry', [
    ('module', ModuleSpec),
    ('value', Optional[float])
])):
    __slots__ = ()

    @staticmethod
    def from_ir(ir: IRType) -> ModuleAreaEntry:
        # Not yet implemented
        pass

# TODO document this
MetricsDBEntry = Union[CriticalPathEntry, TimingPathEntry, ModuleAreaEntry]
#SupportMap = Dict[str, Callable[[str, MetricsDBEntry], List[str]]]
SupportMap = Dict[str, Callable[[str, Any], List[str]]]

FromIRMap = {
    "critical path": CriticalPathEntry.from_ir,
    "timing path": TimingPathEntry.from_ir,
    "area": ModuleAreaEntry.from_ir
} # type: Dict[str, Callable[[IRType], MetricsDBEntry]]

class MetricsDB:

    def __init__(self):
        self._db = {} # type: Dict[str, MetricsDBEntry]

    def create_entry(self, key: str, entry: MetricsDBEntry) -> None:
        if key in self._db:
            raise ValueError("Duplicate entry in MetricsDB: {}".format(key))
        else:
            self._db[key] = entry

    def get_entry(self, key: str) -> MetricsDBEntry:
        if key in self._db:
            return self._db[key]
        else:
            raise ValueError("Entry not found in MetricsDB: {}".format(key))

    @property
    def entries(self) -> Dict[str, MetricsDBEntry]:
        return self._db

class HasMetricSupport(HammerTool):

    @property
    def _support_map(self) -> SupportMap:
        return {}

    def _is_supported(self, entry: MetricsDBEntry) -> bool:
        return (entry.__class__ in self._support_map)

    def create_metrics_db_from_ir(self, ir: Union[str, TextIO]) -> MetricsDB:
        # convert to a dict
        y = yaml.load(ir)
        # create a db
        db = MetricsDB()
        if self.namespace in y:
            testcases = y[self.namespace]
            for testcase in testcases:
                key = "{}.{}".format(self.namespace, testcase)
                testcase_data = testcases[testcase]
                mtype = testcase_data["type"] # type: str
                if mtype in FromIRMap:
                    entry = FromIRMap[mtype](testcase_data) # type: MetricsDBEntry
                    db.create_entry(key, entry)
                else:
                    raise ValueError("Metric IR field <{}> is not supported. Did you forget to update FromIRMap?".format(mtype))
        return db

    def generate_metric_requests_from_db(self, db: MetricsDB) -> List[str]:
        output = [] # type: List[str]
        for key in db.entries:
            entry = db.get_entry(key)
            if self._is_supported(entry):
                output.extend(self._support_map[entry.__class__.__name__](key, entry))
        return output

    def generate_metric_requests_from_ir(self, ir: Union[str, TextIO]) -> List[str]:
        return self.generate_metric_requests_from_db(self.create_metrics_db_from_ir(ir))

    # This will be the key phrase used in the IR
    @property
    @abstractmethod
    def namespace(self) -> str:
        pass

class HasAreaMetricSupport(HasMetricSupport):

    @property
    def _support_map(self) -> SupportMap:
        x = reduce(add_dicts, [super()._support_map, {
            'ModuleAreaEntry': self.get_module_area
        }]) # type: SupportMap
        return x

    @abstractmethod
    def get_module_area(self, key: str, entry: ModuleAreaEntry) -> List[str]:
        pass

class HasTimingPathMetricSupport(HasMetricSupport):

    @property
    def _support_map(self) -> SupportMap:
        x = reduce(add_dicts, [super()._support_map, {
            'CriticalPathEntry': self.get_critical_path,
            'TimingPathEntry': self.get_timing_path
        }]) # type: SupportMap
        return x

    @abstractmethod
    def get_critical_path(self, key: str, entry: CriticalPathEntry) -> List[str]:
        pass

    @abstractmethod
    def get_timing_path(self, key: str, entry: TimingPathEntry) -> List[str]:
        pass
