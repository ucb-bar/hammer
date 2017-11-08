#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi
#  
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

import hammer_vlsi

import tempfile
import unittest

class HammerVLSILoggingTest(unittest.TestCase):
    def test_colours(self):
        """
        Test that we can log with and without colour.
        """
        msg = "This is a test message" # type: str

        log = hammer_vlsi.HammerVLSILogging.context("test")

        hammer_vlsi.HammerVLSILogging.enable_buffering = True # we need this for test
        hammer_vlsi.HammerVLSILogging.clear_callbacks()
        hammer_vlsi.HammerVLSILogging.add_callback(hammer_vlsi.HammerVLSILogging.callback_buffering)

        hammer_vlsi.HammerVLSILogging.enable_colour = True
        log.info(msg)
        self.assertEqual(hammer_vlsi.HammerVLSILogging.get_colour_escape(hammer_vlsi.Level.INFO) + "[test] " + msg + hammer_vlsi.HammerVLSILogging.COLOUR_CLEAR, hammer_vlsi.HammerVLSILogging.get_buffer()[0])

        hammer_vlsi.HammerVLSILogging.enable_colour = False
        log.info(msg)
        self.assertEqual("[test] " + msg, hammer_vlsi.HammerVLSILogging.get_buffer()[0])

    def test_subcontext(self):
        hammer_vlsi.HammerVLSILogging.enable_colour = False
        hammer_vlsi.HammerVLSILogging.enable_tag = True

        hammer_vlsi.HammerVLSILogging.clear_callbacks()
        hammer_vlsi.HammerVLSILogging.add_callback(hammer_vlsi.HammerVLSILogging.callback_buffering)

        # Get top context
        log = hammer_vlsi.HammerVLSILogging.context("top")

        # Create sub-contexts.
        logA = log.context("A")
        logB = log.context("B")

        msgA = "Hello world from A"
        msgB = "Hello world from B"

        logA.info(msgA)
        logB.error(msgB)

        self.assertEqual(hammer_vlsi.HammerVLSILogging.get_buffer(),
            ['[top] [A] ' + msgA, '[top] [B] ' + msgB]
        )

    def test_file_logging(self):
        import os
        fd, path = tempfile.mkstemp(".log")
        os.close(fd) # Don't leak file descriptors

        filelogger = hammer_vlsi.HammerVLSIFileLogger(path)

        hammer_vlsi.HammerVLSILogging.clear_callbacks()
        hammer_vlsi.HammerVLSILogging.add_callback(filelogger.callback)
        log = hammer_vlsi.HammerVLSILogging.context()
        log.info("Hello world")
        log.info("Eternal voyage to the edge of the universe")
        filelogger.close()

        with open(path, 'r') as f:
            self.assertEqual(f.read().strip(), """
[<global>] Level.INFO: Hello world
[<global>] Level.INFO: Eternal voyage to the edge of the universe
""".strip())

        # Remove temp file
        os.remove(path)

class HammerToolTest(unittest.TestCase):
    def test_read_libs(self):
        import hammer_config
        import hammer_tech
        import json
        import shutil

        tech_dir = tempfile.mkdtemp()
        # TODO: use a structured way of creating it when arrays actually work!
        # Currently the subelements of the array don't get recursively "validated", so the underscores don't disappear, etc.
        #~ tech_json_obj = hammer_tech.TechJSON(name="dummy28")
        #~ tech_json_obj.libraries = [
            #~ hammer_tech.Library(milkyway_techfile="soy"),
            #~ hammer_tech.Library(milkyway_techfile="coconut"),
            #~ hammer_tech.Library(openaccess_techfile="juice"),
            #~ hammer_tech.Library(openaccess_techfile="tea")
        #~ ]
        #~ tech_json = tech_json_obj.serialize()
        tech_json = {
            "name": "dummy28",
            "installs": [
            {
              "path": "test",
              "base var": "" # means relative to tech dir
            }
            ],
            "libraries": [
                { "milkyway techfile": "test/soy" },
                { "openaccess techfile": "test/juice" },
                { "milkyway techfile": "test/coconut" },
                { "openaccess techfile": "test/tea" }
            ]
        }
        with open(tech_dir + "/dummy28.tech.json", "w") as f:
            f.write(json.dumps(tech_json, indent=4))
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        class Tool(hammer_vlsi.HammerTool):
            def do_run(self) -> bool:
                def test_tool_format(lib, filt):
                    return ["drink {0}".format(lib)]

                self._read_lib_output = self.read_libs([self.milkyway_techfile_filter], test_tool_format, must_exist=False)
                return True
        test = Tool()
        test.logger = hammer_vlsi.HammerVLSILogging.context("")
        test.run_dir = tempfile.mkdtemp()
        test.technology = tech
        test.set_database(hammer_config.HammerDatabase())
        test.run()

        # Don't care about ordering here.
        self.assertEqual(set(test._read_lib_output), set([
            "drink {0}/test/soy".format(tech_dir),
            "drink {0}/test/coconut".format(tech_dir),
        ]))

        # Cleanup
        shutil.rmtree(test.run_dir)

class TimeValueTest(unittest.TestCase):
    def test_read_and_write(self):
        """
        Test that we can parse and emit time values.
        """
        tv = hammer_vlsi.TimeValue("1000 ns")
        self.assertEqual(tv.str_value_in_units("ns"), "1000 ns")
        self.assertEqual(tv.str_value_in_units("us"), "1 us")
        self.assertEqual(tv.value_in_units("ps"), 1000000.0)

    def test_default_prefix(self):
        """
        Test that we can parse and emit time values.
        """
        tv = hammer_vlsi.TimeValue("1000")
        self.assertEqual(tv.value_in_units("ns"), 1000)
        tv2 = hammer_vlsi.TimeValue("42", "m")
        self.assertEqual(tv2.value_in_units("ms"), 42)

    def test_errors(self):
        """
        Test that errors get caught.
        """
        def bad_1():
            hammer_vlsi.TimeValue("bugaboo")
        def bad_2():
            hammer_vlsi.TimeValue("1.1.1.1 ps")
        def bad_3():
            hammer_vlsi.TimeValue("420 xs")
        def bad_4():
            hammer_vlsi.TimeValue("12 noobs")
        def bad_5():
            hammer_vlsi.TimeValue("666......")
        self.assertRaises(ValueError, bad_1)
        self.assertRaises(ValueError, bad_2)
        self.assertRaises(ValueError, bad_3)
        self.assertRaises(ValueError, bad_4)
        self.assertRaises(ValueError, bad_5)

if __name__ == '__main__':
    unittest.main()
