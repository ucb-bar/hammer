#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer_tech.
#
#  See LICENSE for licence details.

# TODO: move this file out of hammer_vlsi.
# See issue #318.

import json
import os
import shutil
import unittest
import sys

from hammer_vlsi import HammerVLSISettings
from typing import Any, Dict, List, Optional

from hammer_logging import HammerVLSILogging
import hammer_tech
from hammer_tech import LibraryFilter, Stackup, Metal, WidthSpacingTuple, SpecialCell, CellType, DRCDeck, LVSDeck
from hammer_utils import deepdict
from hammer_config import HammerJSONEncoder
from decimal import Decimal

from test_tool_utils import HammerToolTestHelpers, DummyTool
from tech_test_utils import HasGetTech


class HammerTechnologyTest(HasGetTech, unittest.TestCase):
    """
    Tests for the Hammer technology library (hammer_tech).
    """

    def setUp(self) -> None:
        # Make sure the HAMMER_VLSI path is set correctly.
        self.assertTrue(HammerVLSISettings.set_hammer_vlsi_path_from_environment())

    def test_filters_with_extra_extraction(self) -> None:
        """
        Test that filters whose extraction functions return extra (non-path)
        metadata.
        """

        # pylint: disable=too-many-locals

        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_named_library(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["libraries"].append({
                "name": "abcdef",
                "milkyway techfile": "test/abcdef.tf"
            })
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_named_library)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        def filter_func(lib: hammer_tech.Library) -> bool:
            return lib.milkyway_techfile is not None

        def paths_func(lib: hammer_tech.Library) -> List[str]:
            assert lib.milkyway_techfile is not None
            return [lib.milkyway_techfile]

        def extraction_func(lib: hammer_tech.Library, paths: List[str]) -> List[str]:
            assert len(paths) == 1
            if lib.name is None:
                name = ""
            else:
                name = str(lib.name)
            return [json.dumps({"path": paths[0], "name": name}, cls=HammerJSONEncoder, indent=4)]

        def sort_func(lib: hammer_tech.Library):
            assert lib.milkyway_techfile is not None
            return lib.milkyway_techfile

        test_filter = LibraryFilter.new("metatest", "Test filter that extracts metadata",
                                        is_file=True, filter_func=filter_func,
                                        paths_func=paths_func,
                                        extraction_func=extraction_func,
                                        sort_func=sort_func)

        database = hammer_config.HammerDatabase()
        tech.set_database(database)
        raw = tech.process_library_filter(pre_filts=[], filt=test_filter,
                                          must_exist=False,
                                          output_func=hammer_tech.HammerTechnologyUtils.to_plain_item)

        # Disable false positive from pylint
        outputs = list(map(lambda s: json.loads(s), raw))  # pylint: disable=unnecessary-lambda
        self.assertEqual(outputs,
                         [
                             {"path": tech.prepend_dir_path("test/abcdef.tf"), "name": "abcdef"},
                             {"path": tech.prepend_dir_path("test/coconut"), "name": ""},
                             {"path": tech.prepend_dir_path("test/soy"), "name": ""}
                         ])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_process_library_filter_removes_duplicates(self) -> None:
        """
        Test that process_library_filter removes duplicates.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_duplicates(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["libraries"].append({
                "name": "abcdef",
                "gds file": "test/abcdef.gds"
            })
            out_dict["libraries"].append({
                "name": "abcdef2",
                "gds file": "test/abcdef.gds"
            })
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_duplicates)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        self.assertEqual(outputs, ["{0}/abcdef.gds".format(tech_dir)])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    @staticmethod
    def add_tarballs(in_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper method to take an input .tech.json and transform it for
        tarball tests.
        It replaces the source files with a single tarball and replaces
        the libraries with a single library that uses said tarball.
        :param in_dict: Input tech schema
        :return: Output tech schema for tarball tests
        """
        out_dict = deepdict(in_dict)
        del out_dict["installs"]
        out_dict["tarballs"] = [{
            "path": "foobar.tar.gz",
            "homepage": "http://www.example.com/tarballs",
            "base var": "technology.dummy28.tarball_dir"
        }]
        out_dict["libraries"] = [{
            "name": "abcdef",
            "gds file": "foobar.tar.gz/test.gds"
        }]
        return out_dict

    def test_tarballs_not_extracted(self) -> None:
        """
        Test that tarballs that are not pre-extracted work fine.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        # Add defaults to specify tarball_dir.
        with open(os.path.join(tech_dir, "defaults.json"), "w") as f:
            f.write(json.dumps({
                "technology.dummy28.tarball_dir": tech_dir
            }, cls=HammerJSONEncoder))

        HammerToolTestHelpers.write_tech_json(tech_json_filename, self.add_tarballs)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        self.assertEqual(outputs, ["{0}/extracted/foobar.tar.gz/test.gds".format(tech_dir)])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_tarballs_pre_extracted(self) -> None:
        """
        Test that tarballs that are pre-extracted also work as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        # Add defaults to specify tarball_dir.
        with open(os.path.join(tech_dir, "defaults.json"), "w") as f:
            f.write(json.dumps({
                "technology.dummy28.tarball_dir": tech_dir,
                "vlsi.technology.extracted_tarballs_dir": tech_dir_base
            }, cls=HammerJSONEncoder))

        HammerToolTestHelpers.write_tech_json(tech_json_filename, self.add_tarballs)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        self.assertEqual(outputs, ["{0}/foobar.tar.gz/test.gds".format(tech_dir_base)])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_tarballs_pre_extracted_tech_specific(self) -> None:
        """
        Test that tarballs that are pre-extracted and specified using a
        tech-specific setting work.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        # Add defaults to specify tarball_dir.
        with open(os.path.join(tech_dir, "defaults.json"), "w") as f:
            f.write(json.dumps({
                "technology.dummy28.tarball_dir": tech_dir,
                "vlsi.technology.extracted_tarballs_dir": "/should/not/be/used",
                "technology.dummy28.extracted_tarballs_dir": tech_dir_base
            }, cls=HammerJSONEncoder))

        HammerToolTestHelpers.write_tech_json(tech_json_filename, self.add_tarballs)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        self.assertEqual(outputs, ["{0}/foobar.tar.gz/test.gds".format(tech_dir_base)])

        # Cleanup
        shutil.rmtree(tech_dir_base)

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
        """
        Test that the technology library can prepend directories correctly.
        """
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
        tech = hammer_tech.HammerTechnology.load_from_json("dummy28", json.dumps(tech_json, cls=HammerJSONEncoder, indent=2), tech_dir)
        tech.cache_dir = tech_dir  # needs to be set for installs check

        # Check that a tech-provided prefix works fine
        self.assertEqual("{0}/water".format(tech_dir), tech.prepend_dir_path("test/water"))
        self.assertEqual("{0}/fruit".format(tech_dir), tech.prepend_dir_path("test/fruit"))

        # Check that a non-existent prefix gives an error
        with self.assertRaises(ValueError):
            tech.prepend_dir_path("badprefix/file")

        # Check that a lib's custom prefix works
        from hammer_tech import ExtraLibrary
        lib = ExtraLibrary(
            library=hammer_tech.library_from_json("""{"milkyway techfile": "custom/chair"}"""),
            prefix=hammer_tech.PathPrefix(
                prefix="custom",
                path="/tmp/custom"
            )
        ).store_into_library()  # type: hammer_tech.Library
        self.assertEqual("{0}/hat".format("/tmp/custom"), tech.prepend_dir_path("custom/hat", lib))

    def test_installs_in_cache_dir(self) -> None:
        """
        Test that we can access files in the tech cache dir.
        Use case: A PDK file needs to be hacked by post_install_script
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        tech_json = {
            "name": "dummy",
            "installs": [
                {
                    "path": "tech-dummy28-cache",
                    "base var": ""  # means relative to tech dir
                }
            ],
            "libraries": [
                {
                    "lef file": "tech-dummy28-cache/tech.lef",
                    "provides": [
                        {"lib_type": "technology"}
                    ]
                }
            ]
        }  # type: Dict[str, Any]

        with open(tech_json_filename, "w") as f:  # pyline: disable=invalid-name
            f.write(json.dumps(tech_json, cls=HammerJSONEncoder, indent=4))

        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.lef_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        self.assertEqual(outputs, ["{0}/tech.lef".format(tech.cache_dir)])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_yaml_tech_file(self) -> None:
        """
        Test that we can load a yaml tech plugin
        """
        tech_yaml = """
name: My Technology Library
installs:
    - path: test
      base var: ""  # means relative to tech dir
libraries: []
        """
        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")

        tech_yaml_filename = os.path.join(tech_dir, "dummy28.tech.yml")
        with open(tech_yaml_filename, "w") as f:  # pylint: disable=invalid-name
            f.write(tech_yaml)
        sys.path.append(tech_dir_base)
        tech_opt = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        self.assertFalse(tech_opt is None, "Unable to load technology")

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_gds_map_file(self) -> None:
        """
        Test that GDS map file support works as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_gds_map(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"gds map file": "test/gds_map_file"})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_gds_map)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
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
        shutil.rmtree(tech_dir_base)

        # Create a new technology with no GDS map file.
        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")

        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for gds_map_mode works if the technology has no map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'auto',
            'par.inputs.gds_map_file': None
        }])
        self.assertEqual(tool.get_gds_map_file(), None)

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_physical_only_cells_list(self) -> None:
        """
        Test that physical only cells list support works as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_physical_only_cells_list(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"physical only cells list": ["cell1", "cell2"]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_physical_only_cells_list)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        # Test that manual mode for physical_only_cells_mode works.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'manual',
            'par.inputs.physical_only_cells_list': ['cell1']
        }])
        self.assertEqual(tool.get_physical_only_cells(), ['cell1'])

        # Test that auto mode for physical_only_cells_mode works if the technology has a physical only cells list.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'auto',
            'par.inputs.physical_only_cells_list': []
        }])

        self.assertEqual(tool.get_physical_only_cells(), tool.technology.config.physical_only_cells_list)

        # Test that append mode for physical_only_cells_mode works if the everyone has a physical only cells list.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'append',
            'par.inputs.physical_only_cells_list': ['cell3']
        }])

        self.assertEqual(tool.get_physical_only_cells(), ['cell1', 'cell2', 'cell3'])

        # Cleanup
        shutil.rmtree(tech_dir_base)

        # Create a new technology with no physical_only_cells list
        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")

        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for physical only cells list works if the technology has no physical only cells list file.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'auto',
            'par.inputs.physical_only_cells_list': []
        }])
        self.assertEqual(tool.get_physical_only_cells(), [])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_dont_use_list(self) -> None:
        """
        Test that "don't use" list support works as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_dont_use_list(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"dont use list": ["cell1", "cell2"]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_dont_use_list)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        # Test that manual mode for dont_use_mode works.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'manual',
            'vlsi.inputs.dont_use_list': ['cell1']
        }])
        self.assertEqual(tool.get_dont_use_list(), ['cell1'])

        # Test that auto mode for dont_use_mode works if the technology has a "don't use" list.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'auto',
            'vlsi.inputs.dont_use_list': []
        }])

        self.assertEqual(tool.get_dont_use_list(), tool.technology.config.dont_use_list)

        # Test that append mode for dont_use_mode works if the everyone has a "don't use" list.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'append',
            'vlsi.inputs.dont_use_list': ['cell3']
        }])

        self.assertEqual(tool.get_dont_use_list(), ['cell1', 'cell2', 'cell3'])

        # Cleanup
        shutil.rmtree(tech_dir_base)

        # Create a new technology with no dont use list
        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")

        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for don't use list works if the technology has no don't use list file.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'auto',
            'vlsi.inputs.dont_use_list': []
        }])
        self.assertEqual(tool.get_dont_use_list(), [])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_macro_sizes(self) -> None:
        """
        Test that getting macro sizes works as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_lib_with_lef(d: Dict[str, Any]) -> Dict[str, Any]:
            with open(os.path.join(tech_dir, 'my_vendor_lib.lef'), 'w') as f:
                f.write("""VERSION 5.8 ;
BUSBITCHARS "[]" ;
DIVIDERCHAR "/" ;

MACRO my_awesome_macro
  CLASS BLOCK ;
  ORIGIN -0.435 607.525 ;
  FOREIGN my_awesome_macro 0.435 -607.525 ;
  SIZE 810.522 BY 607.525 ;
  SYMMETRY X Y R90 ;
END my_awesome_macro

END LIBRARY
                """)
            r = deepdict(d)
            r['libraries'].append({
                'name': 'my_vendor_lib',
                'lef file': 'test/my_vendor_lib.lef'
            })
            return r

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_lib_with_lef)
        sys.path.append(tech_dir_base)
        tech_opt = hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir)
        if tech_opt is None:
            self.assertTrue(False, "Unable to load technology")
            return
        else:
            tech = tech_opt  # type: hammer_tech.HammerTechnology
        tech.cache_dir = tech_dir

        tech.logger = HammerVLSILogging.context("")

        database = hammer_config.HammerDatabase()
        tech.set_database(database)

        # Test that macro sizes can be read out of the LEF.
        self.assertEqual(tech.get_macro_sizes(), [
            hammer_tech.MacroSize(library='my_vendor_lib', name='my_awesome_macro',
                                  width=Decimal("810.522"), height=Decimal("607.525"))
        ])

        # Cleanup
        shutil.rmtree(tech_dir_base)

    def test_special_cells(self) -> None:
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_special_cells(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"special_cells": [
                                {"name": ["cell1"], "cell_type": "tiehicell"},
                                {"name": ["cell2"], "cell_type": "tiehicell", "size": ["1.5"]},
                                {"name": ["cell3"], "cell_type": "iofiller", "size": ["0.5"]},
                                {"name": ["cell4"], "cell_type": "stdfiller"},
                                {"name": ["cell5"], "cell_type": "endcap"},
                             ]})
            return out_dict
        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_special_cells)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        self.assertEqual(tool.technology.get_special_cell_by_type(CellType.TieHiCell),
                [SpecialCell(name=list(["cell1"]), cell_type=CellType.TieHiCell, size=None, input_ports=None, output_ports=None),
                 SpecialCell(name=list(["cell2"]), cell_type=CellType.TieHiCell, size=list(["1.5"]), input_ports=None, output_ports=None)
                ])

        self.assertEqual(tool.technology.get_special_cell_by_type(CellType.IOFiller),
                [SpecialCell(name=list(["cell3"]), cell_type=CellType.IOFiller, size=list(["0.5"]), input_ports=list(["A","B"]), output_ports=list(["Y"]) )
                ])

        self.assertEqual(tool.technology.get_special_cell_by_type(CellType.StdFiller),
                [SpecialCell(name=list(["cell4"]), cell_type=CellType.StdFiller, size=None, input_ports=list(["A"]), output_ports=list(["Y","Z"]) )
                ])

        self.assertEqual(tool.technology.get_special_cell_by_type(CellType.EndCap),
                [SpecialCell(name=list(["cell5"]), cell_type=CellType.EndCap, size=None, input_ports=None, output_ports=None )
                ])

        self.assertEqual(tool.technology.get_special_cell_by_type(CellType.TieLoCell),
                [SpecialCell(name=list(["cell6"]), cell_type=CellType.TieLoCell, size=None, input_ports=None, output_ports=None )
                ])

        self.assertEqual(tool.technology.get_special_cell_by_type(CellType.TieHiCell),
                [SpecialCell(name=list(["cell7"]), cell_type=CellType.TieHiCell, size=None, input_ports=None, output_ports=None )
                ])

    def test_drc_lvs_decks(self) -> None:
        """
        Test that getting the DRC & LVS decks works as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        def add_drc_lvs_decks(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"drc decks": [
                    {"tool name": "hammer", "deck name": "a_nail", "path": "/path/to/hammer/a_nail.drc.rules"},
                    {"tool name": "chisel", "deck name": "some_wood", "path": "/path/to/chisel/some_wood.drc.rules"},
                    {"tool name": "hammer", "deck name": "head_shark", "path": "/path/to/hammer/head_shark.drc.rules"}
                ]})
            out_dict.update({"lvs decks": [
                    {"tool name": "hammer", "deck name": "a_nail", "path": "/path/to/hammer/a_nail.lvs.rules"},
                    {"tool name": "chisel", "deck name": "some_wood", "path": "/path/to/chisel/some_wood.lvs.rules"},
                    {"tool name": "hammer", "deck name": "head_shark", "path": "/path/to/hammer/head_shark.lvs.rules"}
                ]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_drc_lvs_decks)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        self.maxDiff = None
        self.assertEqual(tech.get_drc_decks_for_tool("hammer"),
                [DRCDeck(tool_name="hammer", name="a_nail", path="/path/to/hammer/a_nail.drc.rules"),
                 DRCDeck(tool_name="hammer", name="head_shark", path="/path/to/hammer/head_shark.drc.rules")
                ])

        self.assertEqual(tech.get_lvs_decks_for_tool("hammer"),
                [LVSDeck(tool_name="hammer", name="a_nail", path="/path/to/hammer/a_nail.lvs.rules"),
                 LVSDeck(tool_name="hammer", name="head_shark", path="/path/to/hammer/head_shark.lvs.rules")
                ])

        self.assertEqual(tech.get_drc_decks_for_tool("chisel"),
                [DRCDeck(tool_name="chisel", name="some_wood", path="/path/to/chisel/some_wood.drc.rules")])

        self.assertEqual(tech.get_lvs_decks_for_tool("chisel"),
                [LVSDeck(tool_name="chisel", name="some_wood", path="/path/to/chisel/some_wood.lvs.rules")])

    def test_stackup(self) -> None:
        """
        Test that getting the stackup works as expected.
        """
        import hammer_config

        tech_dir, tech_dir_base = HammerToolTestHelpers.create_tech_dir("dummy28")
        tech_json_filename = os.path.join(tech_dir, "dummy28.tech.json")

        test_stackup = StackupTestHelper.create_test_stackup_dict(10)

        def add_stackup(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"stackups": [test_stackup]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, add_stackup)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_dir("dummy28", tech_dir))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        self.assertEqual(
            tech.get_stackup_by_name(test_stackup["name"]),
            Stackup.from_setting(tech.get_grid_unit(), test_stackup)
        )

class StackupTestHelper:

    @staticmethod
    def mfr_grid() -> Decimal:
        return Decimal("0.001")

    @staticmethod
    def index_to_min_width_fn(index: int) -> float:
        assert index > 0
        return 0.05 * (1 if (index < 3) else (2 if (index < 5) else 5))

    @staticmethod
    def index_to_min_pitch_fn(index: int) -> float:
        return (StackupTestHelper.index_to_min_width_fn(index) * 9) / 5

    @staticmethod
    def index_to_offset_fn(index: int) -> float:
        return 0.04

    @staticmethod
    def create_wst_list(index: int) -> List[Dict[str, float]]:
        base_w = StackupTestHelper.index_to_min_width_fn(index)
        base_s = StackupTestHelper.index_to_min_pitch_fn(index) - base_w
        wst = []
        for x in range(5):
            wst.append({"width_at_least": x * base_w * 3,
                        "min_spacing": (x+1) * base_s})
        return wst

    @staticmethod
    def create_w_tbl(index: int, entries: int) -> List[float]:
        """
        Create a width table (power_strap_width_table).
        """
        min_w = StackupTestHelper.index_to_min_width_fn(index)
        return list(map(lambda x: min_w*x, range(1, 4 * entries + 1, 4)))

    @staticmethod
    def create_test_metal(index: int) -> Dict[str, Any]:
        output = {} # type: Dict[str, Any]
        output["name"] = "M{}".format(index)
        output["index"] = index
        output["direction"] = "vertical" if (index % 2 == 1) else "horizontal"
        output["min_width"] = StackupTestHelper.index_to_min_width_fn(index)
        output["pitch"] = StackupTestHelper.index_to_min_pitch_fn(index)
        output["offset"] = StackupTestHelper.index_to_offset_fn(index)
        output["power_strap_widths_and_spacings"] = StackupTestHelper.create_wst_list(index)
        output["power_strap_width_table"] = StackupTestHelper.create_w_tbl(index, 1)
        return output

    @staticmethod
    def create_test_stackup_dict(num_metals: int) -> Dict[str, Any]:
        output = {} # type: Dict[str, Any]
        output["name"] = "StackupWith{}Metals".format(num_metals)
        output["metals"] = []
        for x in range(num_metals):
            output["metals"].append(StackupTestHelper.create_test_metal(x+1))
        return output

    @staticmethod
    def create_test_site_dict() -> Dict[str, Any]:
        output = {} # type: Dict[str, Any]
        output["name"] = "CoreSite"
        # Make a 9-track horizontal std cell core site
        output["y"] = StackupTestHelper.create_test_metal(1)["pitch"] * 9
        output["x"] = StackupTestHelper.create_test_metal(2)["pitch"]
        return output

    @staticmethod
    def create_test_stackup_list() -> List["Stackup"]:
        output = []
        for x in range(5, 8):
            output.append(Stackup.from_setting(StackupTestHelper.mfr_grid(), StackupTestHelper.create_test_stackup_dict(x)))
            for m in output[-1].metals:
                assert m.grid_unit == StackupTestHelper.mfr_grid(), "FIXME: the unit grid is different between the tests and metals"
        return output


class StackupTest(unittest.TestCase):
    """
    Tests for the stackup APIs in stackup.py.
    """

    def test_wire_parsing_from_json(self) -> None:
        """
        Test that wires can be parsed correctly from JSON.
        """
        grid_unit = StackupTestHelper.mfr_grid()
        metal_dict = StackupTestHelper.create_test_metal(3)  # type: Dict[str, Any]
        direct_metal = Metal.from_setting(grid_unit, StackupTestHelper.create_test_metal(3))  # type: Metal
        json_string = json.dumps(metal_dict, cls=HammerJSONEncoder)  # type: str
        json_metal = Metal.from_setting(grid_unit, json.loads(json_string))  # type: Metal
        self.assertTrue(direct_metal, json_metal)

    def test_twt_wire(self) -> None:
        """
        Test that a T W T wire is correctly sized.
        This will pass if the wide wire does not have a spacing DRC violation
        to surrounding minimum-sized wires and is within a single unit grid.
        This method is not allowed to round the wire, so simply adding a
        manufacturing grid should suffice to "fail" DRC.
        """
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # Try with 1 track (this should return a minimum width wire)
            w, s, o = m.get_width_spacing_start_twt(1, logger=None)
            self.assertEqual(w, m.min_width)
            self.assertEqual(s, m.pitch - w)

            # e.g. 2 tracks:
            # | | | |
            # T  W  T
            # e.g. 4 tracks:
            # | | | | | |
            # T  --W--  T
            for num_tracks in range(2,40):
                w, s, o = m.get_width_spacing_start_twt(num_tracks, logger=None)
                # Check that the resulting spacing is the min spacing
                self.assertTrue(s >= m.get_spacing_for_width(w))
                # Check that there is no DRC
                self.assertGreaterEqual(m.pitch * (num_tracks + 1), m.min_width + s*2 + w)
                # Check that if we increase the width slightly we get a DRC violation
                w = w + (m.grid_unit * 2)
                s = m.get_spacing_for_width(w)
                self.assertLess(m.pitch * (num_tracks + 1), m.min_width + s*2 + w)

    def test_twwt_wire(self) -> None:
        """
        Test that a T W W T wire is correctly sized.
        This will pass if the wide wire does not have a spacing DRC violation
        to surrounding minimum-sized wires and is within a single unit grid.
        This method is not allowed to round the wire, so simply adding a
        manufacturing grid should suffice to "fail" DRC.
        """
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # Try with 1 track (this should return a minimum width wire)
            w, s, o = m.get_width_spacing_start_twwt(1, logger=None)
            self.assertEqual(w, m.min_width)
            self.assertEqual(s, m.pitch - w)

            # e.g. 2 tracks:
            # | | | | | |
            # T  W   W  T
            # e.g. 4 tracks:
            # | | | | | | | | | |
            # T  --W--   --W--  T
            for num_tracks in range(2,40):
                w, s, o = m.get_width_spacing_start_twwt(num_tracks, logger=None)
                # Check that the resulting spacing is the min spacing
                self.assertGreaterEqual(s, m.get_spacing_for_width(w))
                # Check that there is no DRC
                self.assertGreaterEqual(m.pitch * (2 * num_tracks + 1), m.min_width + s*3 + w*2)
                # Check that if we increase the width slightly we get a DRC violation
                w = w + (m.grid_unit*2)
                s = m.get_spacing_for_width(w)
                self.assertLess(m.pitch * (2 * num_tracks + 1), m.min_width + s*3 + w*2)


    def test_min_spacing_for_width(self) -> None:
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # generate some widths:
            for x in ["1.0", "2.0", "3.4", "4.5", "5.25", "50.2"]:
                # coerce to a manufacturing grid, this is just a test data point
                w = Decimal(x) * m.min_width
                s = m.get_spacing_for_width(w)
                for wst in m.power_strap_widths_and_spacings:
                    if w >= wst.width_at_least:
                        self.assertGreaterEqual(s, wst.min_spacing)

    def test_get_spacing_from_pitch(self) -> None:
        # Generate multiple stackups, but we'll only use the largest for this test
        stackup = StackupTestHelper.create_test_stackup_list()[-1]
        for m in stackup.metals:
            # generate some widths:
            for x in range(0, 100000, 5):
                # Generate a test data point
                p = (m.grid_unit * x) + m.pitch
                s = m.min_spacing_from_pitch(p)
                w = p - s
                # Check that we don't violate DRC
                self.assertGreaterEqual(p, w + m.get_spacing_for_width(w))
                # Check that the wire is as large as possible by growing it
                w = w + (m.grid_unit*2)
                self.assertLess(p, w + m.get_spacing_for_width(w))

    def test_quantize_to_width_table(self) -> None:
        # Generate two metals (index 1) and add more entries to width table of one of them
        # Only 0.05, 0.25, 0.45, 0.65, 0.85+ allowed -> check quantization against metal without width table
        # TODO: improve this behaviour in a future PR
        metal_dict = StackupTestHelper.create_test_metal(1)
        metal_dict["power_strap_width_table"] = StackupTestHelper.create_w_tbl(1, 5)
        q_metal = Metal.from_setting(StackupTestHelper.mfr_grid(), metal_dict)
        nq_metal = Metal.from_setting(StackupTestHelper.mfr_grid(), StackupTestHelper.create_test_metal(1))
        for num_tracks in range(1, 20):
            # twt case
            wq, sq, oq = q_metal.get_width_spacing_start_twt(num_tracks, logger=None)
            wnq, snq, onq = nq_metal.get_width_spacing_start_twt(num_tracks, logger=None)
            if wnq < Decimal('0.25'):
                self.assertEqual(wq, Decimal('0.05'))
            elif wnq < Decimal('0.45'):
                self.assertEqual(wq, Decimal('0.25'))
            elif wnq < Decimal('0.65'):
                self.assertEqual(wq, Decimal('0.45'))
            elif wnq < Decimal('0.85'):
                self.assertEqual(wq, Decimal('0.65'))
            else:
                self.assertEqual(wq, wnq)
            # twwt case
            wq, sq, oq = q_metal.get_width_spacing_start_twwt(num_tracks, logger=None)
            wnq, snq, onq = nq_metal.get_width_spacing_start_twwt(num_tracks, logger=None)
            if wnq < Decimal('0.25'):
                self.assertEqual(wq, Decimal('0.05'))
            elif wnq < Decimal('0.45'):
                self.assertEqual(wq, Decimal('0.25'))
            elif wnq < Decimal('0.65'):
                self.assertEqual(wq, Decimal('0.45'))
            elif wnq < Decimal('0.85'):
                self.assertEqual(wq, Decimal('0.65'))
            else:
                self.assertEqual(wq, wnq)

if __name__ == '__main__':
    unittest.main()
