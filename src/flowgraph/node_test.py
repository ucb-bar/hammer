import logging
import unittest

import matplotlib.pyplot as plt
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
        )
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
            [child1],
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
        )
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
            [child1],
        )
        graph = Graph(root)
        graph_json = graph.to_json(indent=4)
        # logging.info(graph_json)
        # logging.info(node.Graph.from_json(graph_json))

    def test_cycle_reduction(self) -> None:
        """Test that cycles are reduced to an acyclic graph."""
        v0 = Node(
            "v0", "nop", "v0_dir", "v1_dir",
            ["v0-in.json"],
            ["v0-out.json"],
            [],
        )
        v1 = Node(
            "v1", "nop", "v1_dir", "v2_dir",
            ["v0-out.json"],
            ["v1-out.json"],
            [],
        )
        v2 = Node(
            "v2", "nop", "v2_dir", "v0_dir",
            ["v1-out.json"],
            ["v2-out.json"],
            [],
        )
        v0.children.append(v1)
        v1.children.append(v2)
        v2.children.append(v0)

        g = Graph(v0)
        self.assertTrue(len(nx.find_cycle(g.networkx)) > 0)

        g_acyclic = node.convert_to_acyclic(g)
        print(g_acyclic)
        with self.assertRaises(nx.NetworkXNoCycle):
            nx.find_cycle(g_acyclic.networkx)

    def test_visualization(self) -> None:
        """Test visualization of flowgraph."""
        v0 = Node(
            "syn", "nop", "syn_dir", "par_dir",
            ["syn-in.json"],
            ["syn-out.json"],
            [],
        )
        v1 = Node(
            "par", "nop", "par_dir", "drc_dir",
            ["syn-out.json", "par-in.json", "drc-out.json"],
            ["par-out.json"],
            [],
        )
        v2 = Node(
            "drc", "nop", "drc_dir", "par_dir",
            ["par-out.json", "drc-in.json"],
            ["drc-out.json"],
            [],
        )
        v0.children.append(v1)
        v1.children.append(v2)
        v2.children.append(v1)
        g = Graph(v0).networkx
        g.add_edge(v0.pull_dir, v0.action)
        g.add_edge(v0.action, v0.push_dir)
        g.add_edge(v1.pull_dir, v1.action)
        g.add_edge(v1.action, v1.push_dir)
        g.add_edge(v2.pull_dir, v2.action)
        g.add_edge(v2.action, v2.push_dir)
        pos = nx.planar_layout(g)
        blue = "#003262"
        yellow = "#fdb515"
        nx.draw_networkx_nodes(g, pos=pos,
            nodelist=[v0.action, v1.action, v2.action], node_size=1500, node_color=blue, label="Action")
        nx.draw_networkx_nodes(g, pos=pos,
            nodelist=[
                v0.pull_dir, v0.push_dir,
                v1.pull_dir, v1.push_dir,
                v2.pull_dir, v2.push_dir
            ], node_size=1500, node_color=yellow, label="Push/Pull Directory")
        nx.draw_networkx_labels(g, pos=pos, font_size=8, font_color="whitesmoke")
        nx.draw_networkx_edges(g, pos=pos,
            nodelist=[v0.action, v1.action, v2.action],
            node_size=1500, arrowsize=15, connectionstyle="arc3, rad=0.2", edge_color=blue)
        nx.draw_networkx_edges(g, pos=pos,
            edgelist=[
                (v0.pull_dir, v0.action),
                (v0.action, v0.push_dir),
                (v1.pull_dir, v1.action),
                (v1.action, v1.push_dir),
                (v2.pull_dir, v2.action),
                (v2.action, v2.push_dir),
            ], node_size=1500, arrowsize=15, connectionstyle="arc3, rad=0.2", edge_color=yellow)
        plt.axis("off")
        plt.legend(loc="upper left", markerscale=0.2)
        plt.savefig("/home/bngo/Research/hammer/graph.png", bbox_inches="tight", dpi=200)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
