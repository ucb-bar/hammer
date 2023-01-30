import logging
import unittest

import networkx as nx
from hammer.flowgraph import node
from hammer.flowgraph.node import Graph, Node


class NodeTest(unittest.TestCase):

    def test_initialize_node(self) -> None:
        """Test that we can instantiate a node."""
        test = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
        )
        # logging.info(test)
        self.assertEqual(test.action, "syn")

    def test_complex_graph(self) -> None:
        """Creating a more complex graph."""
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["bryan-test.yml"],
            ["syn-out.json"],
        )
        child1 = Node(
            "par", "nop", "syn_dir", "par_dir",
            ["syn-out.json"],
            ["par-out.json"],
        )
        graph = Graph({root: [child1]})
        self.assertTrue(graph.verify())

    def test_cycle_reduction(self) -> None:
        """Test that cycles are reduced to an acyclic graph."""
        v0 = Node(
            "v0", "nop", "v0_dir", "v1_dir",
            ["v0-in.json"],
            ["v0-out.json"],
        )
        v1 = Node(
            "v1", "nop", "v1_dir", "v2_dir",
            ["v0-out.json"],
            ["v1-out.json"],
        )
        v2 = Node(
            "v2", "nop", "v2_dir", "v0_dir",
            ["v1-out.json"],
            ["v2-out.json"],
        )
        g = Graph({
            v0: [v1],
            v1: [v2],
            v2: [v0],
        })
        self.assertTrue(len(nx.find_cycle(g.networkx)) > 0)
        g_acyclic = node.convert_to_acyclic(g)
        with self.assertRaises(nx.NetworkXNoCycle):
            nx.find_cycle(g_acyclic.networkx)

    def test_visualization(self) -> None:
        """Test visualization of flowgraph."""
        import matplotlib.pyplot as plt
        v0 = Node(
            "syn", "nop", "syn_dir", "par_dir",
            ["syn-in.json"],
            ["syn-out.json"],
        )
        v1 = Node(
            "par", "nop", "par_dir", "drc_dir",
            ["syn-out.json", "par-in.json", "drc-out.json"],
            ["par-out.json"],
        )
        v2 = Node(
            "drc", "nop", "drc_dir", "par_dir",
            ["par-out.json", "drc-in.json"],
            ["drc-out.json"],
        )
        g = Graph({
            v0.action: [v1.action],
            v1.action: [v2.action],
            v2.action: []
        }).networkx
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
