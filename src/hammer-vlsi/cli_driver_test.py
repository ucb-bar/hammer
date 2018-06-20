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

from hammer_vlsi import CLIDriver

import unittest


class CLIDriverTest(unittest.TestCase):
    def test_syn_par_config_dumping(self) -> None:
        """
        Test that the syn_par step (running both synthesis and place-and-route) dumps the intermediate config files,
        namely synthesis output config and par input config.
        """

        # Set up some temporary folders for the unit test.
        syn_rundir = tempfile.mkdtemp()
        par_rundir = tempfile.mkdtemp()

        top_module = "dummy"
        config = {
            "vlsi.core.technology": "nop",
            "vlsi.core.synthesis_tool": "mocksynth",
            "vlsi.core.par_tool": "nop",
            "synthesis.inputs.top_module": top_module,
            "synthesis.inputs.input_files": ("/dev/null",),
            "synthesis.mocksynth.temp_folder": syn_rundir
        }
        config_path = os.path.join(syn_rundir, "run_config.json")
        with open(config_path, "w") as f:
            f.write(json.dumps(config, indent=4))

        # Check that running the CLIDriver executes successfully (code 0).
        with self.assertRaises(SystemExit) as cm:
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
        with open(os.path.join(syn_rundir, "par-input.json"), "r") as f:
            par_input = json.loads(f.read())
            self.assertEqual(par_input["par.inputs.top_module"], top_module)

        # Cleanup
        shutil.rmtree(syn_rundir)
        shutil.rmtree(par_rundir)


if __name__ == '__main__':
     unittest.main()
