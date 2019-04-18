#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_metrics.py
#
#  Design metrics traits and utilities for hammer-vlsi
#
#  See LICENSE for licence details.

from hammer_utils import add_dicts, get_or_else
from hammer_vlsi import HammerTool
from abc import abstractmethod
from typing import NamedTuple, Optional, List, Any, Dict, Callable, Union, TextIO
from functools import reduce
import yaml
import copy
import os

# Note: Do not include the top module in the module spec
# e.g. [] = root
#      ['inst1'] = inst at first level of hierarchy
class ModuleSpec(NamedTuple('ModuleSpec', [
    ('path', List[str])
])):
    __slots__ = ()

    @staticmethod
    def from_str(s: str) -> 'ModuleSpec':
        return ModuleSpec(list(filter(lambda x: x != '', s.split("/"))))

    def append(self, child: str) -> 'ModuleSpec':
        return ModuleSpec(self.path + [child])

    @property
    def is_top(self) -> bool:
        return len(self.path) == 0

    @property
    def to_str(self) -> str:
        return "/".join(self.path)

class PortSpec(NamedTuple('PortSpec', [
    ('module', ModuleSpec),
    ('port', str)
])):
    __slots__ = ()

    @staticmethod
    def from_str(s: str) -> 'PortSpec':
        tmp = s.split(':')
        if len(tmp) != 2:
            raise ValueError("Invalid port spec: " + s)
        mod = ModuleSpec.from_str(tmp[0])
        return PortSpec(mod, tmp[1])

    @property
    def to_str(self) -> str:
        return self.module.to_str + ":" + self.port

# TODO document me
IRType = Dict[str, Union[str, List[str]]]

class MetricsDBEntry:

    @abstractmethod
    def register(self, db: 'MetricsDB') -> None:
        pass

    @abstractmethod
    def update(self, d: Dict[str, Any]) -> 'MetricsDBEntry':
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass

class CriticalPathEntry(NamedTuple('CriticalPathEntry', [
    ('module', ModuleSpec),
    ('clock', Optional[PortSpec]), # TODO make this connect to HammerIR clock entry somehow (HammerClockSpec??)
    ('target', Optional[float]),
    ('value', Optional[float])
]), MetricsDBEntry):
    __slots__ = ()

    @staticmethod
    def from_ir(ir: IRType) -> 'CriticalPathEntry':
        try:
            module = ir["module"]
            clock = ir["clock"] if "clock" in ir else ""
            assert isinstance(module, str)
            assert isinstance(clock, str)
            return CriticalPathEntry(
                ModuleSpec.from_str(module),
                PortSpec.from_str(clock) if "clock" in ir else None,
                None,
                None)
        except:
            raise ValueError("Invalid IR for CriticalPathEntry: {}".format(ir))

    @staticmethod
    def type_string() -> str:
        return 'critical path'

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        d['type'] = self.__class__.type_string()
        d['module'] = self.module.to_str
        d['clock'] = self.clock.to_str
        d['target'] = str(get_or_else(self.target, "null"))
        d['value'] = str(get_or_else(self.value, "null"))
        return d

    def register(self, db: 'MetricsDB') -> None:
        db.module_tree.add_module(self.module)

    def update(self, d: Dict[str, Any]) -> MetricsDBEntry:
        target = d['target'] if 'target' in d else self.target
        value = d['value'] if 'value' in d else self.value
        return CriticalPathEntry(self.module, self.clock, target, value)

class ModuleAreaEntry(NamedTuple('ModuleAreaEntry', [
    ('module', ModuleSpec),
    ('value', Optional[float])
]), MetricsDBEntry):
    __slots__ = ()

    @staticmethod
    def from_ir(ir: IRType) -> 'ModuleAreaEntry':
        try:
            mod = ir["module"]
            assert isinstance(mod, str)
            return ModuleAreaEntry(
                ModuleSpec.from_str(mod),
                None)
        except:
            raise ValueError("Invalid IR for ModuleAreaEntry: {}".format(ir))

    @staticmethod
    def type_string() -> str:
        return 'area'

    def to_dict(self) -> Dict[str, Any]:
        d = {}
        d['type'] = self.__class__.type_string()
        d['module'] = self.module.to_str
        d['value'] = str(get_or_else(self.value, "null"))
        return d

    def register(self, db: 'MetricsDB') -> None:
        db.module_tree.add_module(self.module)

    def update(self, d: Dict[str, Any]) -> MetricsDBEntry:
        value = d['value'] if 'value' in d else self.value
        return ModuleAreaEntry(self.module, value)

# TODO document this
#MetricsDBEntry = Union[CriticalPathEntry, ModuleAreaEntry]
#SupportMap = Dict[str, Callable[[str, MetricsDBEntry], List[str]]]
SupportMap = Dict[str, Callable[[str, Any], List[str]]]

FromIRMap = {
    CriticalPathEntry.type_string(): CriticalPathEntry.from_ir,
    ModuleAreaEntry.type_string(): ModuleAreaEntry.from_ir
} # type: Dict[str, Callable[[IRType], MetricsDBEntry]]

class ModuleTree:

    index = 0

    def __init__(self):
        self._children = {} # type: Dict[str, ModuleTree]
        self._rename_id = ModuleTree.index
        ModuleTree.index += 1
        self._no_ungroup = False
        # More properties go here

    def get_or_create_node(self, name: str) -> 'ModuleTree':
        if name in self._children:
            return self._children[name]
        else:
            node = ModuleTree()
            self._children[name] = node
            return node

    def get_no_ungroup_paths(self, prefix: Optional[ModuleSpec] = None) -> List[ModuleSpec]:
        result = [] # type: List[ModuleSpec]
        for name, child in self._children.items():
            new_prefix = ModuleSpec([name])
            if prefix is not None:
                new_prefix = prefix.append(name)
            if child.get_no_ungroup:
                result.append(new_prefix)
            result.extend(child.get_no_ungroup_paths(new_prefix))
        return result

    def add_module(self, m: ModuleSpec) -> 'ModuleTree':
        child = self.get_or_create_node(m.path[0])
        if len(m.path) > 1:
            return child.add_module(ModuleSpec(m.path[1:]))
        else:
            return child

    @property
    def get_no_ungroup(self) -> bool:
        return self._no_ungroup

    def set_no_ungroup(self, val: bool = True) -> None:
        self._no_ungroup = val

    @property
    def is_leaf(self) -> bool:
        return len(self._children) == 0

class MetricsDB:

    def __init__(self):
        self._db = {} # type: Dict[str, Dict[str, MetricsDBEntry]]
        self._tree = ModuleTree()

    def create_entry(self, namespace: str, key: str, entry: MetricsDBEntry) -> None:
        if namespace not in self._db:
            self._db[namespace] = {} # type = Dict[str, MetricsDBEntry]
        if key in self._db[namespace]:
            raise ValueError("Duplicate entry in MetricsDB: {}".format(key))
        else:
            self._db[namespace][key] = entry

    def get_entry(self, namespace: str, key: str) -> MetricsDBEntry:
        if namespace in self._db:
            if key in self._db[namespace]:
                return self._db[namespace][key]
            else:
                raise ValueError("Entry not found in MetricsDB: {}".format(key))
        else:
            raise ValueError("Namespace not found in MetricsDB: {}".format(namespace))

    def update_entry(self, namespace: str, key: str, d: Dict[str, Any]) -> MetricsDBEntry:
        if namespace in self._db:
            if key in self._db[namespace]:
                self._db[namespace][key] = self._db[namespace][key].update(d)
                return self._db[namespace][key]
            else:
                raise ValueError("Entry not found in MetricsDB: {}".format(key))
        else:
            raise ValueError("Namespace not found in MetricsDB: {}".format(namespace))


    def entries(self, namespace: str) -> Dict[str, MetricsDBEntry]:
        if namespace in self._db:
            return self._db[namespace]
        else:
            raise ValueError("Namespace not found in MetricsDB: {}".format(namespace))

    def serialize(self) -> str:
        d = {}
        for namespace in self._db:
            d[namespace] = {}
            for testcase in self._db[namespace]:
                d[namespace][testcase] = self._db[namespace][testcase].to_dict()
        return yaml.dump(d)


    @property
    def module_tree(self) -> ModuleTree:
        return self._tree

class HasMetricSupport(HammerTool):

    @property
    def _support_map(self) -> SupportMap:
        return {}

    def _is_supported(self, entry: MetricsDBEntry) -> bool:
        return (entry.__class__.__name__ in self._support_map)

    def create_metrics_db_from_ir(self, ir: Union[str, TextIO]) -> MetricsDB:
        # convert to a dict
        y = yaml.load(ir) # type: Optional[Dict[str, Any]]
        if y is None:
            y = {}
        assert(isinstance(y, dict))
        # create a db
        db = MetricsDB()
        for namespace in y:
            testcases = y[namespace]
            for testcase in testcases:
                testcase_data = testcases[testcase]
                if "type" not in testcase_data:
                    raise ValueError("Missing \"type\" field in testcase {}".format(testcase))
                mtype = testcase_data["type"] # type: str
                if mtype in FromIRMap:
                    entry = FromIRMap[mtype](testcase_data) # type: MetricsDBEntry
                    db.create_entry(namespace, testcase, entry)
                else:
                    raise ValueError("Metric IR field <{}> is not supported. Did you forget to update FromIRMap?".format(mtype))
        return db

    def generate_metric_requests_from_db(self, db: MetricsDB) -> List[str]:
        output = [] # type: List[str]
        for key in db.entries(self.namespace):
            entry = db.get_entry(self.namespace, key)
            if self._is_supported(entry):
                output.extend(self._support_map[entry.__class__.__name__](key, entry))
        return output

    def generate_metric_requests_from_ir(self, ir: Union[str, TextIO]) -> List[str]:
        # TODO initialize this elsewhere
        self.metrics_db = self.create_metrics_db_from_ir(ir)
        return self.generate_metric_requests_from_db(self.metrics_db)

    def generate_metric_requests_from_file(self, filename: str) -> List[str]:
        if not os.path.isfile(filename):
            raise ValueError("Metrics IR file {} does not exist or is not a file".format(filename))
        with open(filename, "r") as f:
            return self.generate_metric_requests_from_ir(f)

    # This will be the key phrase used in the IR
    @property
    @abstractmethod
    def namespace(self) -> str:
        pass

    def read_results_into_db(self, d: Dict[str, Any]) -> str:
        for testcase in d:
            testcase_data = d[testcase]
            self.metrics_db.update_entry(self.namespace, testcase, testcase_data)

class HasAreaMetricSupport(HasMetricSupport):

    @property
    def _support_map(self) -> SupportMap:
        x = copy.copy(super()._support_map) # type: SupportMap
        x.update({
            'ModuleAreaEntry': self.get_module_area
        })
        return x

    @abstractmethod
    def get_module_area(self, key: str, entry: ModuleAreaEntry) -> List[str]:
        pass

class HasTimingPathMetricSupport(HasMetricSupport):

    @property
    def _support_map(self) -> SupportMap:
        x = copy.copy(super()._support_map) # type: SupportMap
        x.update({
            'CriticalPathEntry': self.get_critical_path
        })
        return x

    @abstractmethod
    def get_critical_path(self, key: str, entry: CriticalPathEntry) -> List[str]:
        pass

