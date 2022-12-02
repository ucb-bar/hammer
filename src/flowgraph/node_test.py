import logging
import unittest

import networkx as nx
import node
from node import Graph, Node


class NodeTest(unittest.TestCase):

    def test_initialize_node(self) -> None:
        """Test that we can instantiate a node."""
        test = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
            [],
            []
        )
        # logging.info(test)
        self.assertEqual(test.action, "syn")

    def test_complex_graph(self) -> None:
        """Creating a more complex graph."""
        child1 = Node(
            "par", "nop", "syn_dir", "par_dir",
            ["syn-out.json"],
            ["par-out.json"],
            [],
            []
        )
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
            [child1],
            []
        )
        graph = Graph(root)
        # logging.info(nx.nodes(graph.networkx))
        self.assertTrue(graph.verify())
        self.assertEqual(graph.root.children[0], child1)

    def test_to_json(self) -> None:
        """Test nodal JSON output."""
        # logging.info(test.to_json())
        child1 = Node(
            "par", "nop", "syn_dir", "par_dir",
            ["syn-out.json"],
            ["par-out.json"],
            [],
            []
        )
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
            [child1],
            []
        )
        graph = Graph(root)
        graph_json = graph.to_json(indent=4)
        # logging.info(graph_json)
        # logging.info(node.Graph.from_json(graph_json))

    def test_cycle_reduction(self) -> None:
        """Test that cycles are reduced to an acyclic graph."""
        v0 = Node(
            "v0", "nop", "v0_dir", "v1_dir",
            ["v0-out.json"],
            ["v1-out.json"],
            [],
            []
        )
        v1 = Node(
            "v1", "nop", "v1_dir", "v2_dir",
            ["v1-out.json"],
            ["v2-out.json"],
            [],
            []
        )
        v2 = Node(
            "v2", "nop", "v2_dir", "v0_dir",
            ["v2-out.json"],
            ["v0-out.json"],
            [],
            []
        )
        v0.children.append(v1)
        v1.children.append(v2)
        v2.children.append(v0)
        g = Graph(v0)
        self.assertTrue(len(nx.find_cycle(g.networkx)) > 0)
        g_acyclic = node.convert_to_acyclic(g)
        logging.info(g_acyclic.networkx)
        with self.assertRaises(nx.NetworkXNoCycle):
            nx.find_cycle(g_acyclic.networkx)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
