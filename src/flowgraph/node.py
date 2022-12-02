#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Represents a flowgraph in HAMMER that can be run and verified.
#  See README.config for more details.
#
#  See LICENSE for licence details.

# pylint: disable=invalid-name

import json
import queue
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Optional

import networkx as nx


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
    push_dir:          str
    pull_dir:          str
    required_inputs:   list[str]
    required_outputs:  list[str]
    children:          list
    optional_inputs:   list[str] = field(default_factory=list)
    optional_outputs:  list[str] = field(default_factory=list)
    status:            Status = Status.NOT_RUN

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
            tuple(self.children),
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
    root: Node

    def __post_init__(self) -> None:
        self.networkx = self.to_networkx()

    def to_json(self, indent: Optional[int] = None) -> str:
        """Writes the graph as a JSON string and saves it to a file.

        Returns:
            dict: Entire flowgraph as a JSON.
        """
        out_dict = asdict(self.root)
        return json.dumps(out_dict, indent=indent, cls=StatusEncoder)

    def to_networkx(self) -> nx.DiGraph:
        """Turns our graph into an NetworkX directed graph.

        Returns:
            nx.DiGraph: NetworkX directed graph.
        """
        q = queue.LifoQueue()
        explored = []
        q.put(self.root)
        edge_list = {}
        while not q.empty():
            v = q.get()
            if v not in explored:
                explored.append(v)
                edge_list[v] = tuple(c for c in v.children)
                for c in v.children:
                    q.put(c)
        return nx.DiGraph(edge_list)

    @staticmethod
    def from_json(dump: str) -> dict:
        """Converts a JSON into an instance of Graph.

        Args:
            dump (str): JSON with the correct schema for a Graph.

        Returns:
            dict: Dictionary containing graph information.
        """
        return json.loads(dump, object_hook=as_status)

    def verify(self) -> bool:
        """Checks if a graph is valid via its inputs and outputs.

        Returns:
            bool: If graph is valid.
        """
        return all(self.__process(v) for v in nx.nodes(self.networkx))

    def __process(self, v: Node) -> bool:
        """Process a specific vertex of a graph.

        Args:
            v (Node): Node to check the validity of.

        Returns:
            bool: If the particular node is valid.
        """
        if v == self.root:
            return True
        parent_outs = \
            set().union(*(set(p.required_outputs) for p in self.networkx.predecessors(v))) \
            | set().union(*(set(p.optional_outputs) for p in self.networkx.predecessors(v)))
        inputs = set(v.required_inputs) | set(v.optional_inputs)
        return parent_outs >= inputs


def convert_to_acyclic(g: Graph) -> Graph:
    """Eliminates cycles in a flowgraph for analysis.

    Args:
        g (Graph): (presumably) cyclic graph to transform.

    Returns:
        Graph: Graph with cloned nodes.
    """
    g_copy = deepcopy(g)
    cycles = nx.simple_cycles(g_copy.networkx)
    for cycle in cycles:
        start, end = cycle[0], cycle[1]
        end_copy = deepcopy(end)
        end_copy.children = []
        start.children[start.children.index(end)] = end_copy
        print(start.children[start.children.index(end_copy)].children)
    return Graph(g_copy.root)
