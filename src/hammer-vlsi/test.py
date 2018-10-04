#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi
#
#  Copyright 2017-2018 Edward Wang <edward.c.wang@compdigitec.com>

import json
import shutil
from abc import abstractmethod, ABCMeta
from numbers import Number

import hammer_vlsi
import hammer_tech
from hammer_logging import Level, HammerVLSIFileLogger
from hammer_logging import HammerVLSILogging

from typing import Dict, List, TypeVar, Union, Optional, Callable, Any

import os
import tempfile
import unittest

from hammer_utils import deepdict


class HammerVLSILoggingTest(unittest.TestCase):
    def test_colours(self):
        """
        Test that we can log with and without colour.
        """
        msg = "This is a test message"  # type: str

        log = HammerVLSILogging.context("test")

        HammerVLSILogging.enable_buffering = True  # we need this for test
        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        HammerVLSILogging.enable_colour = True
        log.info(msg)
        self.assertEqual(HammerVLSILogging.get_colour_escape(Level.INFO) + "[test] " + msg + HammerVLSILogging.COLOUR_CLEAR, HammerVLSILogging.get_buffer()[0])

        HammerVLSILogging.enable_colour = False
        log.info(msg)
        self.assertEqual("[test] " + msg, HammerVLSILogging.get_buffer()[0])

    def test_subcontext(self):
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = True

        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        # Get top context
        log = HammerVLSILogging.context("top")

        # Create sub-contexts.
        logA = log.context("A")
        logB = log.context("B")

        msgA = "Hello world from A"
        msgB = "Hello world from B"

        logA.info(msgA)
        logB.error(msgB)

        self.assertEqual(HammerVLSILogging.get_buffer(),
            ['[top] [A] ' + msgA, '[top] [B] ' + msgB]
        )

    def test_file_logging(self):
        fd, path = tempfile.mkstemp(".log")
        os.close(fd) # Don't leak file descriptors

        filelogger = HammerVLSIFileLogger(path)

        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(filelogger.callback)
        log = HammerVLSILogging.context()
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


class HammerToolTestHelpers:
    """
    Helper functions to aid in the testing of IP library filtering/processing.
    """
    @staticmethod
    def write_tech_json(tech_json_filename: str, postprocessing_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> None:
        # TODO: use a structured way of creating it when arrays actually work!
        # Currently the subelements of the array don't get recursively "validated", so the underscores don't disappear, etc.
        # ~ tech_json_obj = hammer_tech.TechJSON(name="dummy28")
        # ~ tech_json_obj.libraries = [
        # ~ hammer_tech.Library(milkyway_techfile="soy"),
        # ~ hammer_tech.Library(milkyway_techfile="coconut"),
        # ~ hammer_tech.Library(openaccess_techfile="juice"),
        # ~ hammer_tech.Library(openaccess_techfile="tea")
        # ~ ]
        # ~ tech_json = tech_json_obj.serialize()
        tech_json = {
            "name": "dummy28",
            "installs": [
                {
                    "path": "test",
                    "base var": ""  # means relative to tech dir
                }
            ],
            "libraries": [
                {"milkyway techfile": "test/soy"},
                {"openaccess techfile": "test/juice"},
                {"milkyway techfile": "test/coconut"},
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
        }  # type: Dict[str, Any]
        if postprocessing_func is not None:
            tech_json = postprocessing_func(tech_json)
        with open(tech_json_filename, "w") as f:
            f.write(json.dumps(tech_json, indent=4))

    @staticmethod
    def make_test_filter() -> hammer_vlsi.LibraryFilter:
        """
        Make a test filter that returns libraries with openaccess techfiles with libraries that provide 'technology'
        in lib_type first, with the rest sorted by the openaccess techfile.
        """
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


class SingleStepTool(hammer_vlsi.DummyHammerTool, metaclass=ABCMeta):
    """
    Helper class to define a single-step tool in tests.
    """
    @property
    def steps(self) -> List[hammer_vlsi.HammerToolStep]:
        return self.make_steps_from_methods([
            self.step
        ])

    @abstractmethod
    def step(self) -> bool:
        """
        Implement this method for the single step.
        :return: True if the step passed
        """
        pass

class DummyTool(SingleStepTool):
    """
    A dummy tool that does nothing and always passes.
    """
    def step(self) -> bool:
        return True


class HammerTechnologyTest(unittest.TestCase):
    """
    Tests for the Hammer technology library (hammer_tech).
    """
    def test_extra_prefixes(self) -> None:
        """
        Test that extra_prefixes works properly as a property.
        """
        lib = hammer_tech.library_from_json('{"openaccess techfile": "test/oa"}')  # type: hammer_tech.Library

        prefixes_orig = [hammer_tech.PathPrefix(prefix="test", path="/tmp/test")]

        prefixes = [hammer_tech.PathPrefix(prefix="test", path="/tmp/test")]
        lib.extra_prefixes = prefixes
        # Check that we get the original back even after mutating the original list.
        prefixes.append(hammer_tech.PathPrefix(prefix="bar", path="/tmp/bar"))
        self.assertEqual(lib.extra_prefixes, prefixes_orig)

        prefixes2 = lib.extra_prefixes
        # Check that we don't mutate the copy stored in the lib if we mutate after getting it
        prefixes2.append(hammer_tech.PathPrefix(prefix="bar", path="/tmp/bar"))
        self.assertEqual(lib.extra_prefixes, prefixes_orig)

    def test_prepend_dir_path(self) -> None:
        tech_json = {
            "name": "My Technology Library",
            "installs": [
                {
                    "path": "test",
                    "base var": ""  # means relative to tech dir
                }
            ],
            "libraries": []
        }

        tech_dir = "/tmp/path"  # should not be used
        tech = hammer_tech.HammerTechnology.load_from_json("dummy28", json.dumps(tech_json, indent=2), tech_dir)

        # Check that a tech-provided prefix works fine
        self.assertEqual("{0}/water".format(tech_dir), tech.prepend_dir_path("test/water"))
        self.assertEqual("{0}/fruit".format(tech_dir), tech.prepend_dir_path("test/fruit"))

        # Check that a non-existent prefix gives an error
        with self.assertRaises(ValueError):
            tech.prepend_dir_path("badprefix/file")

        # Check that a lib's custom prefix works
        from hammer_vlsi.hammer_tool import ExtraLibrary
        lib = ExtraLibrary(
            library=hammer_tech.library_from_json("""{"milkyway techfile": "custom/chair"}"""),
            prefix=hammer_tech.PathPrefix(
                prefix="custom",
                path="/tmp/custom"
            )
        ).store_into_library()
        self.assertEqual("{0}/hat".format("/tmp/custom"), tech.prepend_dir_path("custom/hat", lib))

    def test_gds_map_file(self) -> None:
        """
        Test that GDS map file support works as expected.
        """
        import hammer_config

        tech_dir = tempfile.mkdtemp()
        tech_json_filename = tech_dir + "/dummy28.tech.json"

        def add_gds_map(d: Dict[str, Any]) -> Dict[str, Any]:
            r = deepdict(d)
            r.update({"gds map file": "test/gds_map_file"})
            return r

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_gds_map)
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        # Test that empty for gds_map_mode results in no map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'empty',
            'par.inputs.gds_map_file': None
        }])
        self.assertEqual(tool.get_gds_map_file(), None)

        # Test that manual mode for gds_map_mode works.
        database.update_project([{
            'par.inputs.gds_map_mode': 'manual',
            'par.inputs.gds_map_file': '/tmp/foo/bar'
        }])
        self.assertEqual(tool.get_gds_map_file(), '/tmp/foo/bar')

        # Test that auto mode for gds_map_mode works if the technology has a map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'auto',
            'par.inputs.gds_map_file': None
        }])
        self.assertEqual(tool.get_gds_map_file(), '{tech}/gds_map_file'.format(tech=tech_dir))

        # Cleanup
        shutil.rmtree(tech_dir)

        # Create a new technology with no GDS map file.
        tech_dir = tempfile.mkdtemp()
        tech_json_filename = tech_dir + "/dummy28.tech.json"
        HammerToolTestHelpers.write_tech_json(tech_json_filename)
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for gds_map_mode works if the technology has no map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'auto',
            'par.inputs.gds_map_file': None
        }])
        self.assertEqual(tool.get_gds_map_file(), None)

        # Cleanup
        shutil.rmtree(tech_dir)


class HammerToolTest(unittest.TestCase):
    def test_read_libs(self) -> None:
        """
        Test that HammerTool can read technology IP libraries and filter/process them.
        """
        import hammer_config

        tech_dir = tempfile.mkdtemp()
        tech_json_filename = tech_dir + "/dummy28.tech.json"
        HammerToolTestHelpers.write_tech_json(tech_json_filename)
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        class Tool(SingleStepTool):
            def step(self) -> bool:
                def test_tool_format(lib, filt) -> List[str]:
                    return ["drink {0}".format(lib)]

                self._read_lib_output = self.read_libs([self.milkyway_techfile_filter], test_tool_format, must_exist=False)

                self._test_filter_output = self.read_libs([HammerToolTestHelpers.make_test_filter()], test_tool_format, must_exist=False)
                return True
        test = Tool()
        test.logger = HammerVLSILogging.context("")
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
        shutil.rmtree(tech_dir)
        shutil.rmtree(test.run_dir)

    def test_timing_lib_ecsm_filter(self) -> None:
        """
        Test that the ECSM-first filter works as expected.
        """
        import hammer_config

        tech_dir = tempfile.mkdtemp()
        tech_json_filename = tech_dir + "/dummy28.tech.json"
        tech_json = {
            "name": "dummy28",
            "installs": [
                {
                    "path": "test",
                    "base var": ""  # means relative to tech dir
                }
            ],
            "libraries": [
                {
                    "ecsm liberty file": "test/eggs.ecsm",
                    "ccs liberty file": "test/eggs.ccs",
                    "nldm liberty file": "test/eggs.nldm"
                },
                {
                    "ccs liberty file": "test/custard.ccs",
                    "nldm liberty file": "test/custard.nldm"
                },
                {
                    "nldm liberty file": "test/noodles.nldm"
                },
                {
                    "ecsm liberty file": "test/eggplant.ecsm"
                },
                {
                    "ccs liberty file": "test/cookies.ccs"
                }
            ]
        }
        with open(tech_json_filename, "w") as f:
            f.write(json.dumps(tech_json, indent=4))
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        class Tool(SingleStepTool):
            lib_outputs = []  # type: List[str]

            def step(self) -> bool:
                Tool.lib_outputs = self.read_libs([self.timing_lib_with_ecsm_filter], self.to_plain_item,
                                                       must_exist=False)
                return True

        test = Tool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = tempfile.mkdtemp()
        test.technology = tech
        test.set_database(hammer_config.HammerDatabase())
        test.run()

        # Check that the ecsm-based filter prioritized ecsm -> ccs -> nldm.
        self.assertEqual(set(Tool.lib_outputs), {
            "{0}/eggs.ecsm".format(tech_dir),
            "{0}/custard.ccs".format(tech_dir),
            "{0}/noodles.nldm".format(tech_dir),
            "{0}/eggplant.ecsm".format(tech_dir),
            "{0}/cookies.ccs".format(tech_dir)
        })

        # Cleanup
        shutil.rmtree(tech_dir)
        shutil.rmtree(test.run_dir)

    def test_read_extra_libs(self) -> None:
        """
        Test that HammerTool can read/process extra IP libraries in addition to those of the technology.
        """
        import hammer_config

        tech_dir = tempfile.mkdtemp()
        tech_json_filename = tech_dir + "/dummy28.tech.json"
        HammerToolTestHelpers.write_tech_json(tech_json_filename)
        tech = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        tech.cache_dir = tech_dir

        class Tool(hammer_vlsi.DummyHammerTool):
            lib_output = []  # type: List[str]
            filter_output = []  # type: List[str]

            @property
            def steps(self) -> List[hammer_vlsi.HammerToolStep]:
                return self.make_steps_from_methods([
                    self.step
                ])

            def step(self) -> bool:
                def test_tool_format(lib, filt) -> List[str]:
                    return ["drink {0}".format(lib)]

                Tool.lib_output = self.read_libs([self.milkyway_techfile_filter], test_tool_format, must_exist=False)

                Tool.filter_output = self.read_libs([HammerToolTestHelpers.make_test_filter()], test_tool_format,
                                                    must_exist=False)
                return True

        test = Tool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = tempfile.mkdtemp()
        test.technology = tech
        # Add some extra libraries to see if they are picked up
        database = hammer_config.HammerDatabase()
        lib1_path = "/foo/bar"
        lib1b_path = "/library/specific/prefix"
        lib2_path = "/baz/quux"
        database.update_project([{
            'vlsi.technology.extra_libraries': [
                {
                    "library": {"milkyway techfile": "test/xylophone"}
                },
                {
                    "library": {"openaccess techfile": "test/orange"}
                },
                {
                    "prefix": {
                        "prefix": "lib1",
                        "path": lib1_path
                    },
                    "library": {"milkyway techfile": "lib1/muffin"}
                },
                {
                    "prefix": {
                        "prefix": "lib1",
                        "path": lib1b_path
                    },
                    "library": {"milkyway techfile": "lib1/granola"}
                },
                {
                    "prefix": {
                        "prefix": "lib2",
                        "path": lib2_path
                    },
                    "library": {
                        "openaccess techfile": "lib2/cake",
                        "milkyway techfile": "lib2/brownie",
                        "provides": [
                            {"lib_type": "stdcell"}
                        ]
                    }
                }
            ]
        }])
        test.set_database(database)
        test.run()

        # Not testing ordering in this assertion.
        self.assertEqual(set(Tool.lib_output),
                         {
                             "drink {0}/soy".format(tech_dir),
                             "drink {0}/coconut".format(tech_dir),
                             "drink {0}/xylophone".format(tech_dir),
                             "drink {0}/muffin".format(lib1_path),
                             "drink {0}/granola".format(lib1b_path),
                             "drink {0}/brownie".format(lib2_path)
                         })

        # We do care about ordering here.
        # Our filter should put the techfile first and sort the rest.
        print("Tool.filter_output = " + str(Tool.filter_output))
        tech_lef_result = [
            # tech lef
            "drink {0}/tea".format(tech_dir)
        ]
        base_lib_results = [
            "drink {0}/grapefruit".format(tech_dir),
            "drink {0}/juice".format(tech_dir),
            "drink {0}/orange".format(tech_dir)
        ]
        extra_libs_results = [
            "drink {0}/cake".format(lib2_path)
        ]
        self.assertEqual(Tool.filter_output, tech_lef_result + sorted(base_lib_results + extra_libs_results))

        # Cleanup
        shutil.rmtree(tech_dir)
        shutil.rmtree(test.run_dir)

    def test_create_enter_script(self) -> None:
        class Tool(hammer_vlsi.DummyHammerTool):
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
        self._driver = None  # type: Optional[hammer_vlsi.HammerDriver]

    # Helper property to check that the driver did get initialized.
    @property
    def driver(self) -> hammer_vlsi.HammerDriver:
        assert self._driver is not None, "HammerDriver must be initialized before use"
        return self._driver

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
        self._driver = hammer_vlsi.HammerDriver(options)
        self.test.assertTrue(self.driver.load_synthesis_tool())
        return self

    def __exit__(self, type, value, traceback) -> bool:
        """Clean up the context by removing the temp_dir."""
        shutil.rmtree(self.temp_dir)
        # Return True (normal execution) if no exception occurred.
        return True if type is None else False


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
        """Test that extra pause hooks cause an error."""
        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_pause_hook("step3"),
                hammer_vlsi.HammerTool.make_post_pause_hook("step3")
            ])
            self.assertFalse(success)

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

    def test_insert_before_first_step(self) -> None:
        """Test that inserting a step before the first step works."""
        def change3(x: hammer_vlsi.HammerTool) -> bool:
            x.set_setting("synthesis.mocksynth.step3", "HelloWorld")
            return True

        with self.create_context() as c:
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_pre_insertion_hook("step1", change3)
            ])
            self.assertTrue(success)

            for i in range(1, 5):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i == 3:
                    self.assertEqual(self.read(file), "HelloWorld")
                else:
                    self.assertEqual(self.read(file), "step{}".format(i))

    def test_resume_pause_hooks_with_custom_steps(self) -> None:
        """Test that resume/pause hooks work with custom steps."""
        with self.create_context() as c:
            def step5(x: hammer_vlsi.HammerTool) -> bool:
                with open(os.path.join(c.temp_dir, "step5.txt"), "w") as f:
                    f.write("HelloWorld")
                return True

            c.driver.set_post_custom_syn_tool_hooks(hammer_vlsi.HammerTool.make_from_to_hooks("step5", "step5"))
            success, syn_output = c.driver.run_synthesis(hook_actions=[
                hammer_vlsi.HammerTool.make_post_insertion_hook("step4", step5)
            ])
            self.assertTrue(success)

            for i in range(1, 6):
                file = os.path.join(c.temp_dir, "step{}.txt".format(i))
                if i == 5:
                    self.assertEqual(self.read(file), "HelloWorld")
                else:
                    self.assertFalse(os.path.exists(file))


if __name__ == '__main__':
    unittest.main()
