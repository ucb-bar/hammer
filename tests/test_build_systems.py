import json
import os
import re
import shutil
import tempfile
from typing import List, Dict

from hammer.config import HammerJSONEncoder
from hammer.vlsi import HammerDriverOptions, HammerVLSISettings, HammerDriver, CLIDriver


class TestHammerBuildSystems:

    def _read_targets_from_makefile(self, lines: List[str]) -> Dict[str, List[str]]:
        """
        Helper method to read information about targets from lines of a Makefile.
        """
        targets = {}  # type: Dict[str, List[str]]

        for line in lines:
            # This regex is looking for all non-special targets (i.e. those that aren't .PHONY, .INTERMEDIATE, .SECONDARY, ...)
            # These are of the format (target_name: list of prereqs ...)
            m = re.match(r"^([^.\s:][^\s:]*)\s*:(.*)$", line)
            if m:
                t = m.group(1)
                p = re.split(r"\s+", m.group(2))
                assert t not in targets, "Found duplicate target {}".format(t)
                targets[t] = p

        return targets

    def test_flat_makefile(self, tmpdir) -> None:
        """
        Test that a Makefile for a flat design is generated correctly.
        """
        proj_config = tmpdir / "config.json"

        settings = {
                "vlsi.core.technology": "hammer.technology.nop",
                "vlsi.core.build_system": "make",
                "synthesis.inputs.top_module": "TopMod"
        }
        with open(proj_config, "w") as f:
            f.write(json.dumps(settings, cls=HammerJSONEncoder, indent=4))

        options = HammerDriverOptions(
            environment_configs=[],
            project_configs=[str(proj_config)],
            log_file=str(tmpdir / "log.txt"),
            obj_dir=str(tmpdir)
        )

        driver = HammerDriver(options)

        CLIDriver.generate_build_inputs(driver, lambda x: None)

        d_file = os.path.join(driver.obj_dir, "hammer.d")
        assert os.path.exists(d_file)

        with open(d_file, "r") as f:
            contents = f.readlines()

        targets = self._read_targets_from_makefile(contents)

        tasks = {"pcb", "sim-rtl", "power-rtl", "syn", "sim-syn", "power-syn", "par", "sim-par", "power-par", "drc", "lvs", "formal-syn", "formal-par", "timing-syn", "timing-par"}
        bridge_tasks = {"syn-to-sim", "syn-to-par", "par-to-sim", "par-to-lvs", "par-to-drc", "syn-to-power", "par-to-power", "sim-rtl-to-power", "sim-syn-to-power", "sim-par-to-power", "syn-to-formal", "par-to-formal", "syn-to-timing", "par-to-timing"}
        expected_targets = tasks.copy()
        expected_targets.update(bridge_tasks)
        expected_targets.update({"redo-" + x for x in expected_targets if x != "pcb"})
        expected_targets.update({os.path.join(tmpdir, x + "-rundir", x + "-output-full.json") for x in tasks if x not in {"sim-rtl", "sim-syn", "sim-par", "power-rtl", "power-syn", "power-par", "formal-syn", "formal-par", "timing-syn", "timing-par"}})
        expected_targets.update({os.path.join(tmpdir, x + "-rundir", x.split('-')[0] + "-output-full.json") for x in tasks if x in {"sim-rtl", "sim-syn", "sim-par", "power-rtl", "power-syn", "power-par", "formal-syn", "formal-par", "timing-syn", "timing-par"}})
        expected_targets.update({os.path.join(tmpdir, x + "-input.json") for x in tasks if x not in {"syn", "pcb", "sim-rtl", "power-rtl"}})
        expected_targets.update({os.path.join(tmpdir, x + "-input.json") for x in {"power-sim-rtl", "power-sim-syn", "power-sim-par"}})

        assert set(targets.keys()) == set(expected_targets)

        # TODO at some point we should add more tests

    def test_hier_makefile(self, tmpdir) -> None:
        """
        Test that a Makefile for a hierarchical design is generated correctly.
        """
        proj_config = os.path.join(str(tmpdir), "config.json")

        settings = {
                "vlsi.core.technology": "hammer.technology.nop",
                "vlsi.core.build_system": "make",
                "vlsi.inputs.hierarchical.mode": "hierarchical",
                "vlsi.inputs.hierarchical.top_module": "TopMod",
                "vlsi.inputs.hierarchical.config_source": "manual",
                "vlsi.inputs.hierarchical.manual_modules": [{"TopMod": ["SubModA", "SubModB"]}],
                "vlsi.inputs.hierarchical.manual_placement_constraints": [
                    {"TopMod": [
                        {"path": "top", "type": "toplevel", "x": 0, "y": 0, "width": 1234, "height": 7890, "margins": {"left": 1, "top": 2, "right": 3, "bottom": 4}},
                        {"path": "top/C", "type": "placement", "x": 2, "y": 102, "width": 30, "height": 40},
                        {"path": "top/B", "type": "hierarchical", "x": 10, "y": 30, "master": "SubModB"},
                        {"path": "top/A", "type": "hierarchical", "x": 200, "y": 120, "master": "SubModA"}]},
                    {"SubModA": [
                        {"path": "a", "type": "toplevel", "x": 0, "y": 0, "width": 100, "height": 200, "margins": {"left": 0, "top": 0, "right": 0, "bottom": 0}}]},
                    {"SubModB": [
                        {"path": "b", "type": "toplevel", "x": 0, "y": 0, "width": 340, "height": 160, "margins": {"left": 0, "top": 0, "right": 0, "bottom": 0}}]}
                ]
            }
        with open(proj_config, "w") as f:
            f.write(json.dumps(settings, cls=HammerJSONEncoder, indent=4))

        options = HammerDriverOptions(
            environment_configs=[],
            project_configs=[proj_config],
            log_file=os.path.join(str(tmpdir), "log.txt"),
            obj_dir=str(tmpdir)
        )

        driver = HammerDriver(options)

        CLIDriver.generate_build_inputs(driver, lambda x: None)

        d_file = os.path.join(driver.obj_dir, "hammer.d")
        assert os.path.exists(d_file)

        with open(d_file, "r") as f:
            contents = f.readlines()

        targets = self._read_targets_from_makefile(contents)

        mods = {"TopMod", "SubModA", "SubModB"}
        expected_targets = {"pcb", os.path.join(tmpdir, "pcb-rundir", "pcb-output-full.json")}
        hier_tasks = {"sim-rtl", "power-rtl", "syn", "sim-syn", "power-syn", "par", "sim-par", "power-par", "drc", "lvs", "formal-syn", "formal-par", "timing-syn", "timing-par"}
        for task in hier_tasks:
            expected_targets.update({task + "-" + x for x in mods})
            expected_targets.update({"redo-" + task + "-" + x for x in mods})
            expected_targets.update({os.path.join(tmpdir, task + "-" + x, task.split("-")[0] + "-output-full.json") for x in mods})
        bridge_tasks = {"syn-to-sim", "syn-to-par", "par-to-sim", "par-to-lvs", "par-to-drc", "syn-to-power", "par-to-power", "sim-rtl-to-power", "sim-syn-to-power", "sim-par-to-power", "syn-to-formal", "par-to-formal", "syn-to-timing", "par-to-timing"}
        for task in bridge_tasks:
            expected_targets.update({task + "-" + x for x in mods})
            expected_targets.update({"redo-" + task + "-" + x for x in mods})

        # Only non-leafs get a hier-par-to-syn target
        expected_targets.update({"hier-par-to-syn-" + x for x in mods if x in {"TopMod"}})
        expected_targets.update({"redo-hier-par-to-syn-" + x for x in mods if x in {"TopMod"}})

        # Only non-leafs get a syn-*-input.json target
        expected_targets.update({os.path.join(tmpdir, "syn-" + x + "-input.json") for x in mods if x in {"TopMod"}})
        expected_targets.update({os.path.join(tmpdir, "sim-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "sim-par-" + x + "-input.json") for x in mods})
        #expected_targets.update({os.path.join(tmpdir, "power-rtl-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-sim-rtl-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-sim-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-sim-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "lvs-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "drc-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "formal-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "formal-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "timing-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "timing-par-" + x + "-input.json") for x in mods})

        assert set(targets.keys()) == expected_targets

        # TODO at some point we should add more tests
