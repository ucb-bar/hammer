#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
import json
import shutil
from numbers import Number

import hammer_vlsi

from typing import Dict, List, TypeVar, Union

import os
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
                    "base var": ""  # means relative to tech dir
                }
            ],
            "libraries": [
                { "milkyway techfile": "test/soy" },
                { "openaccess techfile": "test/juice" },
                { "milkyway techfile": "test/coconut" },
                {
                    "openaccess techfile": "test/orange",
                    "provides": [
                        {"lib_type": "stdcell"}
                    ]
                },
                {
                    "openaccess techfile": "test/grapefruit",
                    "provides": [
                        {"lib_type": "stdcell"}
                    ]
                },
                {
                    "openaccess techfile": "test/tea",
                    "provides": [
                        {"lib_type": "technology"}
                    ]
                },
            ]
        }
        with open(tech_dir + "/dummy28.tech.json", "w") as f:
            f.write(json.dumps(tech_json, indent=4))
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        def make_test_filter() -> hammer_vlsi.LibraryFilter:
            def filter_func(lib: hammer_tech.Library) -> bool:
                return lib.openaccess_techfile is not None

            def extraction_func(lib: hammer_tech.Library) -> List[str]:
                assert lib.openaccess_techfile is not None
                return [lib.openaccess_techfile]

            def sort_func(lib: hammer_tech.Library) -> Union[Number, str, tuple]:
                assert lib.openaccess_techfile is not None
                if lib.provides is not None and len(
                        list(filter(lambda x: x is not None and x.lib_type == "technology", lib.provides))) > 0:
                    # Put technology first
                    return (0, "")
                else:
                    return (1, str(lib.openaccess_techfile))

            return hammer_vlsi.LibraryFilter.new(
                filter_func=filter_func,
                extraction_func=extraction_func,
                tag="test", description="Test filter",
                is_file=True,
                sort_func=sort_func
            )

        class Tool(hammer_vlsi.HammerTool):
            @property
            def steps(self) -> List[hammer_vlsi.HammerToolStep]:
                return self.make_steps_from_methods([
                    self.step
                ])

            def step(self) -> bool:
                def test_tool_format(lib, filt):
                    return ["drink {0}".format(lib)]

                self._read_lib_output = self.read_libs([self.milkyway_techfile_filter], test_tool_format, must_exist=False)

                self._test_filter_output = self.read_libs([make_test_filter()], test_tool_format, must_exist=False)
                return True
        test = Tool()
        test.logger = hammer_vlsi.HammerVLSILogging.context("")
        test.run_dir = tempfile.mkdtemp()
        test.technology = tech
        test.set_database(hammer_config.HammerDatabase())
        test.run()

        # Don't care about ordering here.
        self.assertEqual(set(test._read_lib_output),
                         {"drink {0}/soy".format(tech_dir), "drink {0}/coconut".format(tech_dir)})

        # We do care about ordering here.
        self.assertEqual(test._test_filter_output, [
            "drink {0}/tea".format(tech_dir),
            "drink {0}/grapefruit".format(tech_dir),
            "drink {0}/juice".format(tech_dir),
            "drink {0}/orange".format(tech_dir)
        ])

        # Cleanup
        shutil.rmtree(test.run_dir)

    def test_create_enter_script(self):
        class Tool(hammer_vlsi.HammerTool):
            @property
            def steps(self) -> List[hammer_vlsi.HammerToolStep]:
                return []

            @property
            def env_vars(self) -> Dict[str, str]:
                return {
                    "HELLO": "WORLD",
                    "EMPTY": "",
                    "CLOUD": "9",
                    "lol": "abc\"cat\""
                }

        fd, path = tempfile.mkstemp(".sh")
        os.close(fd) # Don't leak file descriptors

        test = Tool()
        test.create_enter_script(path)
        with open(path) as f:
            enter_script = f.read()
        # Cleanup
        os.remove(path)

        self.assertEqual(
"""
export CLOUD="9"
export EMPTY=""
export HELLO="WORLD"
export lol='abc"cat"'
""".strip(), enter_script.strip()
        )

        fd, path = tempfile.mkstemp(".sh")
        test.create_enter_script(path, raw=True)
        with open(path) as f:
            enter_script = f.read()
        # Cleanup
        os.remove(path)

        self.assertEqual(
"""
export CLOUD=9
export EMPTY=
export HELLO=WORLD
export lol=abc"cat"
""".strip(), enter_script.strip()
        )


T = TypeVar('T')


class HammerToolHooksTestContext:
    def __init__(self, test: unittest.TestCase) -> None:
        self.test = test  # type: unittest.TestCase
        self.temp_dir = ""  # type: str
        self.driver = None  # type: hammer_vlsi.HammerDriver

    def __enter__(self) -> "HammerToolHooksTestContext":
        """Initialize context by creating the temp_dir, driver, and loading mocksynth."""
        self.test.assertTrue(hammer_vlsi.HammerVLSISettings.set_hammer_vlsi_path_from_environment(),
                        "hammer_vlsi_path must exist")
        temp_dir = tempfile.mkdtemp()
        json_path = os.path.join(temp_dir, "project.json")
        with open(json_path, "w") as f:
            f.write(json.dumps({
                "vlsi.core.synthesis_tool": "mocksynth",
                "vlsi.core.technology": "nop",
                "synthesis.inputs.top_module": "dummy",
                "synthesis.inputs.input_files": ("/dev/null",),
                "synthesis.mocksynth.temp_folder": temp_dir
            }, indent=4))
        options = hammer_vlsi.HammerDriverOptions(
            environment_configs=[],
            project_configs=[json_path],
            log_file=os.path.join(temp_dir, "log.txt"),
            obj_dir=temp_dir
        )
        self.temp_dir = temp_dir
        self.driver = hammer_vlsi.HammerDriver(options)
        self.test.assertTrue(self.driver.load_synthesis_tool())
        return self

    def __exit__(self, type, value, traceback) -> bool:
        """Clean up the context by removing the temp_dir."""
        shutil.rmtree(self.temp_dir)
        return True


class HammerToolHooksTest(unittest.TestCase):
    def create_context(self) -> HammerToolHooksTestContext:
        return HammerToolHooksTestContext(self)

    @staticmethod
    def read(filename: str) -> str:
        with open(filename, "r") as f:
            return f.read()

    def test_normal_execution(self) -> None:
        """Test that no hooks means that everything is executed properly."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis()
            self.assertTrue(success)

            for i in range(1, 5):
                self.assertEqual(self.read(os.path.join(c.temp_dir, "step{}.txt".format(i))), "step{}".format(i))

    def test_replacement_hooks(self) -> None:
        """Test that replacement hooks work."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_removal_hook("step2"),
                hammer_vlsi.HammerTool.make_removal_hook("step4")
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i == 2 or i == 4:
                    self.assertFalse(os.path.exists(file))
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

    def test_resume_hooks(self) -> None:
        """Test that resume hooks work."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_resume_hook("step3")
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i <= 2:
                    self.assertFalse(os.path.exists(file), "step{}.txt should not exist".format(i))
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_post_resume_hook("step2")
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i <= 2:
                    self.assertFalse(os.path.exists(file), "step{}.txt should not exist".format(i))
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

    def test_pause_hooks(self) -> None:
        """Test that pause hooks work."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_pause_hook("step3")
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i > 2:
                    self.assertFalse(os.path.exists(file))
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_post_pause_hook("step3")
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i > 3:
                    self.assertFalse(os.path.exists(file))
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

    def test_extra_pause_hooks(self) -> None:
        """Test that extra pause hooks do nothing."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_pause_hook("step3"),
                hammer_vlsi.HammerTool.make_post_pause_hook("step3")
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i > 2:
                    self.assertFalse(os.path.exists(file))
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

    def test_insertion_hooks(self) -> None:
        """Test that insertion hooks work."""

        def change1(x: hammer_vlsi.HammerTool) -> bool:
            x.set_setting("synthesis.mocksynth.step1", "HelloWorld")
            return True

        def change2(x: hammer_vlsi.HammerTool) -> bool:
            x.set_setting("synthesis.mocksynth.step2", "HelloWorld")
            return True

        def change3(x: hammer_vlsi.HammerTool) -> bool:
            x.set_setting("synthesis.mocksynth.step3", "HelloWorld")
            return True

        def change4(x: hammer_vlsi.HammerTool) -> bool:
            x.set_setting("synthesis.mocksynth.step4", "HelloWorld")
            return True

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_insertion_hook("step3", change3)
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i == 3:
                    self.assertEqual(self.read(file), "HelloWorld")
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

        # Test inserting before the first step
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_insertion_hook("step1", change1)
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i == 1:
                    self.assertEqual(self.read(file), "HelloWorld")
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_insertion_hook("step2", change2),
                hammer_vlsi.HammerTool.make_post_insertion_hook("step3", change3),
                hammer_vlsi.HammerTool.make_pre_insertion_hook("change3", change4)
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i == 2 or i == 4:
                    self.assertEqual(self.read(file), "HelloWorld")
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

    def test_bad_hooks(self) -> None:
        """Test that hooks with bad targets are errors."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_removal_hook("does_not_exist")
            ])
            self.assertFalse(success)

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_removal_hook("free_lunch")
            ])
            self.assertFalse(success)

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_removal_hook("penrose_stairs")
            ])
            self.assertFalse(success)


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
