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

import hammer_config
from hammer_logging.test import HammerLoggingCaptureContext
from hammer_vlsi import CLIDriver, HammerDriver

import unittest


class CLIDriverTest(unittest.TestCase):
    @staticmethod
    def generate_dummy_config(syn_rundir: str, config_path: str, top_module: str) -> Dict[str, Any]:
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
            f.write(json.dumps(unpacked_config, indent=4))

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
