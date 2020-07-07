#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Helper and utility classes for testing HammerTool.
#
#  See LICENSE for licence details.

import json
import os
import tempfile
from abc import ABCMeta, abstractmethod
from numbers import Number
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import hammer_tech
from hammer_tech import LibraryFilter
from hammer_config import HammerJSONEncoder
import hammer_vlsi


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
    def create_tech_dir(tech_name: str) -> Tuple[str, str]:
        """
        Create a temporary folder for a test technology.
        Note: the caller is responsible for removing the tech_dir_base folder
        after use!
        :param tech_name: Technology name (e.g. "asap7")
        :return: Tuple of create tech_dir and tech_dir_base (which the caller
                 must delete)
        """
        tech_dir_base = tempfile.mkdtemp()
        tech_dir = os.path.join(tech_dir_base, tech_name)
        os.mkdir(tech_dir)
        tech_init_py = os.path.join(tech_dir, "__init__.py")
        with open(tech_init_py, "w") as f: # pylint: disable=invalid-name
            f.write("from hammer_tech import HammerTechnology\nclass {t}Technology(HammerTechnology):\n    pass\ntech = {t}Technology()".format(
                t=tech_name))

        return tech_dir, tech_dir_base

    @staticmethod
    def write_tech_json(
            tech_json_filename: str,
            postprocessing_func: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None) -> None:
        """
        Write a dummy tech JSON to the given filename with the given
        postprocessing.
        """
        tech_json = {
            "name": "dummy28",
            "grid_unit": "0.001",
            "time_unit": "1 ns",
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
            assert lib.openaccess_techfile is not None
            if lib.provides is not None and len(
                    list(filter(lambda x: x is not None and x.lib_type == "technology", lib.provides))) > 0:
                # Put technology first
                return (0, "")
            else:
                return (1, str(lib.openaccess_techfile))

        return LibraryFilter.new(
            filter_func=filter_func,
            paths_func=paths_func,
            tag="test", description="Test filter",
            is_file=True,
            sort_func=sort_func
        )
