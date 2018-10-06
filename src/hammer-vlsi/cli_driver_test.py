#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi CLIDriver
#
#  Copyright 2018 Edward Wang <edward.c.wang@compdigitec.com>

import json
import os
import shutil
import tempfile
from typing import Any, Callable, Dict, Optional

from hammer_vlsi import CLIDriver, HammerDriver

import unittest


class CLIDriverTest(unittest.TestCase):
    def generate_dummy_config(self, syn_rundir: str, config_path: str, top_module: str) -> Dict[str, Any]:
        """
        Generate and write a dummy config to the given path.
        :param syn_rundir: Directory to set as the synthesis rundir.
        :param config_path: Path to which to write the config.
        :param top_module: Module to set as the top module.
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

        with open(config_path, "w") as f:
            f.write(json.dumps(config, indent=4))

        return config

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

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn", # action
                "-p", config_path,
                "--output", syn_out_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # Now run syn-to-par with the main config as well as the outputs.
        with self.assertRaises(SystemExit) as cm:  # type: ignore
            CLIDriver().main(args=[
                "syn-to-par", # action
                "-p", config_path,
                "-p", syn_out_path,
                "--output", syn_to_par_out_path,
                "--syn_rundir", syn_rundir,
                "--par_rundir", par_rundir
            ])
        self.assertEqual(cm.exception.code, 0)

        # synthesis output should NOT keep other settings
        with open(syn_out_path, "r") as f:
            syn_output = json.loads(f.read())
            self.assertEqual(syn_output["synthesis.outputs.output_files"], [])
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
            self.assertEqual(syn_output["synthesis.outputs.output_files"], [])
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
            self.assertEqual(syn_output["synthesis.outputs.output_files"], [])
            # syn-output should NOT keep other settings
            self.assertFalse("vlsi.core.technology" in syn_output)
        with open(os.path.join(syn_rundir, "syn-output-full.json"), "r") as f:
            syn_output_full = json.loads(f.read())
            self.assertEqual(syn_output_full["synthesis.outputs.output_files"], [])
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


if __name__ == '__main__':
     unittest.main()
