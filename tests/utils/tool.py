#  Helper and utility classes for testing HammerTool.
#
#  See LICENSE for licence details.

import json
import os
from abc import ABCMeta, abstractmethod
from numbers import Number
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import pathlib

import hammer.tech as hammer_tech
from hammer.tech import LibraryFilter
from hammer.config import HammerJSONEncoder
import hammer.vlsi as hammer_vlsi


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


class HammerToolTestHelpers:
    """
    Helper functions to aid in the testing of IP library filtering/processing.
    """

    @staticmethod
    def create_tech_dir(tech_dir_base: str, tech_name: str) -> str:
        """
        Create a test technology package.
        :param tech_dir_base: The directory in which to create the technology package
        :param tech_name: Technology name (e.g. "asap7")
        :return: The path to the created tech_dir within tech_dir_base
        """
        tech_dir = os.path.join(tech_dir_base, tech_name)
        os.mkdir(tech_dir)
        tech_init_py = os.path.join(tech_dir, "__init__.py")
        with open(tech_init_py, "w") as f: # pylint: disable=invalid-name
            f.write(f"""from hammer.tech import HammerTechnology
class {tech_name}Technology(HammerTechnology):
    pass
tech = {tech_name}Technology()""")

        p = pathlib.Path(tech_dir_base) / tech_name
        (p / "soy").write_text("soy milkyway")
        (p / "juice").write_text("juice OA")
        (p / "coconut").write_text("coconut milkyway")
        (p / "orange").write_text("orange OA stdcell")
        (p / "grapefruit").write_text("grapefruit OA stdcell")
        (p / "tea").write_text("tea OA tech")

        return tech_dir

    @staticmethod
    def write_tech_json(
            tech_json_filename: str,
            tech_name: str,
            postprocessing_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> None:
        """
        Write a dummy tech JSON to the given filename with the given
        postprocessing.
        """
        tech_json = {
            "name": tech_name,
            "grid_unit": "0.001",
            "time_unit": "1 ns",
            "installs": [],
            "libraries": [
                {"milkyway_techfile": "soy"},
                {"openaccess_techfile": "juice"},
                {"milkyway_techfile": "coconut"},
                {
                    "openaccess_techfile": "orange",
                    "provides": [
                        {"lib_type": "stdcell"}
                    ]
                },
                {
                    "openaccess_techfile": "grapefruit",
                    "provides": [
                        {"lib_type": "stdcell"}
                    ]
                },
                {
                    "openaccess_techfile": "tea",
                    "provides": [
                        {"lib_type": "technology"}
                    ]
                },
            ]
        }  # type: Dict[str, Any]
        if postprocessing_func is not None:
            tech_json = postprocessing_func(tech_json)
        with open(tech_json_filename, "w") as f:  # pylint: disable=invalid-name
            f.write(json.dumps(tech_json, cls=HammerJSONEncoder, indent=4))

    @staticmethod
    def make_test_filter() -> LibraryFilter:
        """
        Make a test filter that returns libraries with openaccess techfiles with libraries that provide 'technology'
        in lib_type first, with the rest sorted by the openaccess techfile.
        """
        def filter_func(lib: hammer_tech.Library) -> bool:
            return lib.openaccess_techfile is not None

        def paths_func(lib: hammer_tech.Library) -> List[str]:
            assert lib.openaccess_techfile is not None
            return [lib.openaccess_techfile]

        def sort_func(lib: hammer_tech.Library) -> Union[Number, str, tuple]:
            print(lib.openaccess_techfile, lib.provides)
            assert lib.openaccess_techfile is not None
            if lib.provides is not None and len(
                    list(filter(lambda x: x is not None and x.lib_type == "technology", lib.provides))) > 0:
                # Put technology first
                return (0, "")
            else:
                if "/" in lib.openaccess_techfile:
                    return (1, lib.openaccess_techfile.split('/')[1])
                else:
                    return (1, str(lib.openaccess_techfile))

        return LibraryFilter(
            filter_func=filter_func,
            paths_func=paths_func,
            tag="test", description="Test filter",
            is_file=True,
            sort_func=sort_func
        )
