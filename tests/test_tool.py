import json
import os
from typing import List, Dict, Any
import sys
from pathlib import Path

import pytest

from hammer import tech as hammer_tech, vlsi as hammer_vlsi
from hammer.config import HammerJSONEncoder
from hammer.logging import HammerVLSILogging, HammerVLSIFileLogger
from hammer.logging.test import HammerLoggingCaptureContext
from hammer.utils import deeplist, deepdict
from utils.stackup import StackupTestHelper
from utils.tech import HasGetTech
from utils.tool import HammerToolTestHelpers, SingleStepTool, DummyTool


class TestHammerTool(HasGetTech):
    def test_read_libs(self, tmp_path, request) -> None:
        """
        Test that HammerTool can read technology IP libraries and filter/process them.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        logger = HammerVLSILogging.context("")
        logger.logging_class.clear_callbacks()
        tech.logger = logger

        class Tool(SingleStepTool):
            def step(self) -> bool:
                def test_tool_format(lib, filt) -> List[str]:
                    return ["drink {0}".format(lib)]

                self._read_lib_output = tech.read_libs([hammer_tech.filters.milkyway_techfile_filter], test_tool_format, must_exist=False)

                self._test_filter_output = tech.read_libs([HammerToolTestHelpers.make_test_filter()], test_tool_format, must_exist=False)
                return True

        test = Tool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        database = hammer_config.HammerDatabase()
        test.set_database(database)
        tech.set_database(database)
        test.run()

        # Don't care about ordering here.
        assert set(test._read_lib_output) == {
            "drink {0}/soy".format(tech_dir),
            "drink {0}/coconut".format(tech_dir)
        }

        # We do care about ordering here.
        assert test._test_filter_output == [
            "drink {0}/tea".format(tech_dir),
            "drink {0}/grapefruit".format(tech_dir),
            "drink {0}/juice".format(tech_dir),
            "drink {0}/orange".format(tech_dir)
        ]

    def test_timing_lib_ecsm_filter(self, tmp_path, request) -> None:
        """
        Test that the ECSM-first filter works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        tech_json = {
            "name": f"{tech_name}",
            "libraries": [
                {
                    "ecsm_liberty_file": "eggs.ecsm",
                    "ccs_liberty_file": "eggs.ccs",
                    "nldm_liberty_file": "eggs.nldm"
                },
                {
                    "ccs_liberty_file": "custard.ccs",
                    "nldm_liberty_file": "custard.nldm"
                },
                {
                    "nldm_liberty_file": "noodles.nldm"
                },
                {
                    "ecsm_liberty_file": "eggplant.ecsm"
                },
                {
                    "ccs_liberty_file": "cookies.ccs"
                }
            ]
        }
        with open(tech_json_filename, "w") as f:
            f.write(json.dumps(tech_json, cls=HammerJSONEncoder, indent=4))
        (Path(tech_dir) / "eggs.ecsm").write_text("eggs ecsm")
        (Path(tech_dir) / "eggs.ccs").write_text("eggs ccs")
        (Path(tech_dir) / "eggs.nldm").write_text("eggs nldm")
        (Path(tech_dir) / "custard.ccs").write_text("custard ccs")
        (Path(tech_dir) / "custard.nldm").write_text("custard nldm")
        (Path(tech_dir) / "noodles.nldm").write_text("noodles nldm")
        (Path(tech_dir) / "eggplant.ecsm").write_text("eggplant ecsm")
        (Path(tech_dir) / "cookies.ccs").write_text("cookies ccs")

        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        logger = HammerVLSILogging.context("")
        logger.logging_class.clear_callbacks()
        tech.logger = logger

        class Tool(SingleStepTool):
            lib_outputs = []  # type: List[str]

            def step(self) -> bool:
                Tool.lib_outputs = tech.read_libs([hammer_tech.filters.timing_lib_with_ecsm_filter],
                                                  hammer_tech.HammerTechnologyUtils.to_plain_item,
                                                  must_exist=False)
                return True

        test = Tool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        test.set_database(hammer_config.HammerDatabase())
        tech.set_database(hammer_config.HammerDatabase())
        test.run()

        # Check that the ecsm-based filter prioritized ecsm -> ccs -> nldm.
        assert set(Tool.lib_outputs) == {
            "{0}/eggs.ecsm".format(tech_dir),
            "{0}/custard.ccs".format(tech_dir),
            "{0}/noodles.nldm".format(tech_dir),
            "{0}/eggplant.ecsm".format(tech_dir),
            "{0}/cookies.ccs".format(tech_dir)
        }

    def test_read_extra_libs(self, tmp_path, request) -> None:
        """
        Test that HammerTool can read/process extra IP libraries in addition to those of the technology.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir
        tech.logger = HammerVLSILogging.context("tech")

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

                Tool.lib_output = tech.read_libs([hammer_tech.filters.milkyway_techfile_filter], test_tool_format, must_exist=False)

                Tool.filter_output = tech.read_libs([HammerToolTestHelpers.make_test_filter()], test_tool_format,
                                                    must_exist=False)
                return True

        test = Tool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        # Add some extra libraries to see if they are picked up
        database = hammer_config.HammerDatabase()
        lib1_path = "/foo/bar"
        lib1b_path = "/library/specific/prefix"
        lib2_path = "/baz/quux"
        database.update_project([{
            'vlsi.technology.extra_libraries': [
                {
                    "library": {"milkyway_techfile": "xylophone"}
                },
                {
                    "library": {"openaccess_techfile": "orange"}
                },
                {
                    "prefix": {
                        "id": "lib1",
                        "path": lib1_path
                    },
                    "library": {"milkyway_techfile": "lib1/muffin"}
                },
                {
                    "prefix": {
                        "id": "lib1",
                        "path": lib1b_path
                    },
                    "library": {"milkyway_techfile": "lib1/granola"}
                },
                {
                    "prefix": {
                        "id": "lib2",
                        "path": lib2_path
                    },
                    "library": {
                        "openaccess_techfile": "lib2/cake",
                        "milkyway_techfile": "lib2/brownie",
                        "provides": [
                            {"lib_type": "stdcell"}
                        ]
                    }
                }
            ]
        }])
        p = Path(tech_dir_base) / tech_name
        (p / "xylophone").write_text("xylophone mw")

        test.set_database(database)
        tech.set_database(database)
        test.run()

        # Not testing ordering in this assertion.
        assert set(Tool.lib_output) == {
            "drink {0}/soy".format(tech_dir),
            "drink {0}/coconut".format(tech_dir),
            "drink {0}/xylophone".format(tech_dir),
            "drink {0}/muffin".format(lib1_path),
            "drink {0}/granola".format(lib1b_path),
            "drink {0}/brownie".format(lib2_path)
        }

        # We do care about ordering here.
        # Our filter should put the techfile first and sort the rest.
        # print("Tool.filter_output = " + str(Tool.filter_output))
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
        # print(tech_lef_result + sorted(base_lib_results + extra_libs_results))

        assert Tool.filter_output == tech_lef_result + sorted(base_lib_results + extra_libs_results)

    def test_create_enter_script(self, tmp_path) -> None:
        class Tool(hammer_vlsi.DummyHammerTool):
            @property
            def env_vars(self) -> Dict[str, str]:
                return {
                    "HELLO": "WORLD",
                    "EMPTY": "",
                    "CLOUD": "9",
                    "lol": "abc\"cat\""
                }

        path = str(tmp_path / "script.sh")

        test = Tool()
        test.create_enter_script(path)
        with open(path) as f:
            enter_script = f.read()
        # Cleanup
        os.remove(path)

        assert """export CLOUD="9"
export EMPTY=""
export HELLO="WORLD"
export lol='abc"cat"'
""".strip() == enter_script.strip()

        path = str(tmp_path / "script2.sh")
        test.create_enter_script(path, raw=True)
        with open(path) as f:
            enter_script = f.read()
        # Cleanup
        os.remove(path)

        assert """export CLOUD=9
export EMPTY=
export HELLO=WORLD
export lol=abc"cat"
""".strip() == enter_script.strip()

    def test_bad_export_config_outputs(self, tmp_path) -> None:
        """
        Test that a plugin that fails to call super().export_config_outputs()
        is caught.
        """
        tmpdir = str(tmp_path)
        proj_config = os.path.join(tmpdir, "config.json")

        with open(proj_config, "w") as f:
            f.write(json.dumps({
                "vlsi.core.technology": "hammer.technology.nop",
                "vlsi.core.synthesis_tool": "hammer.synthesis.mocksynth",
                "vlsi.core.par_tool": "hammer.par.nop",
                "synthesis.inputs.top_module": "dummy",
                "synthesis.inputs.input_files": ("/dev/null",)
            }, cls=HammerJSONEncoder, indent=4))

        class BadExportTool(hammer_vlsi.HammerSynthesisTool, DummyTool):
            def export_config_outputs(self) -> Dict[str, Any]:
                # Deliberately forget to call super().export_config_outputs
                return {
                    'extra': 'value'
                }

            def fill_outputs(self) -> bool:
                self.output_files = deeplist(self.input_files)
                return True

            def __init__(self):
                super().__init__()
                self._package = "hammer.synthesis.mocksynth"

        driver = hammer_vlsi.HammerDriver(
            hammer_vlsi.HammerDriver.get_default_driver_options()._replace(project_configs=[
                proj_config
            ], log_file=f"{tmpdir}/hammer-vlsi.log", obj_dir=f"{tmpdir}/obj_dir"))

        syn_tool = BadExportTool()
        driver.set_up_synthesis_tool(syn_tool, "bad_tool", run_dir=tmpdir)
        with HammerLoggingCaptureContext() as c:
            driver.run_synthesis()
        # TODO: reenable when logging fixed
        #assert c.log_contains("did not call super().export_config_outputs()")

    def test_bumps(self, tmp_path, request) -> None:
        # Test that HammerTool bump support works.
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir
        tech.logger = HammerVLSILogging.context("")

        test = DummyTool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        database = hammer_config.HammerDatabase()
        # Check bad mode string doesn't look at null dict
        settings = """{
     "vlsi.inputs.bumps_mode": "auto"
}"""
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_bumps = test.get_bumps()
        # TODO: reenable when logging fixed
        #assert c.log_contains("Invalid bumps_mode")
        assert my_bumps is None, "Invalid bumps_mode should assume empty bumps"

        settings = """{
     "vlsi.inputs.bumps_mode": "manual",
     "vlsi.inputs.bumps": {
                     "x": 14,
                     "y": 14,
                     "pitch": 200,
                     "cell": "MY_REDACTED_BUMP_CELL",
                     "assignments": [
                         {"name": "reset", "x": 5, "y": 3},
                         {"no_connect": true, "x": 5, "y": 4},
                         {"name": "VDD", "x": 2, "y": 1},
                         {"name": "VSS", "x": 1, "y": 1},
                         {"name": "VSS", "no_connect": true, "x": 2, "y": 2},
                         {"x": 3, "y": 3},
                         {"name": "VSS", "x": 14, "y": 14}
                     ]
                 }
 }
 """
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_bumps = test.get_bumps()
        # TODO: reenable when logging fixed
        #assert c.log_contains("Invalid bump assignment")
        assert my_bumps is not None
        # Only one of the assignments is invalid so the above 7 becomes 6
        assert len(my_bumps.assignments) == 6

    def test_good_pins(self, tmp_path, request) -> None:
        """
        Test that good pin configurations work without error.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_stackup(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["stackups"] = [StackupTestHelper.create_test_stackup(8, StackupTestHelper.mfr_grid()).dict()]
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_stackup)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir
        tech.logger = HammerVLSILogging.context("")

        test = DummyTool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        database = hammer_config.HammerDatabase()
        hammer_vlsi.HammerVLSISettings.load_builtins_and_core(database)

        settings = """
        {
        "technology.core.stackup": "StackupWith8Metals",
        "vlsi.inputs.pin_mode": "generated",
        "vlsi.inputs.pin.assignments": [
                     {"pins": "foo*", "side": "top", "layers": ["M5", "M3"]},
                     {"pins": "bar*", "side": "bottom", "layers": ["M5"]},
                     {"pins": "baz*", "side": "left", "layers": ["M4"]},
                     {"pins": "qux*", "side": "right", "layers": ["M2"]},
                     {"pins": "tx_n", "preplaced": true},
                     {"pins": "tx_p", "preplaced": true},
                     {"pins": "rx_n", "side": "left", "layers": ["M6"]},
                     {"pins": "rx_p", "side": "right", "layers": ["M6"]}
                 ]
        }
        """
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()

        # For a correct configuration, there should be no warnings
        # or errors.
        assert len(c.logs) == 0

        assert my_pins is not None
        assert len(my_pins) == 8

    def test_pin_modes(self, tmp_path, request) -> None:
        """
        Test that both full_auto and semi_auto pin modes work.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_stackup(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["stackups"] = [StackupTestHelper.create_test_stackup(8, StackupTestHelper.mfr_grid()).dict()]
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_stackup)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir
        tech.logger = HammerVLSILogging.context("")

        test = DummyTool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        database = hammer_config.HammerDatabase()
        hammer_vlsi.HammerVLSISettings.load_builtins_and_core(database)

        # Full-auto config should work in full_auto
        settings = """
        {
        "technology.core.stackup": "StackupWith8Metals",
        "vlsi.inputs.pin_mode": "generated",
        "vlsi.inputs.pin.generate_mode": "full_auto",
        "vlsi.inputs.pin.assignments": [
                     {"pins": "foo*", "side": "top", "layers": ["M5", "M3"]},
                     {"pins": "tx_n", "preplaced": true},
                     {"pins": "rx_n", "side": "left", "layers": ["M6"]}
                 ]
        }
        """
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()

        # TODO: reenable when logging fixed
        #assert len(c.logs) == 0
        assert my_pins is not None
        assert len(my_pins) == 3

        # Full-auto config should also work in semi_auto
        settings = """
        {
        "technology.core.stackup": "StackupWith8Metals",
        "vlsi.inputs.pin_mode": "generated",
        "vlsi.inputs.pin.generate_mode": "semi_auto",
        "vlsi.inputs.pin.assignments": [
                     {"pins": "foo*", "side": "top", "layers": ["M5", "M3"]},
                     {"pins": "tx_n", "preplaced": true},
                     {"pins": "rx_n", "side": "left", "layers": ["M6"]}
                 ]
        }
        """
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()

        assert len(c.logs) == 0
        assert my_pins is not None
        assert len(my_pins) == 3

        # Semi-auto config should work in semi_auto
        settings = """
        {
        "technology.core.stackup": "StackupWith8Metals",
        "vlsi.inputs.pin_mode": "generated",
        "vlsi.inputs.pin.generate_mode": "semi_auto",
        "vlsi.inputs.pin.assignments": [
                     {"pins": "foo*", "side": "top", "layers": ["M5", "M3"]},
                     {"pins": "tx_n", "preplaced": true},
                     {"pins": "rx_n", "side": "left", "layers": ["M6"], "width": 888.8}
                 ]
        }
        """
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()

        assert len(c.logs) == 0
        assert my_pins is not None
        assert len(my_pins) == 3

        # Semi-auto config should give errors in full_auto
        settings = """
        {
        "technology.core.stackup": "StackupWith8Metals",
        "vlsi.inputs.pin_mode": "generated",
        "vlsi.inputs.pin.generate_mode": "full_auto",
        "vlsi.inputs.pin.assignments": [
                     {"pins": "foo*", "side": "top", "layers": ["M5", "M3"]},
                     {"pins": "tx_n", "preplaced": true},
                     {"pins": "rx_n", "side": "left", "layers": ["M6"], "width": 888.8}
                 ]
        }
        """
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()

        # TODO: reenable when logging fixed
        #assert len(c.logs) == 1
        #assert "width requires semi_auto" in c.logs[0]

    def test_pins(self, tmp_path, request) -> None:
        """
        Test that HammerTool pin placement support works.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_stackup(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["stackups"] = [StackupTestHelper.create_test_stackup(8, StackupTestHelper.mfr_grid()).dict()]
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_stackup)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir
        tech.logger = HammerVLSILogging.context("")

        test = DummyTool()
        test.logger = HammerVLSILogging.context("")
        test.run_dir = str(tmp_path / "rundir")
        test.technology = tech
        database = hammer_config.HammerDatabase()
        hammer_vlsi.HammerVLSISettings.load_builtins_and_core(database)
        # Check bad mode string doesn't look at null dict
        settings = """
{
    "vlsi.inputs.pin_mode": "auto"
}
"""
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()
        # TODO: reenable when logging fixed
        #assert c.log_contains("Invalid pin_mode")
        assert len(my_pins) == 0, "Invalid pin_mode should assume empty pins"

        settings = """
{
    "technology.core.stackup": "StackupWith8Metals",
    "vlsi.inputs.pin_mode": "generated",
    "vlsi.inputs.pin.assignments": [
        {"pins": "*", "side": "top", "layers": ["M5", "M3"]},
        {"pins": "*", "side": "bottom", "layers": ["M5"]},
        {"pins": "*", "side": "left", "layers": ["M4"]},
        {"pins": "*", "side": "right", "layers": ["M2"]},
        {"pins": "bad_side", "side": "right", "layers": ["M3"]},
        {"pins": "tx1", "preplaced": true},
        {"pins": "bad_tx_n", "preplaced": true, "layers": ["M7"]},
        {"pins": "tx2", "preplaced": true, "side": "right", "layers": ["M7"]},
        {"pins": "tx3", "preplaced": true, "side": "right"},
        {"pins": "*", "layers": ["M2"]},
        {"pins": "*", "side": "bottom"},
        {"pins": "no_layers"},
        {"pins": "wrong_side", "side": "upsidedown", "layers": ["M2"]}
    ]
}
"""
        database.update_project([hammer_config.load_config_from_string(settings, is_yaml=False)])
        test.set_database(database)

        with HammerLoggingCaptureContext() as c:
            my_pins = test.get_pin_assignments()
        # TODO: reenable when logging fixed
        # assert c.log_contains("Pins bad_side assigned layers ")
        # assert c.log_contains("Pins bad_tx_n assigned as a preplaced pin with layers")
        # assert c.log_contains("Pins no_layers assigned without layers")
        # assert c.log_contains("Pins wrong_side have invalid side")
        assert my_pins is not None
        # Only one of the assignments is invalid so the above 7 becomes 6
        assert len(my_pins) == 9

    def test_hierarchical_width_height(self, tmp_path, request) -> None:
        """
        Test that hierarchical placements correctly propagate width and height.
        """
        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_stackup(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["stackups"] = [StackupTestHelper.create_test_stackup(8, StackupTestHelper.mfr_grid()).dict()]
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_stackup)
        sys.path.append(tech_dir_base)
        tmpdir = str(tmp_path / "tmpdir")
        os.mkdir(tmpdir)
        proj_config = os.path.join(tmpdir, "config.json")

        settings = {
                "vlsi.core.technology": f"{tech_name}",
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

        driver = hammer_vlsi.HammerDriver(
            hammer_vlsi.HammerDriver.get_default_driver_options()._replace(project_configs=[
                proj_config
            ], log_file=f"{tmpdir}/hammer-vlsi.log", obj_dir=f"{tmpdir}/obj_dir"))

        # This should not assert
        hier_settings = driver.get_hierarchical_settings()

        top_constraints = [x[1]["vlsi.inputs.placement_constraints"] for x in hier_settings if x[0] == "TopMod"][0]
        print(top_constraints)
        a = [x for x in top_constraints if x["type"] == "hierarchical" and x["master"] == "SubModA"][0]
        b = [x for x in top_constraints if x["type"] == "hierarchical" and x["master"] == "SubModB"][0]
        print(a)
        # Note that Decimals get serialized as strings
        assert a["width"] == "100"
        assert a["height"] == "200"
        assert b["width"] == "340"
        assert b["height"] == "160"

        # Corrupt SubModA's width and heights
        settings["vlsi.inputs.hierarchical.manual_placement_constraints"] = [
                    {"TopMod": [
                        {"path": "top", "type": "toplevel", "x": 0, "y": 0, "width": 1234, "height": 7890, "margins": {"left": 1, "top": 2, "right": 3, "bottom": 4}},
                        {"path": "top/C", "type": "placement", "x": 2, "y": 102, "width": 30, "height": 40},
                        {"path": "top/B", "type": "hierarchical", "x": 10, "y": 30, "master": "SubModB"},
                        {"path": "top/A", "type": "hierarchical", "x": 200, "y": 120, "width": 123, "height": 456, "master": "SubModA"}]},
                    {"SubModA": [
                        {"path": "a", "type": "toplevel", "x": 0, "y": 0, "width": 100, "height": 200, "margins": {"left": 0, "top": 0, "right": 0, "bottom": 0}}]},
                    {"SubModB": [
                        {"path": "b", "type": "toplevel", "x": 0, "y": 0, "width": 340, "height": 160, "margins": {"left": 0, "top": 0, "right": 0, "bottom": 0}}]}
                ]

        with open(proj_config, "w") as f:
            f.write(json.dumps(settings, cls=HammerJSONEncoder, indent=4))

        driver = hammer_vlsi.HammerDriver(
            hammer_vlsi.HammerDriver.get_default_driver_options()._replace(project_configs=[
                proj_config
            ], log_file=f"{tmpdir}/hammer-vlsi.log", obj_dir=f"{tmpdir}/obj_dir"))

        # This should assert because we mismatched SubModA's width and height with the master values
        with pytest.raises(ValueError):
            hier_settings = driver.get_hierarchical_settings()
