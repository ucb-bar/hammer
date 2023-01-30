#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Represents a flowgraph in HAMMER that can be run and verified.
#  See README.config for more details.
#
#  See LICENSE for licence details.

# pylint: disable=invalid-name

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum

import networkx as nx

from hammer.vlsi import cli_driver


class Status(Enum):
    """Represents the status of a node in the flowgraph.
    https://tinyurl.com/2bstth7y
    """
    NOT_RUN    = "NOT_RUN"
    RUNNING    = "RUNNING"
    INCOMPLETE = "INCOMPLETE"
    INVALID    = "INVALID"
    COMPLETE   = "COMPLETE"


class StatusEncoder(json.JSONEncoder):
    def default(self, o: Status) -> str:
        if isinstance(o, Status):
            return o.name
        return super().default(o)


def as_status(dct):
    if "status" in dct:
        dct["status"] = Status[dct["status"]]
    return dct


# make sure union of required/optional outs is superset of children required/optional inputs
# separate required validity checking and optional validity checking
# meta dict for tech compatibilty
# for cycles, reduce to DAG via cloning of one of the nodes

@dataclass
class Node:
    action:            str
    tool:              str
    pull_dir:          str
    push_dir:          str
    required_inputs:   list[str]
    required_outputs:  list[str]
    status:            Status    = Status.NOT_RUN
    __uuid:            uuid.UUID = field(default_factory=uuid.uuid4)
    optional_inputs:   list[str] = field(default_factory=list)
    optional_outputs:  list[str] = field(default_factory=list)

    def __key(self) -> tuple:
        """Key value for hashing.

        Returns:
            tuple: All fields concatenated.
        """
        return (
            self.action,
            self.tool,
            self.push_dir,
            self.pull_dir,
            tuple(self.required_inputs),
            tuple(self.required_outputs),
            tuple(self.optional_inputs),
            tuple(self.optional_outputs),
            self.status
        )

    def __hash__(self) -> int:
        return hash(self.__key)

    def to_json(self) -> dict:
        """Writes the node to a JSON string.

        Args:
            fname (str): File name to write to.

        Returns:
            str: Node represented as a JSON.
        """
        return asdict(self)


@dataclass
class Graph:
    edge_list: dict[Node, list[Node]]

    def __post_init__(self) -> None:
        self.networkx = nx.DiGraph(self.edge_list)

    def verify(self) -> bool:
        """Checks if a graph is valid via its inputs and outputs.

        Returns:
            bool: If graph is valid.
        """
        return all(self.__process(v) for v in convert_to_acyclic(self).networkx)

    def __process(self, v: Node) -> bool:
        """Process a specific vertex of a graph.

        Args:
            v (Node): Node to check the validity of.

        Returns:
            bool: If the particular node is valid.
        """
        parent_outs = \
            set().union(*(set(p.required_outputs) for p in self.networkx.predecessors(v))) \
            | set().union(*(set(p.optional_outputs) for p in self.networkx.predecessors(v)))
        inputs = set(v.required_inputs) | set(v.optional_inputs)
        return self.networkx.in_degree(v) == 0 or parent_outs >= inputs

    def run(self, start: Node) -> None:
        """Run a HAMMER flowgraph."""
        if not self.verify():
            raise RuntimeError("Flowgraph is invalid")
        if start not in self.networkx:
            raise RuntimeError("Node not in flowgraph")

        start.status = Status.RUNNING
        arg_list = {
            "action": start.action,
            'environment_config': None,
            'configs': [os.path.join(start.pull_dir, i) for i in start.required_inputs],
            'log': None,
            'obj_dir': start.push_dir,
            'syn_rundir': '',
            'par_rundir': '',
            'drc_rundir': '',
            'lvs_rundir': '',
            'sim_rundir': '',
            'power_rundir': '',
            'formal_rundir': '',
            'timing_rundir': '',
            # TODO: sub-step determinations
            'from_step': None,
            'after_step': None,
            'to_step': None,
            'until_step': None,
            'only_step': None,
            'output': 'output.json',
            'verilog': None,
            'firrtl': None,
            'top': None,
            'cad_files': None
        }

        driver = cli_driver.CLIDriver()
        try:
            driver.run_main_parsed(arg_list)
            start.status = Status.COMPLETE
            for c in nx.neighbors(self.networkx, start):
                self.run(c)
        except Exception as e:
            start.status = Status.INCOMPLETE
            raise e

def convert_to_acyclic(g: Graph) -> Graph:
    """Eliminates cycles in a flowgraph for analysis.

    Args:
        g (Graph): (presumably) cyclic graph to transform.

    Returns:
        Graph: Graph with cloned nodes.
    """
    cycles = sorted(nx.simple_cycles(g.networkx))
    new_edge_list = g.edge_list.copy()
    for cycle in cycles:
        cut_start, cut_end = cycle[0], cycle[1]
        cut_end_copy = Node(
            cut_end.action,
            cut_end.tool,
            cut_end.pull_dir, cut_end.push_dir,
            cut_end.required_inputs, cut_end.required_outputs,
            cut_end.status,
            cut_end.optional_inputs, cut_end.optional_outputs
        )
        cut_start_children = new_edge_list[cut_start]
        new_edge_list[cut_start] = []
        new_edge_list[cut_end_copy] = cut_start_children
    return Graph(new_edge_list)

# TODO: refresh graph
