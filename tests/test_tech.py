#  Tests for hammer_tech.
#
#  See LICENSE for licence details.

import json
import os
import shutil
import sys
from typing import Any, Dict, List, Callable
import pathlib

import pytest

from hammer.vlsi import HammerVLSISettings

from hammer.logging import HammerVLSILogging, HammerVLSILoggingContext, HammerVLSIFileLogger
import hammer.tech as hammer_tech
from hammer.tech import LibraryFilter, Stackup, SpecialCell, CellType, DRCDeck, LVSDeck
from hammer.utils import deepdict
from hammer.config import HammerJSONEncoder
from decimal import Decimal

from utils.tool import HammerToolTestHelpers, DummyTool
from utils.tech import HasGetTech
from utils.stackup import StackupTestHelper


# Tests for the Hammer technology library (hammer_tech).
class TestHammerTechnology(HasGetTech):
    def test_filters_with_extra_extraction(self, tmpdir, request) -> None:
        """
        Test that filters whose extraction functions return extra (non-path)
        metadata.
        """

        # pylint: disable=too-many-locals
        import hammer.config as hammer_config
        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_named_library(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["libraries"].append({
                "name": "abcdef",
                "milkyway_techfile": "abcdef.tf"
            })
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_named_library)
        sys.path.append(tech_dir_base)
        (pathlib.Path(tech_dir) / "abcdef.tf").write_text("techfile")

        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
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

        test_filter = LibraryFilter(
            tag="metatest",
            description="Test filter that extracts metadata",
            is_file=True,
            filter_func=filter_func,
            paths_func=paths_func,
            extraction_func=extraction_func,
            sort_func=sort_func
        )

        database = hammer_config.HammerDatabase()
        tech.set_database(database)
        raw = tech.process_library_filter(pre_filts=[], filt=test_filter,
                                          must_exist=False,
                                          output_func=hammer_tech.HammerTechnologyUtils.to_plain_item)

        # Disable false positive from pylint
        outputs = list(map(lambda s: json.loads(s), raw))  # pylint: disable=unnecessary-lambda
        expected = [
            {"path": tech.prepend_dir_path("abcdef.tf"), "name": "abcdef"},
            {"path": tech.prepend_dir_path("coconut"), "name": ""},
            {"path": tech.prepend_dir_path("soy"), "name": ""}
        ]
        assert outputs == expected

    def test_process_library_filter_removes_duplicates(self, tmpdir, request) -> None:
        """
        Test that process_library_filter removes duplicates.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_duplicates(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict["libraries"].append({
                "name": "abcdef",
                "gds_file": "abcdef.gds"
            })
            out_dict["libraries"].append({
                "name": "abcdef2",
                "gds_file": "abcdef.gds"
            })
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_duplicates)
        sys.path.append(tech_dir_base)
        (pathlib.Path(tech_dir) / "abcdef.gds").write_text("gds1")

        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda s, _: [s])
        assert outputs == ["{0}/abcdef.gds".format(tech_dir)]

    @staticmethod
    def add_tarballs(tech_name: str) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
        """
        Helper method to take an input .tech.json and transform it for
        tarball tests.
        It replaces the source files with a single tarball and replaces
        the libraries with a single library that uses said tarball.
        :param in_dict: Input tech schema
        :return: Output tech schema for tarball tests
        """
        def inner(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            del out_dict["installs"]
            out_dict["tarballs"] = [{
                "root": {
                    "id": "foobar.tar.gz",
                    "path": f"technology.{tech_name}.tarball_dir"
                },
                "homepage": "http://www.example.com/tarballs"
            }]
            out_dict["libraries"] = [{
                "name": "abcdef",
                "gds_file": "foobar.tar.gz/test.gds"
            }]
            return out_dict
        return inner

    def test_tarballs_not_extracted(self, tmp_path, request) -> None:
        """
        Test that tarballs that are not pre-extracted work fine.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmp_path)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        # Add defaults to specify tarball_dir.
        with open(os.path.join(tech_dir, "defaults.json"), "w") as f:
            f.write(json.dumps({
                f"technology.{tech_name}.tarball_dir": tech_dir
            }, cls=HammerJSONEncoder))

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, self.add_tarballs(tech_name))
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        assert outputs == ["{0}/extracted/foobar.tar.gz/test.gds".format(tech_dir)]

    def test_tarballs_pre_extracted(self, tmpdir, request) -> None:
        """
        Test that tarballs that are pre-extracted also work as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        # Add defaults to specify tarball_dir.
        with open(os.path.join(tech_dir, "defaults.json"), "w") as f:
            f.write(json.dumps({
                f"technology.{tech_name}.tarball_dir": tech_dir,
                "vlsi.technology.extracted_tarballs_dir": tech_dir_base
            }, cls=HammerJSONEncoder))

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, self.add_tarballs(tech_name))
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        assert outputs == ["{0}/foobar.tar.gz/test.gds".format(tech_dir_base)]

    def test_tarballs_pre_extracted_tech_specific(self, tmpdir, request) -> None:
        """
        Test that tarballs that are pre-extracted and specified using a
        tech-specific setting work.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        # Add defaults to specify tarball_dir.
        with open(os.path.join(tech_dir, "defaults.json"), "w") as f:
            f.write(json.dumps({
                f"technology.{tech_name}.tarball_dir": tech_dir,
                "vlsi.technology.extracted_tarballs_dir": "/should/not/be/used",
                f"technology.{tech_name}.extracted_tarballs_dir": tech_dir_base
            }, cls=HammerJSONEncoder))

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, self.add_tarballs(tech_name))
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.gds_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        assert outputs == ["{0}/foobar.tar.gz/test.gds".format(tech_dir_base)]

    def test_extra_prefixes(self) -> None:
        """
        Test that extra_prefixes works properly as a property.
        """
        lib: hammer_tech.Library = hammer_tech.library_from_json('{"openaccess techfile": "test/oa"}')

        prefixes_orig = [hammer_tech.PathPrefix(id="test", path="/tmp/test")]

        prefixes = [hammer_tech.PathPrefix(id="test", path="/tmp/test")]
        # TODO: this isn't backwards compatible with the previous extra_prefixes API
        #  figure out why deep copying for just this one field was so important
        lib.extra_prefixes = prefixes.copy()
        # Check that we get the original back even after mutating the original list.
        prefixes.append(hammer_tech.PathPrefix(id="bar", path="/tmp/bar"))
        assert lib.extra_prefixes == prefixes_orig

        prefixes2 = lib.extra_prefixes.copy()
        # Check that we don't mutate the copy stored in the lib if we mutate after getting it
        prefixes2.append(hammer_tech.PathPrefix(id="bar", path="/tmp/bar"))
        assert lib.extra_prefixes == prefixes_orig

    def test_prepend_dir_path(self, tmpdir, request) -> None:
        """
        Test that the technology library can prepend directories correctly.
        """
        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)

        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir  # needs to be set for installs check

        # Check that a tech-provided prefix works fine
        assert "{0}/water".format(tech_dir) == tech.prepend_dir_path("cache/water")
        assert "{0}/fruit".format(tech_dir) == tech.prepend_dir_path("cache/fruit")

        # Check that a non-existent prefix gives an error
        with pytest.raises(ValueError):
            tech.prepend_dir_path("badprefix/file")

        # Check that a lib's custom prefix works
        from hammer.tech import ExtraLibrary
        lib = ExtraLibrary(
            library=hammer_tech.library_from_json("""{"milkyway_techfile": "custom/chair"}"""),
            prefix=hammer_tech.PathPrefix(
                id="custom",
                path="/tmp/custom"
            )
        ).store_into_library()  # type: hammer_tech.Library
        assert "{0}/hat".format("/tmp/custom") == tech.prepend_dir_path("custom/hat", lib)

    def test_installs_in_cache_dir(self, tmpdir, request) -> None:
        """
        Test that we can access files in the tech cache dir.
        Use case: A PDK file needs to be hacked by post_install_script
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        tech_json: Dict[str, Any] = {
            "name": f"{tech_name}",
            "installs": [
            ],
            "libraries": [
                {
                    "lef_file": "cache/tech.lef",
                    "provides": [
                        {"lib_type": "technology"}
                    ]
                }
            ]
        }

        with open(tech_json_filename, "w") as f:  # pyline: disable=invalid-name
            f.write(json.dumps(tech_json, cls=HammerJSONEncoder, indent=4))

        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        database = hammer_config.HammerDatabase()
        database.update_technology(tech.get_config())
        HammerVLSISettings.load_builtins_and_core(database)
        tech.set_database(database)
        outputs = tech.process_library_filter(pre_filts=[], filt=hammer_tech.filters.lef_filter,
                                              must_exist=False,
                                              output_func=lambda str, _: [str])

        assert outputs == ["{0}/tech.lef".format(tech.cache_dir)]

    def test_yaml_tech_file(self, tmpdir, request) -> None:
        """
        Test that we can load a yaml tech plugin
        """
        tech_yaml = """
name: My Technology Library
installs:
    - id: test
      path: "hammer.key.to.lib"
libraries: []
        """
        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)

        tech_yaml_filename = os.path.join(tech_dir, f"{tech_name}.tech.yml")
        with open(tech_yaml_filename, "w") as f:  # pylint: disable=invalid-name
            f.write(tech_yaml)
        sys.path.append(tech_dir_base)
        tech_opt = hammer_tech.HammerTechnology.load_from_module(tech_name)
        assert tech_opt is not None, "Unable to load technology"

    def test_gds_map_file(self, tmpdir, request) -> None:
        """
        Test that GDS map file support works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_gds_map(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"gds_map_file": "cache/gds_map_file"})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_gds_map)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        # Test that empty for gds_map_mode results in no map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'empty',
            'par.inputs.gds_map_file': None,
            'par.inputs.gds_map_resource': None
        }])
        assert tool.get_gds_map_file() is None

        # Test that manual mode for gds_map_mode works.
        database.update_project([{
            'par.inputs.gds_map_mode': 'manual',
            'par.inputs.gds_map_file': '/tmp/foo/bar',
            'par.inputs.gds_map_resource': None
        }])
        assert tool.get_gds_map_file() == '/tmp/foo/bar'

        # Test that auto mode for gds_map_mode works if the technology has a map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'auto',
            'par.inputs.gds_map_file': None,
            'par.inputs.gds_map_resource': None
        }])
        assert tool.get_gds_map_file() == '{tech}/gds_map_file'.format(tech=tech_dir)

        # Cleanup
        shutil.rmtree(tech_dir)

        # Create a new technology with no GDS map file.
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)

        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for gds_map_mode works if the technology has no map file.
        database.update_project([{
            'par.inputs.gds_map_mode': 'auto',
            'par.inputs.gds_map_file': None,
            'par.inputs.gds_map_resource': None
        }])
        assert tool.get_gds_map_file() is None

    def test_physical_only_cells_list(self, tmpdir, request) -> None:
        """
        Test that physical only cells list support works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_physical_only_cells_list(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"physical_only_cells_list": ["cell1", "cell2"]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_physical_only_cells_list)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
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
        assert tool.get_physical_only_cells() == ['cell1']

        # Test that auto mode for physical_only_cells_mode works if the technology has a physical only cells list.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'auto',
            'par.inputs.physical_only_cells_list': []
        }])

        assert tool.get_physical_only_cells() == tool.technology.config.physical_only_cells_list

        # Test that append mode for physical_only_cells_mode works if the everyone has a physical only cells list.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'append',
            'par.inputs.physical_only_cells_list': ['cell3']
        }])

        assert tool.get_physical_only_cells() == ['cell1', 'cell2', 'cell3']

        # Cleanup
        shutil.rmtree(tech_dir)

        # Create a new technology with no physical_only_cells list
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)

        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for physical only cells list works if the technology has no physical only cells list file.
        database.update_project([{
            'par.inputs.physical_only_cells_mode': 'auto',
            'par.inputs.physical_only_cells_list': []
        }])
        assert tool.get_physical_only_cells() == []

    def test_dont_use_list(self, tmpdir, request) -> None:
        """
        Test that "don't use" list support works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_dont_use_list(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"dont_use_list": ["cell1", "cell2"]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_dont_use_list)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
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
        assert tool.get_dont_use_list() == ['cell1']

        # Test that auto mode for dont_use_mode works if the technology has a "don't use" list.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'auto',
            'vlsi.inputs.dont_use_list': []
        }])

        assert tool.get_dont_use_list() == tool.technology.config.dont_use_list

        # Test that append mode for dont_use_mode works if the everyone has a "don't use" list.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'append',
            'vlsi.inputs.dont_use_list': ['cell3']
        }])

        assert tool.get_dont_use_list() == ['cell1', 'cell2', 'cell3']

        # Cleanup
        shutil.rmtree(tech_dir)

        # Create a new technology with no dont use list
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)

        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool.technology = tech

        # Test that auto mode for don't use list works if the technology has no don't use list file.
        database.update_project([{
            'vlsi.inputs.dont_use_mode': 'auto',
            'vlsi.inputs.dont_use_list': []
        }])
        assert tool.get_dont_use_list() == []

    def test_macro_sizes(self, tmpdir, request) -> None:
        """
        Test that getting macro sizes works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

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

END LIBRARY""")
            r = deepdict(d)
            r['libraries'].append({
                'name': 'my_vendor_lib',
                'lef_file': 'cache/my_vendor_lib.lef'
            })
            return r

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_lib_with_lef)
        sys.path.append(tech_dir_base)
        tech_opt = hammer_tech.HammerTechnology.load_from_module(tech_name)
        if tech_opt is None:
            assert False, "Unable to load technology"
            return
        else:
            tech = tech_opt  # type: hammer_tech.HammerTechnology
        tech.cache_dir = tech_dir

        with HammerVLSIFileLogger(os.path.join(tech_dir, "log")) as file_logger:
            HammerVLSILogging.clear_callbacks()
            HammerVLSILogging.add_callback(file_logger.callback)
            tech.logger = HammerVLSILogging.context("")
            #HammerVLSILogging.context("")

            database = hammer_config.HammerDatabase()
            tech.set_database(database)

            # Test that macro sizes can be read out of the LEF.
            assert tech.get_macro_sizes() == [
                hammer_tech.MacroSize(library='my_vendor_lib', name='my_awesome_macro',
                                      width=Decimal("810.522"), height=Decimal("607.525"))
            ]

    def test_special_cells(self, tmpdir, request) -> None:
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_special_cells(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"special_cells": [
                                {"name": ["cell1"], "cell_type": "tiehicell"},
                                {"name": ["cell2"], "cell_type": "tiehicell", "size": ["1.5"]},
                                {"name": ["cell3"], "cell_type": "iofiller", "size": ["0.5"], "input_ports": ["A", "B"], "output_ports": ["Y"]},
                                {"name": ["cell4"], "cell_type": "stdfiller", "input_ports": ["A"], "output_ports": ["Y", "Z"]},
                                {"name": ["cell5"], "cell_type": "endcap"},
                             ]})
            return out_dict
        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_special_cells)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        assert tool.technology.get_special_cell_by_type(CellType.TieHiCell) == [
            SpecialCell(name=list(["cell1"]), cell_type=CellType.TieHiCell, size=None, input_ports=None, output_ports=None),
            SpecialCell(name=list(["cell2"]), cell_type=CellType.TieHiCell, size=list(["1.5"]), input_ports=None, output_ports=None)
        ]

        assert tool.technology.get_special_cell_by_type(CellType.IOFiller) == [
            SpecialCell(name=list(["cell3"]), cell_type=CellType.IOFiller, size=list(["0.5"]), input_ports=list(["A","B"]), output_ports=list(["Y"]))
        ]

        assert tool.technology.get_special_cell_by_type(CellType.StdFiller) == [
            SpecialCell(name=list(["cell4"]), cell_type=CellType.StdFiller, size=None, input_ports=list(["A"]), output_ports=list(["Y", "Z"]))
        ]

        assert tool.technology.get_special_cell_by_type(CellType.EndCap) == [
            SpecialCell(name=list(["cell5"]), cell_type=CellType.EndCap, size=None, input_ports=None, output_ports=None)
        ]

        assert tool.technology.get_special_cell_by_type(CellType.TieLoCell) == []

    def test_drc_lvs_decks(self, tmpdir, request) -> None:
        """
        Test that getting the DRC & LVS decks works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        def add_drc_lvs_decks(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"drc_decks": [
                    {"tool_name": "hammer", "deck_name": "a_nail", "path": "/path/to/hammer/a_nail.drc.rules"},
                    {"tool_name": "chisel", "deck_name": "some_wood", "path": "/path/to/chisel/some_wood.drc.rules"},
                    {"tool_name": "hammer", "deck_name": "head_shark", "path": "/path/to/hammer/head_shark.drc.rules"}
                ]})
            out_dict.update({"lvs_decks": [
                    {"tool_name": "hammer", "deck_name": "a_nail", "path": "/path/to/hammer/a_nail.lvs.rules"},
                    {"tool_name": "chisel", "deck_name": "some_wood", "path": "/path/to/chisel/some_wood.lvs.rules"},
                    {"tool_name": "hammer", "deck_name": "head_shark", "path": "/path/to/hammer/head_shark.lvs.rules"}
                ]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_drc_lvs_decks)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        self.maxDiff = None
        assert tech.get_drc_decks_for_tool("hammer") == [
            DRCDeck(tool_name="hammer", deck_name="a_nail", path="/path/to/hammer/a_nail.drc.rules"),
            DRCDeck(tool_name="hammer", deck_name="head_shark", path="/path/to/hammer/head_shark.drc.rules")
        ]

        assert tech.get_lvs_decks_for_tool("hammer") == [
            LVSDeck(tool_name="hammer", deck_name="a_nail", path="/path/to/hammer/a_nail.lvs.rules"),
            LVSDeck(tool_name="hammer", deck_name="head_shark", path="/path/to/hammer/head_shark.lvs.rules")
        ]

        assert tech.get_drc_decks_for_tool("chisel") == [
            DRCDeck(tool_name="chisel", deck_name="some_wood", path="/path/to/chisel/some_wood.drc.rules")
        ]

        assert tech.get_lvs_decks_for_tool("chisel") == [
            LVSDeck(tool_name="chisel", deck_name="some_wood", path="/path/to/chisel/some_wood.lvs.rules")
        ]

    def test_get_stackups(self, tmpdir, request) -> None:
        """
        Test that getting the stackup works as expected.
        """
        import hammer.config as hammer_config

        tech_dir_base = str(tmpdir)
        tech_name = request.function.__name__  # create unique technology folders for each test
        tech_dir = HammerToolTestHelpers.create_tech_dir(tech_dir_base, tech_name)
        tech_json_filename = os.path.join(tech_dir, f"{tech_name}.tech.json")

        test_stackup = StackupTestHelper.create_test_stackup(10, StackupTestHelper.mfr_grid())

        def add_stackup(in_dict: Dict[str, Any]) -> Dict[str, Any]:
            out_dict = deepdict(in_dict)
            out_dict.update({"stackups": [test_stackup.dict()]})
            return out_dict

        HammerToolTestHelpers.write_tech_json(tech_json_filename, tech_name, add_stackup)
        sys.path.append(tech_dir_base)
        tech = self.get_tech(hammer_tech.HammerTechnology.load_from_module(tech_name))
        tech.cache_dir = tech_dir

        tool = DummyTool()
        tool.technology = tech
        database = hammer_config.HammerDatabase()
        tool.set_database(database)

        assert tech.get_stackup_by_name(test_stackup.name) == Stackup.from_setting(tech.get_grid_unit(), test_stackup.dict())
