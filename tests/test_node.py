import json
import os
import tempfile
import unittest
from textwrap import dedent

import networkx as nx
import pytest
from networkx.readwrite import json_graph

from hammer.flowgraph import node
from hammer.flowgraph.node import Graph, Node, Status
from hammer.logging import HammerVLSILogging


class TestNode(unittest.TestCase):

    def test_initialize_node(self) -> None:
        """Test that we can instantiate a node."""
        test = Node(
            "syn", "nop", "syn_dir", "",
            ["foo.yml"],
            ["syn-out.json"],
        )
        self.assertEqual(test.action, "syn")

    def test_complex_graph(self) -> None:
        """Creating a more complex graph."""
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["foo.yml"],
            ["syn-out.json"],
        )
        child1 = Node(
            "par", "nop", "syn_dir", "par_dir",
            ["syn-out.json"],
            ["par-out.json"],
        )
        graph = Graph({root: [child1]})
        self.assertEqual(len(graph.networkx), 2)
        self.assertEqual(graph.networkx.number_of_edges(), 1)
        self.assertTrue(graph.verify())

    def test_invalid_graph(self) -> None:
        """Test that invalid flowgraphs are detected."""
        root = Node(
            "syn", "nop", "syn_dir", "",
            ["foo.yml"],
            ["syn-out.json"],
        )
        child1 = Node(
            "par", "nop", "syn_dir", "par_dir",
            ["syn-in.json"],
            ["par-out.json"],
        )
        graph = Graph({root: [child1]})
        self.assertFalse(graph.verify())

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
        self.assertEqual(len(g_acyclic.networkx), 4)
        self.assertEqual(g.networkx.number_of_edges(), 3)

    def test_big_cycle_reduction(self) -> None:
        """Test that larger cycles are reduced to an acyclic graph."""
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
            "v2", "nop", "v2_dir", "v3_dir",
            ["v1-out.json"],
            ["v2-out.json"],
        )
        v3 = Node(
            "v3", "nop", "v3_dir", "v0_dir",
            ["v2-out.json"],
            ["v3-out.json"],
        )
        g = Graph({
            v0: [v1],
            v1: [v2],
            v2: [v3],
            v3: [v0]
        })
        self.assertTrue(len(nx.find_cycle(g.networkx)) > 0)
        g_acyclic = node.convert_to_acyclic(g)
        with self.assertRaises(nx.NetworkXNoCycle):
            nx.find_cycle(g_acyclic.networkx)
        self.assertEqual(len(g_acyclic.networkx), 5)
        self.assertEqual(g.networkx.number_of_edges(), 4)

    def test_multi_cycle_reduction(self) -> None:
        """Test that multiple cycles are reduced to an acyclic graph."""
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
        v3 = Node(
            "v3", "nop", "v3_dir", "v4_dir",
            ["v2-out.json"],
            ["v3-out.json"],
        )
        v4 = Node(
            "v4", "nop", "v4_dir", "v5_dir",
            ["v3-out.json"],
            ["v4-out.json"],
        )
        v5 = Node(
            "v5", "nop", "v5_dir", "v3_dir",
            ["v4-out.json"],
            ["v3-out.json"],
        )
        g = Graph({
            v0: [v1],
            v1: [v2],
            v2: [v0, v3],
            v3: [v4, v2],
            v4: [v5],
            v5: [v3]
        })
        self.assertTrue(len(nx.find_cycle(g.networkx)) > 0)
        g_acyclic = node.convert_to_acyclic(g)
        with self.assertRaises(nx.NetworkXNoCycle):
            nx.find_cycle(g_acyclic.networkx)

    @pytest.mark.xfail(raises=ImportError, reason="Matplotlib currently not imported")
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

    def test_run_basic(self) -> None:
        """Test a basic syn -> par flow, all with nop tools."""
        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        cfg = dedent("""
            synthesis.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            par.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            drc.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            lvs.inputs:
                input_files: ["LICENSE", "README.md"]
                schematic_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"
                hcells_list: []

            pcb.inputs:
                top_module: "z1top.xdc"

            formal.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            sim.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            vlsi:
                core:
                    technology: "hammer.technology.nop"

                    synthesis_tool: "hammer.synthesis.nop"
                    par_tool: "hammer.par.nop"
                    drc_tool: "hammer.drc.nop"
                    lvs_tool: "hammer.lvs.nop"
                    power_tool: "hammer.power.nop"
                    sim_tool: "mocksim"
        """)

        with tempfile.TemporaryDirectory() as td:
            os.mkdir(os.path.join(td, "syn_dir"))
            os.mkdir(os.path.join(td, "par_dir"))

            with open(os.path.join(td, "syn_dir", "syn-in.yml"), 'w', encoding="utf-8") as tf1:
                tf1.write(cfg)

            syn = Node(
                "syn", "nop",
                os.path.join(td, "syn_dir"), os.path.join(td, "s2p_dir"),
                ["syn-in.yml"],
                ["syn-out.json"],
            )
            s2p = Node(
                "syn-to-par", "nop",
                os.path.join(td, "s2p_dir"), os.path.join(td, "par_dir"),
                ["syn-out.json"],
                ["s2p-out.json"],
            )
            par = Node(
                "par", "nop",
                os.path.join(td, "par_dir"), os.path.join(td, "out_dir"),
                ["s2p-out.json"],
                ["par-out.json"],
            )
            g = Graph({
                syn: [s2p],
                s2p: [par],
                par: []
            })
            g.run(syn)

        for n in g.networkx:
            self.assertEqual(n.status, Status.COMPLETE)

    def test_invalid_run(self) -> None:
        """
        Test that a failing run should not run
        other steps and exit gracefully.
        """
        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        cfg = dedent("""
            synthesis.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            par.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            drc.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            lvs.inputs:
                input_files: ["LICENSE", "README.md"]
                schematic_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"
                hcells_list: []

            pcb.inputs:
                top_module: "z1top.xdc"

            formal.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            sim.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            vlsi:
                core:
                    technology: "hammer.technology.nop"

                    synthesis_tool: "hammer.synthesis.nop"
                    par_tool: "hammer.par.nop"
                    drc_tool: "hammer.drc.nop"
                    lvs_tool: "hammer.lvs.nop"
                    power_tool: "hammer.power.nop"
                    sim_tool: "mocksim"
        """)

        with tempfile.TemporaryDirectory() as td:
            os.mkdir(os.path.join(td, "syn_dir"))
            os.mkdir(os.path.join(td, "par_dir"))

            with open(os.path.join(td, "syn_dir", "syn-in.yml"), 'w', encoding="utf-8") as tf1:
                tf1.write(cfg)

            syn = Node(
                "syn", "nop",
                os.path.join(td, "syn_dir"), os.path.join(td, "s2p_dir"),
                ["syn-in.yml"],
                ["syn-out.json"],
            )
            s2p_bad = Node(
                "blah", "nop",
                os.path.join(td, "s2p_dir"), os.path.join(td, "par_dir"),
                ["syn-out.json"],
                ["s2p-out.json"],
            )
            par = Node(
                "par", "nop",
                os.path.join(td, "par_dir"), os.path.join(td, "out_dir"),
                ["s2p-out.json"],
                ["par-out.json"],
            )
            g = Graph({
                syn: [s2p_bad],
                s2p_bad: [par],
                par: []
            })
            g.run(syn)

            self.assertEqual(syn.status, Status.COMPLETE)
            self.assertEqual(s2p_bad.status, Status.INCOMPLETE)
            self.assertEqual(par.status, Status.NOT_RUN)

    def test_resume_graph(self) -> None:
        """
        Test that a user can stop and start a flow if needed.
        """
        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        cfg = dedent("""
            synthesis.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            par.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            drc.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            lvs.inputs:
                input_files: ["LICENSE", "README.md"]
                schematic_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"
                hcells_list: []

            pcb.inputs:
                top_module: "z1top.xdc"

            formal.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            sim.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            vlsi:
                core:
                    technology: "hammer.technology.nop"

                    synthesis_tool: "hammer.synthesis.nop"
                    par_tool: "hammer.par.nop"
                    drc_tool: "hammer.drc.nop"
                    lvs_tool: "hammer.lvs.nop"
                    power_tool: "hammer.power.nop"
                    sim_tool: "mocksim"
        """)

        with tempfile.TemporaryDirectory() as td:
            os.mkdir(os.path.join(td, "syn_dir"))
            os.mkdir(os.path.join(td, "par_dir"))

            with open(os.path.join(td, "syn_dir", "syn-in.yml"), 'w', encoding="utf-8") as tf1:
                tf1.write(cfg)

            syn = Node(
                "syn", "nop",
                os.path.join(td, "syn_dir"), os.path.join(td, "s2p_dir"),
                ["syn-in.yml"],
                ["syn-out.json"],
            )
            s2p_bad = Node(
                "blah", "nop",
                os.path.join(td, "s2p_dir"), os.path.join(td, "par_dir"),
                ["syn-out.json"],
                ["s2p-out.json"],
            )
            par = Node(
                "par", "nop",
                os.path.join(td, "par_dir"), os.path.join(td, "out_dir"),
                ["s2p-out.json"],
                ["par-out.json"],
            )
            g = Graph({
                syn: [s2p_bad],
                s2p_bad: [par],
                par: []
            })
            g_failed_run = g.run(syn)

            self.assertEqual(syn.status, Status.COMPLETE)
            self.assertEqual(s2p_bad.status, Status.INCOMPLETE)
            self.assertEqual(par.status, Status.NOT_RUN)

            s2p_bad.action = "syn-to-par"
            g_good = g_failed_run.run(s2p_bad)
            for n in g_good.networkx:
                self.assertEqual(n.status, Status.COMPLETE)

    def test_mermaid(self) -> None:
        """
        Test that Mermaid visualization works.
        """
        with tempfile.TemporaryDirectory() as td:
            os.mkdir(os.path.join(td, "syn_dir"))
            os.mkdir(os.path.join(td, "par_dir"))

            syn = Node(
                "syn", "nop",
                os.path.join(td, "syn_dir"), os.path.join(td, "s2p_dir"),
                ["syn-in.yml"],
                ["syn-out.json"],
            )
            s2p = Node(
                "syn-to-par", "nop",
                os.path.join(td, "s2p_dir"), os.path.join(td, "par_dir"),
                ["syn-out.json"],
                ["s2p-out.json"],
            )
            par = Node(
                "par", "nop",
                os.path.join(td, "par_dir"), os.path.join(td, "out_dir"),
                ["s2p-out.json"],
                ["par-out.json"],
            )
            g = Graph({
                syn: [s2p],
                s2p: [par],
                par: []
            })

            g.to_mermaid(os.path.join(td, "mermaid.txt"))
            with open(os.path.join(td, "mermaid.txt"), 'r', encoding="utf-8") as f:
                s = f.readlines()
                self.assertListEqual(s, ["stateDiagram-v2\n", "    syn --> syn-to-par\n", "    syn-to-par --> par\n"])

    def test_encode_decode(self) -> None:
        """
        Test that a flowgraph can be encoded and decoded.
        """
        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        cfg = dedent("""
            synthesis.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            par.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            drc.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            lvs.inputs:
                input_files: ["LICENSE", "README.md"]
                schematic_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"
                hcells_list: []

            pcb.inputs:
                top_module: "z1top.xdc"

            formal.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            sim.inputs:
                input_files: ["LICENSE", "README.md"]
                top_module: "z1top.xdc"

            vlsi:
                core:
                    technology: "hammer.technology.nop"

                    synthesis_tool: "hammer.synthesis.nop"
                    par_tool: "hammer.par.nop"
                    drc_tool: "hammer.drc.nop"
                    lvs_tool: "hammer.lvs.nop"
                    power_tool: "hammer.power.nop"
                    sim_tool: "mocksim"
        """)

        with tempfile.TemporaryDirectory() as td:
            os.mkdir(os.path.join(td, "syn_dir"))
            os.mkdir(os.path.join(td, "par_dir"))

            with open(os.path.join(td, "syn_dir", "syn-in.yml"), 'w', encoding="utf-8") as tf1:
                tf1.write(cfg)
            syn = Node(
                "syn", "nop",
                os.path.join(td, "syn_dir"), os.path.join(td, "s2p_dir"),
                ["syn-in.yml"],
                ["syn-out.json"],
            )
            s2p = Node(
                "syn-to-par", "nop",
                os.path.join(td, "s2p_dir"), os.path.join(td, "par_dir"),
                ["syn-out.json"],
                ["s2p-out.json"],
            )
            par = Node(
                "par", "nop",
                os.path.join(td, "par_dir"), os.path.join(td, "out_dir"),
                ["s2p-out.json"],
                ["par-out.json"],
            )
            g = Graph({
                syn: [s2p],
                s2p: [par],
                par: []
            })

            out = json.dumps(g.to_json(), cls=node.NodeEncoder)
            g_dec = json.loads(out, object_hook=node.as_node)
            # print(g.to_json())
            print(json_graph.node_link_graph(g_dec).nodes)

if __name__ == "__main__":
    unittest.main()
