#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi CLIDriver
#
#  See LICENSE for licence details.

import json
import os
import shutil
import tempfile
import re
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional

import hammer_config
from hammer_config import HammerJSONEncoder
from hammer_logging.test import HammerLoggingCaptureContext
from hammer_tech import MacroSize
from hammer_vlsi import CLIDriver, HammerDriver, HammerDriverOptions, HammerVLSISettings, PlacementConstraint, PlacementConstraintType
from hammer_utils import deepdict

import unittest


class CLIDriverTest(unittest.TestCase):
    @staticmethod
    def generate_dummy_config(syn_rundir: str, config_path: str, top_module: str, postprocessing_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate and write a dummy config to the given path.
        :param syn_rundir: Directory to set as the synthesis rundir.
        :param config_path: Path to which to write the config.
        :param top_module: Module to set as the top module.
        :param postprocessing_func: Optional function to modify/add to the config.
        :return: Config dictionary that was written.
        """
        config = {
            "vlsi.core.technology": "nop",
            "vlsi.core.synthesis_tool": "mocksynth",
            "vlsi.core.par_tool": "nop",
            "synthesis.inputs.top_module": top_module,
            "synthesis.inputs.input_files": ("/dev/null",),
            "synthesis.mocksynth.temp_folder": syn_rundir
        }  # type: Dict[str, Any]

        if postprocessing_func is not None:
            config = postprocessing_func(config)

        with open(config_path, "w") as f:
            f.write(json.dumps(config, cls=HammerJSONEncoder, indent=4))

        return config

    def run_syn_to_par_with_output(self, config_path: str, syn_rundir: str,
                                   par_rundir: str,
                                   syn_out_path: str,
                                   syn_to_par_out_path: str) -> None:
        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn",  # action
                "-p", config_path,
                "--output", syn_out_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)
        # Now run syn-to-par with the main config as well as the outputs.
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn-to-par",  # action
                "-p", config_path,
                "-p", syn_out_path,
                "--output", syn_to_par_out_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

    def test_syn_to_par(self) -> None:
        """
        Test that syn-to-par works with the output-only JSON.
        """

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()
        par_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")
        syn_out_path = os.path.join(syn_rundir, "syn_out.json")
        syn_to_par_out_path = os.path.join(syn_rundir, "syn_par_out.json")
        self.generate_dummy_config(syn_rundir, config_path, top_module)

        self.run_syn_to_par_with_output(config_path, syn_rundir, par_rundir,
                                        syn_out_path, syn_to_par_out_path)

        # synthesis output should NOT keep other settings
        with open(syn_out_path, "r") as f:
            syn_output = json.loads(f.read())
            self.assertEqual(syn_output["synthesis.outputs.output_files"], ["/dev/null"])
            self.assertFalse("vlsi.core.technology" in syn_output)
        # Generated par input should have other settings
        with open(syn_to_par_out_path, "r") as f:
            par_input = json.loads(f.read())
            self.assertEqual(par_input["par.inputs.top_module"], top_module)
            # par-input should preserve other settings
            self.assertEqual(par_input["vlsi.core.technology"], "nop")

        # Cleanup
        shutil.rmtree(syn_rundir)
        shutil.rmtree(par_rundir)

    def test_syn_to_par_full(self) -> None:
        """
        Test that syn-to-par works with the full JSON.
        """

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()
        par_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")
        syn_out_full_path = os.path.join(syn_rundir, "syn-output-full.json")
        syn_to_par_out_path = os.path.join(syn_rundir, "syn_par_out.json")
        self.generate_dummy_config(syn_rundir, config_path, top_module)

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn", # action
                "-p", config_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Now run syn-to-par with the main config as well as the outputs.
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn-to-par", # action
                "-p", syn_out_full_path,
                "--output", syn_to_par_out_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # synthesis full output should keep other settings
        with open(syn_out_full_path, "r") as f:
            syn_output = json.loads(f.read())
            self.assertEqual(syn_output["synthesis.outputs.output_files"], ["/dev/null"])
            self.assertEqual(syn_output["vlsi.core.technology"], "nop")
        # Generated par input should have other settings
        with open(syn_to_par_out_path, "r") as f:
            par_input = json.loads(f.read())
            self.assertEqual(par_input["par.inputs.top_module"], top_module)
            # par-input should preserve other settings
            self.assertEqual(par_input["vlsi.core.technology"], "nop")

        # Cleanup
        shutil.rmtree(syn_rundir)
        shutil.rmtree(par_rundir)

    def test_syn_to_par_improper(self) -> None:
        """
        Test that appropriate error messages are raised when syn-to-par
        is used on a config that does not have outputs.
        """

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()
        par_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")
        log_path = os.path.join(syn_rundir, "log.txt")
        self.generate_dummy_config(syn_rundir, config_path, top_module)

        with HammerLoggingCaptureContext() as c:
            # Running syn-to-par on a not-output config should fail.
            with self.assertRaises(SystemExit) as cm:  # type: ignore
                CLIDriver().main(args=[
                    "syn-to-par",  # action
                    "-p", config_path,
                    "--log", log_path,
                    "--syn_rundir", syn_rundir,
                    "--par_rundir", par_rundir
                ])
            self.assertEqual(cm.exception.code, 1)
        self.assertTrue(c.log_contains("Input config does not appear to contain valid synthesis outputs"))

        # Cleanup
        shutil.rmtree(syn_rundir)
        shutil.rmtree(par_rundir)

    def test_syn_to_par_same_as_syn_par(self) -> None:
        """
        Test that syn-par generates the same par input as calling syn,
        syn-to-par.
        """

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()
        par_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")
        syn_out_path = os.path.join(syn_rundir, "syn_out.json")
        syn_to_par_out_path = os.path.join(syn_rundir, "syn_par_out.json")
        self.generate_dummy_config(syn_rundir, config_path, top_module)

        # Run syn-to-par
        self.run_syn_to_par_with_output(config_path, syn_rundir, par_rundir,
                                        syn_out_path, syn_to_par_out_path)

        # Run syn-par
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn-par", # action
                "-p", config_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Check that the syn-to-par generated par input and the syn-par
        # generated par input are the same, modulo any synthesis.outputs.*
        # settings since they don't matter for par input.
        with open(syn_to_par_out_path, "r") as f:
            with open(os.path.join(syn_rundir, "par-input.json"), "r") as f2:
                syn_to_par_output = json.loads(f.read())
                syn_to_par_output = dict(filter(lambda i: "synthesis.outputs." not in i[0], syn_to_par_output.items()))
                syn_par_output = json.loads(f2.read())
                syn_par_output = dict(filter(lambda i: "synthesis.outputs." not in i[0], syn_par_output.items()))
                self.assertEqual(syn_to_par_output, syn_par_output)

        # Cleanup
        shutil.rmtree(syn_rundir)
        shutil.rmtree(par_rundir)

    def test_syn_par_config_dumping(self) -> None:
        """
        Test that the syn_par step (running both synthesis and place-and-route) dumps the intermediate config files,
        namely synthesis output config and par input config.
        """

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()
        par_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")
        self.generate_dummy_config(syn_rundir, config_path, top_module)

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn-par", # action
                "-p", config_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Check that the synthesis output and par input configs got dumped.
        with open(os.path.join(syn_rundir, "syn-output.json"), "r") as f:
            syn_output = json.loads(f.read())
            self.assertEqual(syn_output["synthesis.outputs.output_files"], ["/dev/null"])
            # syn-output should NOT keep other settings
            self.assertFalse("vlsi.core.technology" in syn_output)
        with open(os.path.join(syn_rundir, "syn-output-full.json"), "r") as f:
            syn_output_full = json.loads(f.read())
            self.assertEqual(syn_output_full["synthesis.outputs.output_files"], ["/dev/null"])
            # syn-output-full should preserve other settings
            self.assertEqual(syn_output_full["vlsi.core.technology"], "nop")
        with open(os.path.join(syn_rundir, "par-input.json"), "r") as f:
            par_input = json.loads(f.read())
            self.assertEqual(par_input["par.inputs.top_module"], top_module)
            # par-input should preserve other settings
            self.assertEqual(par_input["vlsi.core.technology"], "nop")

        # Cleanup
        shutil.rmtree(syn_rundir)
        shutil.rmtree(par_rundir)

    def test_dump(self) -> None:
        """
        Test that dump works properly.
        """
        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        output_path = os.path.join(syn_rundir, "output.json")
        config_packed_path = os.path.join(syn_rundir, "run_config_packed.json")
        config_path = os.path.join(syn_rundir, "run_config.json")
        self.generate_dummy_config(syn_rundir, config_packed_path, top_module)
        # Equivalent config to above but not unpacked
        with open(config_packed_path, "r") as f:
            unpacked_config = hammer_config.reverse_unpack(json.loads(f.read()))
        with open(config_path, "w") as f:
            f.write(json.dumps(unpacked_config, cls=HammerJSONEncoder, indent=4))

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "dump",  # action
                "-p", config_path,
                "--output", output_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", syn_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Check that dumped output should be same as what we read in.
        with open(output_path, "r") as f:
            dumped_output = json.loads(f.read())
        with open(config_packed_path, "r") as f:
            packed_output = json.loads(f.read())
        self.assertEqual(packed_output, dumped_output)

        # Cleanup
        shutil.rmtree(syn_rundir)

    def test_hier_dump(self) -> None:
        """
        Test that hierarchical settings work properly.
        """
        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")

        def add_hier(d: Dict[str, Any]) -> Dict[str, Any]:
            output = deepdict(d)
            dummy_placement = PlacementConstraint(
                path="dummy",
                type=PlacementConstraintType.Dummy,
                x=Decimal("0"),
                y=Decimal("0"),
                width=Decimal("10"),
                height=Decimal("10"),
                master=None,
                create_physical=None,
                orientation=None,
                margins=None,
                top_layer=None,
                layers=None,
                obs_types=None).to_dict()
            output["vlsi.inputs.default_output_load"] = 1
            output["vlsi.inputs.hierarchical.top_module"] = top_module
            output["vlsi.inputs.hierarchical.flat"] = "hierarchical"
            output["vlsi.inputs.hierarchical.config_source"] = "manual"
            output["vlsi.inputs.hierarchical.manual_modules"] = [
                {"mod1": ["m1s1", "m1s2"], "mod2": ["m2s1"], top_module: ["mod1", "mod2"]}]
            manual_constraints = [{"mod1": [dummy_placement]},
                                  {"mod2": [dummy_placement]},
                                  {"m1s1": [dummy_placement]},
                                  {"m1s2": [dummy_placement]},
                                  {"m2s1": [dummy_placement]},
                                  {top_module: [dummy_placement]}]
            output["vlsi.inputs.hierarchical.manual_placement_constraints"] = manual_constraints
            output["vlsi.inputs.hierarchical.constraints"] = [{"mod1": [{"vlsi.inputs.default_output_load": 2}]},
                                                              {"m2s1": [{"vlsi.inputs.default_output_load": 3}]}]
            return output

        self.generate_dummy_config(
            syn_rundir, config_path, top_module, postprocessing_func=add_hier)

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "auto",  # action
                "-p", config_path,
                "--obj_dir", syn_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Check that dumped output should be same as what we read in.
        with open(os.path.join(syn_rundir, "syn-m2s1/full_config.json"), "r") as f:
            dumped_output = json.loads(f.read())
        self.assertEqual(dumped_output['vlsi.inputs.default_output_load'], 3)
        with open(os.path.join(syn_rundir, "syn-m1s1/full_config.json"), "r") as f:
            dumped_output = json.loads(f.read())
        self.assertEqual(dumped_output['vlsi.inputs.default_output_load'], 1)
        with open(os.path.join(syn_rundir, "syn-mod1/full_config.json"), "r") as f:
            dumped_output = json.loads(f.read())
        self.assertEqual(dumped_output['vlsi.inputs.default_output_load'], 2)

        # Cleanup
        shutil.rmtree(syn_rundir)

    def test_hier_dump_empty_constraints(self) -> None:
        """
        Test that hierarchical settings work properly even when no constraints
        are given.
        """
        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")

        def add_hier(d: Dict[str, Any]) -> Dict[str, Any]:
            output = deepdict(d)
            output["vlsi.inputs.default_output_load"] = 1
            output["vlsi.inputs.hierarchical.top_module"] = top_module
            output["vlsi.inputs.hierarchical.flat"] = "hierarchical"
            output["vlsi.inputs.hierarchical.config_source"] = "manual"
            output["vlsi.inputs.hierarchical.manual_modules"] = [
                {"mod1": ["m1s1", "m1s2"], "mod2": ["m2s1"], top_module: ["mod1", "mod2"]}]
            output["vlsi.inputs.hierarchical.manual_placement_constraints"] = []
            output["vlsi.inputs.hierarchical.constraints"] = []
            return output

        self.generate_dummy_config(
            syn_rundir, config_path, top_module, postprocessing_func=add_hier)

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "auto",  # action
                "-p", config_path,
                "--obj_dir", syn_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Cleanup
        shutil.rmtree(syn_rundir)

    def test_dump_macrosizes(self) -> None:
        """
        Test that dump-macrosizes works properly.
        """
        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        output_path = os.path.join(syn_rundir, "output.json")
        config_path = os.path.join(syn_rundir, "run_config.json")

        my_size = MacroSize(
            library='my_lib',
            name='my_cell',
            width=Decimal("100"),
            height=Decimal("100")
        )

        def add_macro_sizes(d: Dict[str, Any]) -> Dict[str, Any]:
            output = deepdict(d)
            output["vlsi.technology.extra_macro_sizes"] = [my_size.to_setting()]
            return output

        self.generate_dummy_config(syn_rundir, config_path, top_module, postprocessing_func=add_macro_sizes)

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "dump-macrosizes",  # action
                "-p", config_path,
                "--output", output_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", syn_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Check that dumped output should be same as what we read in.
        with open(output_path, "r") as f:
            dumped_output = json.loads(f.read())
            self.assertEqual(dumped_output, [my_size.to_setting()])

        # Cleanup
        shutil.rmtree(syn_rundir)

    def test_override_actions(self) -> None:
        """
        Test that we can override actions like synthesis_action etc in subclasses.
        """

        class OverriddenDriver(CLIDriver):
            synthesis_called = False  # type: bool

            def synthesis_action(self, driver: HammerDriver,
                                 append_error_func: Callable[[str], None]) -> Optional[Dict]:
                def post_run_func(driver: HammerDriver) -> None:
                    OverriddenDriver.synthesis_called = True

                return self.create_action(action_type="synthesis", extra_hooks=None, post_run_func=post_run_func)(
                    driver, append_error_func)

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()

        # Generate a config for testing.
        top_module = "dummy"
        config_path = os.path.join(syn_rundir, "run_config.json")
        self.generate_dummy_config(syn_rundir, config_path, top_module)

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            OverriddenDriver().main(args=[
                "syn",  # action
                "-p", config_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", syn_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Check that our synthesis function got called.
        self.assertEqual(OverriddenDriver.synthesis_called, True)

        # Cleanup
        shutil.rmtree(syn_rundir)

    def test_bad_override(self) -> None:
        """Test that a bad override of e.g. synthesis_action is caught."""
        with self.assertRaises(TypeError):
            class BadOverride(CLIDriver):
                def synthesis_action(self, bad: int) -> dict:  # type: ignore
                    return {bad: "bad"}
            BadOverride()


class HammerBuildSystemsTest(unittest.TestCase):

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
                self.assertFalse(t in targets, "Found duplicate target {}".format(t))
                targets[t] = p

        return targets

    def test_flat_makefile(self) -> None:
        """
        Test that a Makefile for a flat design is generated correctly.
        """
        tmpdir = tempfile.mkdtemp()
        proj_config = os.path.join(tmpdir, "config.json")

        settings = {
                "vlsi.core.technology": "nop",
                "vlsi.core.build_system": "make",
                "synthesis.inputs.top_module": "TopMod"
            }
        with open(proj_config, "w") as f:
            f.write(json.dumps(settings, cls=HammerJSONEncoder, indent=4))

        options = HammerDriverOptions(
            environment_configs=[],
            project_configs=[proj_config],
            log_file=os.path.join(tmpdir, "log.txt"),
            obj_dir=tmpdir
        )

        self.assertTrue(HammerVLSISettings.set_hammer_vlsi_path_from_environment(),
            "hammer_vlsi_path must exist")
        driver = HammerDriver(options)

        CLIDriver.generate_build_inputs(driver, lambda x: None)

        d_file = os.path.join(driver.obj_dir, "hammer.d")
        self.assertTrue(os.path.exists(d_file))

        with open(d_file, "r") as f:
            contents = f.readlines()

        targets = self._read_targets_from_makefile(contents)

        tasks = {"pcb", "sim-rtl", "syn", "sim-syn", "par", "sim-par", "power-par", "drc", "lvs", "formal-syn", "formal-par", "timing-syn", "timing-par"}
        bridge_tasks = {"syn-to-sim", "syn-to-par", "par-to-sim", "par-to-lvs", "par-to-drc", "par-to-power", "sim-par-to-power", "syn-to-formal", "par-to-formal", "syn-to-timing", "par-to-timing"}
        expected_targets = tasks.copy()
        expected_targets.update(bridge_tasks)
        expected_targets.update({"redo-" + x for x in expected_targets if x is not "pcb"})
        expected_targets.update({os.path.join(tmpdir, x + "-rundir", x + "-output-full.json") for x in tasks if x not in {"sim-rtl", "sim-syn", "sim-par", "power-par", "formal-syn", "formal-par", "timing-syn", "timing-par"}})
        expected_targets.update({os.path.join(tmpdir, x + "-rundir", x.split('-')[0] + "-output-full.json") for x in tasks if x in {"sim-rtl", "sim-syn", "sim-par", "power-par", "formal-syn", "formal-par", "timing-syn", "timing-par"}})
        expected_targets.update({os.path.join(tmpdir, x + "-input.json") for x in tasks if x not in {"syn", "pcb", "sim-rtl", "power-par"}})
        expected_targets.update({os.path.join(tmpdir, x + "-input.json") for x in {"power-par", "power-sim-par"}})

        self.assertEqual(set(targets.keys()), set(expected_targets))

        # TODO at some point we should add more tests

        # Cleanup
        shutil.rmtree(tmpdir)

    def test_hier_makefile(self) -> None:
        """
        Test that a Makefile for a hierarchical design is generated correctly.
        """
        tmpdir = tempfile.mkdtemp()
        proj_config = os.path.join(tmpdir, "config.json")

        settings = {
                "vlsi.core.technology": "nop",
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
            log_file=os.path.join(tmpdir, "log.txt"),
            obj_dir=tmpdir
        )

        self.assertTrue(HammerVLSISettings.set_hammer_vlsi_path_from_environment(),
            "hammer_vlsi_path must exist")
        driver = HammerDriver(options)

        CLIDriver.generate_build_inputs(driver, lambda x: None)

        d_file = os.path.join(driver.obj_dir, "hammer.d")
        self.assertTrue(os.path.exists(d_file))

        with open(d_file, "r") as f:
            contents = f.readlines()

        targets = self._read_targets_from_makefile(contents)

        mods = {"TopMod", "SubModA", "SubModB"}
        expected_targets = {"pcb", os.path.join(tmpdir, "pcb-rundir", "pcb-output-full.json")}
        hier_tasks = {"sim-rtl", "syn", "sim-syn", "par", "sim-par", "power-par", "drc", "lvs", "formal-syn", "formal-par", "timing-syn", "timing-par"}
        for task in hier_tasks:
            expected_targets.update({task + "-" + x for x in mods})
            expected_targets.update({"redo-" + task + "-" + x for x in mods})
            expected_targets.update({os.path.join(tmpdir, task + "-" + x, task.split("-")[0] + "-output-full.json") for x in mods})
        bridge_tasks = {"syn-to-sim", "syn-to-par", "par-to-sim", "par-to-lvs", "par-to-drc", "par-to-power", "sim-par-to-power", "syn-to-formal", "par-to-formal", "syn-to-timing", "par-to-timing"}
        for task in bridge_tasks:
            expected_targets.update({task + "-" + x for x in mods})
            expected_targets.update({"redo-" + task + "-" + x for x in mods})

        # Only non-leafs get a syn-*-input.json target
        expected_targets.update({os.path.join(tmpdir, "syn-" + x + "-input.json") for x in mods if x in {"TopMod"}})
        expected_targets.update({os.path.join(tmpdir, "sim-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "sim-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "power-sim-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "lvs-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "drc-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "formal-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "formal-par-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "timing-syn-" + x + "-input.json") for x in mods})
        expected_targets.update({os.path.join(tmpdir, "timing-par-" + x + "-input.json") for x in mods})

        self.assertEqual(set(targets.keys()), expected_targets)

        # TODO at some point we should add more tests

        # Cleanup
        shutil.rmtree(tmpdir)



if __name__ == '__main__':
     unittest.main()
