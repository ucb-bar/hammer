#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Represents a flowgraph in HAMMER that can be run and verified.
#  See README.config for more details.
#
#  See LICENSE for licence details.

# pylint: disable=invalid-name

import importlib
import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Union

import networkx as nx
from networkx.readwrite import json_graph

from hammer.logging import HammerVLSILogging
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


# separate required validity checking and optional validity checking
# meta dict for tech compatibilty

@dataclass
class Node:
    """Defines a node for an action in a flowgraph.

    Returns:
        Node: Complete description of an action.
    """
    action:            str
    tool:              str
    pull_dir:          str
    push_dir:          str
    required_inputs:   list[str]
    required_outputs:  list[str]
    status:            Status    = Status.NOT_RUN
    # __uuid:            uuid.UUID = field(default_factory=uuid.uuid4)
    driver:            str       = ""
    optional_inputs:   list[str] = field(default_factory=list)
    optional_outputs:  list[str] = field(default_factory=list)
    step_controls:     dict[str, str] = field(default_factory=lambda: {
        "from_step": "",
        "after_step": "",
        "to_step": "",
        "until_step": "",
        "only_step": "",
    })

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
            self.status,
            tuple(self.step_controls.items())
        )

    def __hash__(self) -> int:
        """Dunder method for uniquely hashing a `Node` object.

        Returns:
            int: Hash of a `Node`.
        """
        return hash(self.__key)

    def __is_privileged(self) -> bool:
        """Private method for checking if
        step control is applied to a `Node`.

        Returns:
            bool: If the node is allowed to be the starting point of a flow.
        """
        return any(i != "" for i in self.step_controls.values())

    @property
    def privileged(self) -> bool:
        """Property for determining node privilege.

        Returns:
            bool: If the node is allowed to be the starting point of a flow.
        """
        return self.__is_privileged()

class NodeEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Node):
            return asdict(o)
        elif isinstance(o, Status):
            return o.value
        return super().default(o)

def as_node(dct: dict) -> Union[Node, dict]:
    if "action" in dct:
        return Node(
            dct["action"],
            dct["tool"],
            dct["pull_dir"],
            dct["push_dir"],
            dct["required_inputs"],
            dct["required_outputs"],
            Status(dct["status"]),
            dct["optional_inputs"],
            dct["optional_outputs"],
        )
    return dct

@dataclass
class Graph:
    """Defines a flowgraph.

    Returns:
        Graph: HAMMER flowgraph.
    """
    edge_list: dict[Node, list[Node]]
    auto_auxiliary: bool = True

    def __post_init__(self) -> None:
        self.networkx = nx.DiGraph(Graph.insert_auxiliary_actions(self.edge_list) if self.auto_auxiliary else self.edge_list)

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

    @staticmethod
    def insert_auxiliary_actions(edge_list: dict[Node, list[Node]]) -> dict[Node, list[Node]]:
        """Inserts x-to-y actions between two semantically related actions (e.g. if syn and par are connected, then we have to insert a syn-to-par node here).

        Args:
            edge_list (dict[Node, list[Node]]): Edge list without auxiliary actions.

        Returns:
            dict[Node, list[Node]]: Transformed edge list with auxiliary actions.
        """
        valid_auxiliary_actions = [
            ("synthesis", "par"),
            ("syn", "par"),
            ("heir-par", "syn"),
            ("heir_par", "syn"),
            ("par", "drc"),
            ("par", "lvs"),
            ("synthesis", "sim"),
            ("syn", "sim"),
            ("par", "sim"),
            ("syn", "power"),
            ("par", "power"),
            ("sim", "power"),
            ("synthesis", "formal"),
            ("syn", "formal"),
            ("par", "formal"),
            ("synthesis", "timing"),
            ("syn", "timing"),
            ("par", "timing"),
        ]

        changes = []
        edge_list_copy = edge_list.copy()
        for parent_idx, (parent, children) in enumerate(edge_list.items()):
            for child_idx, child in enumerate(children):
                if (parent.action, child.action) in valid_auxiliary_actions:
                    aux_action = f"{parent.action}-to-{child.action}"
                    aux_node = Node(
                        aux_action,
                        parent.tool,
                        os.path.join(os.path.dirname(parent.pull_dir), f"{aux_action}-dir"),
                        child.pull_dir,
                        parent.required_outputs,
                        [f"{aux_action}-out.json"],
                    )
                    changes.append((parent_idx, child_idx, aux_node))

        for parent_idx, child_idx, aux_node in changes:
            parent, children = list(edge_list_copy.items())[parent_idx]
            parent.push_dir = os.path.join(
                os.path.dirname(parent.pull_dir),
                f"{aux_node.action}-dir")

            child = children[child_idx]
            child.required_inputs = aux_node.required_outputs

            children[child_idx] = aux_node
            if aux_node not in edge_list_copy:
                edge_list_copy[aux_node] = []
            edge_list_copy[aux_node].append(child)
        return edge_list_copy


    def run(self, start: Node) -> Any:
        """Runs a flowgraph.

        Args:
            start (Node): Node to start the run on.

        Raises:
            RuntimeError: If the flowgraph is invalid.
            RuntimeError: If the starting node is not in the flowgraph.
        """
        if not self.verify():
            raise RuntimeError("Flowgraph is invalid. Please check your flow's inputs and outputs.")
        if start not in self.networkx:
            raise RuntimeError("Node not in flowgraph. Did you construct the graph correctly?")
        if not start.privileged and any(i.privileged for i in self.networkx):
            raise RuntimeError("Attempting to run non-privileged node in privileged flow. Please complete your stepped flow first.")

        if start.driver != "":
            driver_pkg_path, driver_module = start.driver.rsplit('.', 1)
            driver_pkg = importlib.import_module(driver_pkg_path)
            driver = getattr(driver_pkg, driver_module)()
            if not isinstance(driver, cli_driver.CLIDriver):
                raise TypeError(f"Driver {driver} does not extend CLIDriver, cannot run a flow.")
        else:
            driver = cli_driver.CLIDriver()

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
            'from_step': start.step_controls["from_step"],
            'after_step': start.step_controls["after_step"],
            'to_step': start.step_controls["to_step"],
            'until_step': start.step_controls["until_step"],
            'only_step': start.step_controls["only_step"],
            'output': os.path.join(start.push_dir, start.required_outputs[0]),  # TODO: fix this
            'verilog': None,
            'firrtl': None,
            'top': None,
            'cad_files': None,
            'dump_history': False
        }

        start.status = Status.RUNNING
        ctxt = HammerVLSILogging.context(start.action)
        ctxt.info(f"Running graph step {start.action}")
        code = driver.run_main_parsed(arg_list)
        if code == 0:
            start.status = Status.COMPLETE
        else:
            start.status = Status.INCOMPLETE
            ctxt.fatal(f"Step {start.action} failed")
            return self

        for c in nx.neighbors(self.networkx, start):
            self.run(c)

        return self

    def to_json(self) -> dict:
        """Encodes a graph as a JSON string.

        Returns:
            str: JSON dump of a flowgraph.
        """
        return json_graph.node_link_data(self.networkx)

    def to_d2(self) -> Any:
        raise NotImplementedError()

    def to_mermaid(self) -> str:
        """Converts the flowgraph into Mermaid format for visualization.

        Args:
            fname (str): Output file name.

        Returns:
            str: Path to Mermaid Markdown file.
        """
        folder = os.path.dirname(list(self.networkx.nodes)[0].pull_dir)
        fname = os.path.join(folder, "graph_viz.md")
        with open(fname, 'w', encoding="utf-8") as f:
            f.write("```mermaid\nstateDiagram-v2\n")
            for start in self.networkx:
                f.writelines(
                    f"    {start.action} --> {child.action}\n"
                    for child in nx.neighbors(self.networkx, start)
                )
            f.write("```\n")
        return fname

def convert_to_acyclic(g: Graph) -> Graph:
    """Eliminates cycles in a flowgraph for analysis.

    Args:
        g (Graph): (presumably) cyclic graph to transform.

    Returns:
        Graph: Graph with cloned nodes.
    """
    cycles = nx.simple_cycles(g.networkx)
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


# TODO: serialization format
# TODO: cycles are conditional on user input
# TODO: write tests for hooks/steps
# TODO: make custom driver and tech for steps
