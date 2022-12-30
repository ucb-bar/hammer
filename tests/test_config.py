#  Unit tests for the hammer_config module.
#
#  See LICENSE for licence details.

import os
import tempfile
import warnings
import pytest
import importlib.resources
from typing import List, Dict

import hammer.config as hammer_config


class TestHammerDatabase:
    # For tests that don't check against any types
    NO_TYPES = []  # type: List[Dict]

    def test_overriding(self) -> None:
        """
        Test that we can add a project first and technology after and still have it override.
        """
        db = hammer_config.HammerDatabase()
        db.update_project([{"tech.x": "foo"}])
        assert db.get_setting("tech.x", check_type=False) == "foo"
        db.update_technology([{"tech.x": "bar"}], self.NO_TYPES)
        assert db.get_setting("tech.x", check_type=False) == "foo"

    def test_unpacking(self) -> None:
        """
        Test that input configs get unpacked.
        """
        db = hammer_config.HammerDatabase()
        config = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: "yes"
        dac: "no"
""", is_yaml=True)
        db.update_core([config], self.NO_TYPES)
        assert db.get_setting("foo.bar.adc", check_type=False) == "yes"
        assert db.get_setting("foo.bar.dac", check_type=False) == "no"

    def test_no_config_junk(self) -> None:
        """Test that no _config_path junk variables get left behind."""
        db = hammer_config.HammerDatabase()
        db.update_core([hammer_config.load_config_from_string("key1: value1", is_yaml=True)], self.NO_TYPES)
        db.update_technology([hammer_config.load_config_from_string("key2: value2", is_yaml=True)], self.NO_TYPES)
        db.update_project([hammer_config.load_config_from_string("key3: value3", is_yaml=True)])
        for key in hammer_config.HammerDatabase.internal_keys():
            assert db.has_setting(key) is False, "Should not have internal key " + key

    def test_repeated_updates(self) -> None:
        """
        Test that repeated updates don't cause duplicates.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
a.b:
  c: []
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
a.b.c: ["test"]
a.b.c_meta: append
""", is_yaml=True)
        db.update_core([base], self.NO_TYPES)
        assert db.get_setting("a.b.c", check_type=False) == []
        db.update_project([meta])
        assert db.get_setting("a.b.c", check_type=False) == ["test"]
        db.update_technology([], self.NO_TYPES)
        assert db.get_setting("a.b.c", check_type=False) == ["test"]
        db.update_environment([])
        assert db.get_setting("a.b.c", check_type=False) == ["test"]

    def test_no_json_yaml_precedence(self) -> None:
        """
        Test that neither JSON nor YAML take precedence over each other.
        """
        yaml = """
foo.bar: "i'm yaml"
"""
        json = """{
    "foo.bar": "i'm json"
}
        """
        db1 = hammer_config.HammerDatabase()
        yaml_config = hammer_config.load_config_from_string(yaml, is_yaml=True)
        json_config = hammer_config.load_config_from_string(json, is_yaml=False)
        db1.update_core([hammer_config.combine_configs([yaml_config, json_config])], self.NO_TYPES)
        assert db1.get_setting("foo.bar", check_type=False) == "i'm json"

        db2 = hammer_config.HammerDatabase()
        db2.update_core([hammer_config.combine_configs([json_config, yaml_config])], self.NO_TYPES)
        assert db2.get_setting("foo.bar", check_type=False) == "i'm yaml"

    def test_meta_json2list(self) -> None:
        """
        Test that the meta attribute "json2list" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    flash: "yes"
    max: "min"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
    "foo.pipeline": "[\\"1\\", \\"2\\"]",
    "foo.pipeline_meta": "json2list"
}
    """, is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.flash", check_type=False) == "yes"
        assert db.get_setting("foo.max", check_type=False) == "min"
        assert db.get_setting("foo.pipeline", check_type=False) == ["1", "2"]

    def test_meta_lazyjson2list(self) -> None:
        """
        Test that the meta attribute "lazyjson2list" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    flash: "yes"
    max: "min"
    pipeline: "[]"
    pipeline_meta: "lazyjson2list"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
    "foo.pipeline": "[\\"1\\", \\"2\\"]"
}
    """, is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.flash", check_type=False) == "yes"
        assert db.get_setting("foo.max", check_type=False) == "min"
        assert db.get_setting("foo.pipeline", check_type=False) == ["1", "2"]

    def test_meta_subst(self) -> None:
        """
        Test that the meta attribute "subst" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    flash: "yes"
    one: "1"
    two: "2"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.pipeline": "${foo.flash}man",
  "foo.pipeline_meta": "subst",
  "foo.uint": ["${foo.one}", "${foo.two}"],
  "foo.uint_meta": "subst"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.flash", check_type=False) == "yes"
        assert db.get_setting("foo.pipeline", check_type=False) == "yesman"
        assert db.get_setting("foo.uint", check_type=False) == ["1", "2"]

    def test_meta_lazysubst(self) -> None:
        """
        Test that the meta attribute "lazysubst" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    flash: "yes"
    one: "1"
    two: "2"
style: "waterfall"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.pipeline": "${foo.flash}man",
  "foo.pipeline_meta": "subst",
  "foo.reg": "Wire",
  "foo.reginit": "${foo.reg}Init",
  "foo.reginit_meta": "lazysubst",
  "foo.later": "${later}",
  "foo.later_meta": "lazysubst",
  "foo.methodology": "${style} design",
  "foo.methodology_meta": "lazysubst"
}
""", is_yaml=False)
        project = hammer_config.load_config_from_string("""
{
  "later": "later",
  "style": "agile"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        db.update_project([project])
        assert db.get_setting("foo.flash", check_type=False) == "yes"
        assert db.get_setting("foo.pipeline", check_type=False) == "yesman"
        assert db.get_setting("foo.reginit", check_type=False) == "WireInit"
        assert db.get_setting("foo.later", check_type=False) == "later"
        assert db.get_setting("foo.methodology", check_type=False) == "agile design"

    def test_meta_lazysubst_array(self) -> None:
        """
        Check that lazysubst works correctly with an array.
        """
        db = hammer_config.HammerDatabase()
        d = hammer_config.load_config_from_string("""
        target: "foo"
        array: ["${target}bar"]
        array_meta: lazysubst
        """, is_yaml=True)
        db.update_core([d], self.NO_TYPES)
        assert db.get_setting("array", check_type=False) == ["foobar"]

    def test_meta_append(self) -> None:
        """
        Test that the meta attribute "append" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: "yes"
        dac: "no"
        dsl: ["scala"]
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.dsl": ["python"],
  "foo.bar.dsl_meta": "append",
  "foo.bar.dac": "current_weighted"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar.dac", check_type=False) == "current_weighted"
        assert db.get_setting("foo.bar.dsl", check_type=False) == ["scala", "python"]

    def test_meta_crossappend(self) -> None:
        """
        Test that the meta attribute "crossappend" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo.bar.dsl: ["scala"]
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.languages": ["foo.bar.dsl", ["python"]],
  "foo.bar.languages_meta": "crossappend"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar.dsl", check_type=False) == ["scala"]
        assert db.get_setting("foo.bar.languages", check_type=False) == ["scala", "python"]

    def test_meta_crossappendref(self) -> None:
        """
        Test that the meta attribute "crossappendref" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo.bar.dsl: ["scala"]
snakes: ["python"]
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.languages": ["foo.bar.dsl", "snakes"],
  "foo.bar.languages_meta": "crossappendref"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar.dsl", check_type=False) == ["scala"]
        assert db.get_setting("foo.bar.languages", check_type=False) == ["scala", "python"]

    def test_meta_crossref(self) -> None:
        """
        Test that the meta attribute "crossref" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
my:
    numbers: ["1", "2", "3"]
    dichotomy: false
    unity: true
    world: ["world"]
"target_key": "my.dichotomy"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "just.numbers": "my.numbers",
  "just.numbers_meta": "crossref",
  "copies.numbers": ["my.numbers", "my.world"],
  "copies.numbers_meta": "crossref",
  "bools": ["my.dichotomy", "my.unity"],
  "bools_meta": "crossref",
  "indirect.numbers": "${target_key}",
  "indirect.numbers_meta": ["subst", "crossref"]
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("just.numbers", check_type=False) == ["1", "2", "3"]
        assert db.get_setting("copies.numbers", check_type=False) == [["1", "2", "3"], ["world"]]
        assert db.get_setting("bools", check_type=False) == [False, True]
        assert db.get_setting("indirect.numbers", check_type=False) == False

    def test_meta_lazycrossref(self) -> None:
        """
        Test that lazy crossref works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
my:
    numbers: ["1", "2", "3"]
    """, is_yaml=True)
        meta = hammer_config.load_config_from_string("""
numbers: "my.numbers"
numbers_meta: crossref
lazy.numbers: "numbers"
lazy.numbers_meta: lazycrossref
    """, is_yaml=True)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("lazy.numbers", check_type=False) == ["1", "2", "3"]

    def test_meta_crossref_errors(self) -> None:
        """
        Test that the meta attribute "crossref" raises errors appropriately.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
my:
    numbers: ["1", "2", "3"]
    dichotomy: false
    unity: true
    world: ["world"]
"target_key": "my.dichotomy"
""", is_yaml=True)
        with pytest.raises(ValueError):
            meta = hammer_config.load_config_from_string("""
{
  "no_crossrefing_using_int": 123,
  "no_crossrefing_using_int_meta": "crossref"
}
""", is_yaml=False)
            db.update_core([base, meta], self.NO_TYPES)
            db.get_setting("no_crossrefing_using_int", check_type=False)
        with pytest.raises(ValueError):
            meta = hammer_config.load_config_from_string("""
{
  "no_crossrefing_using_bool": false,
  "no_crossrefing_using_bool_meta": "crossref"
}
""", is_yaml=False)
            db.update_core([base, meta], self.NO_TYPES)
            db.get_setting("no_crossrefing_using_bool", check_type=False)
        with pytest.raises(ValueError):
            meta = hammer_config.load_config_from_string("""
{
  "bad_list": [1, 2],
  "bad_list_meta": "crossref"
}
""", is_yaml=False)
            db.update_core([base, meta], self.NO_TYPES)
            db.get_setting("bad_list", check_type=False)

    def test_meta_prependlocal(self) -> None:
        """
        Test that the meta attribute "prependlocal" works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: "yes"
        dac: "no"
        dsl: ["scala"]
        base_test: "local_path"
        base_test_meta: prependlocal
""", is_yaml=True, path="base/config/path")
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.dsl": ["python"],
  "foo.bar.dsl_meta": "append",
  "foo.bar.dac": "current_weighted",
  "foo.bar.meta_test": "local_path",
  "foo.bar.meta_test_meta": "prependlocal"
}
""", is_yaml=False, path="meta/config/path")
        array = hammer_config.load_config_from_string("""
foo:
    bar:
        array_test: ["local_path", "express_path"]
        array_test_meta: prependlocal
""", is_yaml=True, path="array/config/path")
        db.update_core([base, meta, array], self.NO_TYPES)
        assert db.get_setting("foo.bar.dac", check_type=False) == "current_weighted"
        assert db.get_setting("foo.bar.dsl", check_type=False) == ["scala", "python"]
        assert db.get_setting("foo.bar.base_test", check_type=False) == "base/config/path/local_path"
        assert db.get_setting("foo.bar.meta_test", check_type=False) == "meta/config/path/local_path"
        assert db.get_setting("foo.bar.array_test", check_type=False) == ["array/config/path/local_path", "array/config/path/express_path"]

    def test_meta_transclude(self) -> None:
        """
        Test that the meta attribute "transclude" works.
        """
        # Put some text into the file.
        file_contents = "The quick brown fox jumps over the lazy dog"
        fd, path = tempfile.mkstemp(".txt")
        with open(path, "w") as f:
            f.write(file_contents)

        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
chips:
    potato: tuber
    bear: "yeah"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "chips.tree": "<path>",
  "chips.tree_meta": "transclude"
}
""".replace("<path>", path), is_yaml=False)

        db.update_core([base, meta], self.NO_TYPES)

        # Trigger merge before cleanup
        assert db.get_setting("chips.potato", check_type=False) == "tuber"

        # Cleanup
        os.remove(path)

        assert db.get_setting("chips.bear", check_type=False) == "yeah"
        assert db.get_setting("chips.tree", check_type=False) == file_contents

    def test_meta_transclude_subst(self) -> None:
        """
        Test that the meta attribute "transclude" works with "subst".
        """
        # Put some text into the file.
        file_contents = "I like ${food.condiment} on my ${food.dish}."
        file_contents_sol = "I like monosodium monochloride on my chips."
        local_path = "meta/config/path"
        fd, path = tempfile.mkstemp(".txt")
        with open(path, "w") as f:
            f.write(file_contents)

        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
food:
    condiment: "monosodium monochloride"
    dish: "chips"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "food.announcement": "<path>",
  "food.announcement_meta": ["transclude", "subst"]
}
""".replace("<path>", path), is_yaml=False)

        db.update_core([base, meta], self.NO_TYPES)

        # Trigger merge before cleanup
        assert db.get_setting("food.dish", check_type=False) == "chips"

        # Cleanup
        os.remove(path)

        assert db.get_setting("food.announcement", check_type=False) == file_contents_sol

    def test_meta_as_array_1(self) -> None:
        """
        Test meta attributes that are an array.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        base_test: "local_path"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.meta_test": "${foo.bar.base_test}",
  "foo.bar.meta_test_meta": ["subst"]
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar.base_test", check_type=False) == "local_path"
        assert db.get_setting("foo.bar.meta_test", check_type=False) == "local_path"

    def test_multiple_lazy_metas(self) -> None:
        """
        Test multiple lazy metas applied at once.
        Note that this is unsupported at the moment.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
hello1: "abc"
hello2: "def"
base: "hello1"
test: "${base}"
test_meta: ["lazysubst", "lazycrossref"]
    """, is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
    "base": "hello2"
}
    """, is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        with pytest.raises(ValueError) as cm:
            assert db.get_setting("base", check_type=False) == "hello2"
            assert db.get_setting("test", check_type=False) == "def"
        msg = str(cm)
        assert "Multiple lazy directives in a single directive array not supported yet" in msg

    def test_meta_append_bad(self) -> None:
        """
        Test that the meta attribute "append" catches bad inputs.
        """
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: "yes"
        dac: "no"
        dsl: "scala"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.dsl": ["python"],
  "foo.bar.dsl_meta": "append",
  "foo.bar.dac": "current_weighted"
}
""", is_yaml=False)
        with pytest.raises(ValueError):
            hammer_config.combine_configs([base, meta])

        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.dsl": "c++",
  "foo.bar.dsl_meta": "append",
  "foo.bar.dac": "current_weighted"
}
""", is_yaml=False)
        with pytest.raises(ValueError):
            hammer_config.combine_configs([base, meta])

    def test_load_yaml_empty_dict(self) -> None:
        """
        Test that load_yaml works with empty dictionaries.
        """
        assert hammer_config.load_yaml("x: {}") == {"x": {}}

    def test_meta_lazy_referencing_other_lazy(self) -> None:
        """
        Test that lazy settings can reference other lazy settings.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
global: "hello world"
tool1:
    common: "${global} tool1"
    common_meta: "lazysubst"
    a: "${tool1.common} abc"
    a_meta: "lazysubst"
    b: "${tool1.common} bcd"
    b_meta: "lazysubst"
tool2:
    common: "${global} tool2"
    common_meta: "lazysubst"
    x: "${tool2.common} xyz"
    x_meta: "lazysubst"
    z: "${tool2.common} zyx"
    z_meta: "lazysubst"
conglomerate: "${tool1.common} + ${tool2.common}"
conglomerate_meta: "lazysubst"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "global": "foobar"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("global", check_type=False) == "foobar"
        assert db.get_setting("tool1.common", check_type=False) == "foobar tool1"
        assert db.get_setting("tool1.a", check_type=False) == "foobar tool1 abc"
        assert db.get_setting("tool1.b", check_type=False) == "foobar tool1 bcd"
        assert db.get_setting("tool2.common", check_type=False) == "foobar tool2"
        assert db.get_setting("tool2.x", check_type=False) == "foobar tool2 xyz"
        assert db.get_setting("tool2.z", check_type=False) == "foobar tool2 zyx"
        assert db.get_setting("conglomerate", check_type=False) == "foobar tool1 + foobar tool2"

    def test_meta_lazysubst_other_lazysubst(self) -> None:
        """
        Check that a lazysubst which references other lazysubst works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    flash: "yes"
    one: "1"
    two: "2"
    lolcat: ""
    twelve: "${lolcat}"
    twelve_meta: lazysubst
    """, is_yaml=True)
        project = hammer_config.load_config_from_string("""
{
  "lolcat": "whatever",
  "later": "${foo.twelve}",
  "later_meta": "lazysubst"
}
    """, is_yaml=False)
        db.update_core([base], self.NO_TYPES)
        db.update_project([project])
        assert db.get_setting("lolcat", check_type=False) == "whatever"
        assert db.get_setting("foo.twelve", check_type=False) == "whatever"
        assert db.get_setting("later", check_type=False) == "whatever"

    def test_meta_lazycrossappendref(self) -> None:
        """
        Test that lazy crossappendref works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
global: ["hello", "world", "scala"]
tool_1: "global"
tool_1_meta: "lazycrossref"
snakes: ["python"]
tool: ["tool_1", "snakes"]
tool_meta: "lazycrossappendref"
""", is_yaml=True)
        db.update_core([base], self.NO_TYPES)
        assert db.get_setting("global", check_type=False) == ["hello", "world", "scala"]
        assert db.get_setting("tool", check_type=False) == ["hello", "world", "scala", "python"]

    def test_meta_lazycrossappend_with_lazycrossref(self) -> None:
        """
        Test that lazy crossappend works with lazy crossref in one file.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
global: ["hello", "world", "scala"]
tool_1: "global"
tool_1_meta: "lazycrossref"
tool: ["tool_1", ["python"]]
tool_meta: "lazycrossappend"
""", is_yaml=True)
        db.update_core([base], self.NO_TYPES)
        assert db.get_setting("global", check_type=False) == ["hello", "world", "scala"]
        assert db.get_setting("tool", check_type=False) == ["hello", "world", "scala", "python"]

    def test_meta_lazyappend_with_lazycrossref_2(self) -> None:
        """
        Test that lazy "append" works with lazy crossref.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
global: ["hello", "world"]
tool: "global"
tool_meta: "lazycrossref"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "global": ["scala"],
  "global_meta": "append",
  "tool": ["python"],
  "tool_meta": "lazyappend"
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("global", check_type=False) == ["hello", "world", "scala"]
        assert db.get_setting("tool", check_type=False) == ["hello", "world", "scala", "python"]

    def test_self_reference_lazysubst(self) -> None:
        """
        Test that self-referencing lazy subst works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
base_str: "hello"
derivative_str: "${base_str}"
derivative_str_meta: "lazysubst"
        """, is_yaml=True)
        config1 = hammer_config.load_config_from_string("""
{
    "derivative_str": "${derivative_str}_1",
    "derivative_str_meta": "lazysubst"
}
        """, is_yaml=True)
        config2 = hammer_config.load_config_from_string("""
{
    "derivative_str": "${derivative_str}_2",
    "derivative_str_meta": "lazysubst"
}
        """, is_yaml=True)
        db.update_core([base, config1, config2], self.NO_TYPES)
        assert db.get_setting("derivative_str", check_type=False) == "hello_1_2"

    def test_self_reference_lazycrossref(self) -> None:
        """
        Test that self-referencing lazy crossref works.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
base: "hello"
derivative: "base"
derivative_meta: "lazycrossref"
        """, is_yaml=True)
        config1 = hammer_config.load_config_from_string("""
{
    "derivative": "derivative",
    "derivative_meta": "lazycrossref"
}
        """, is_yaml=True)
        config2 = hammer_config.load_config_from_string("""
{
    "base": "tower",
    "derivative": "derivative",
    "derivative_meta": "lazycrossref"
}
        """, is_yaml=True)
        db.update_core([base, config1, config2], self.NO_TYPES)
        assert db.get_setting("base", check_type=False) == "tower"

    def test_self_reference_lazyappend(self) -> None:
        """
        Test that lazy "append" works.
        Note that append is always self-referencing.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
global: ["hello", "world"]
""", is_yaml=True)
        config1 = hammer_config.load_config_from_string("""
{
  "global": ["scala"],
  "global_meta": "lazyappend"
}
""", is_yaml=False)
        config2 = hammer_config.load_config_from_string("""
{
  "global": ["python"],
  "global_meta": "lazyappend"
}
""", is_yaml=False)
        db.update_core([base, config1], self.NO_TYPES)
        db.update_project([config2])
        assert db.get_setting("global", check_type=False) == ["hello", "world", "scala", "python"]

    def test_meta_deepsubst_cwd(self) -> None:
        """
        Test that the deepsubst special meta "cwd" correctly prepends the CWD.
        """
        cwd = os.getcwd()
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar_meta: deepsubst
    bar:
    - adc: "yes"
      dac: "no"
      dsl: ["scala"]
      base_test: "some_relative_path"
      base_test_deepsubst_meta: "cwd"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar_meta": ["append", "deepsubst"],
  "foo.bar": [{
      "dsl": ["python"],
      "dsl_meta": "append",
      "dac": "current_weighted",
      "meta_test": "some/relative/path",
      "meta_test_deepsubst_meta": "cwd",
      "abs_test": "/this/is/an/abs/path",
      "abs_test_deepsubst_meta": "cwd"
  }]
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar", check_type=False)[0]["base_test"] == os.path.join(cwd, "some_relative_path")
        assert db.get_setting("foo.bar", check_type=False)[1]["meta_test"] == os.path.join(cwd, "some/relative/path")
        # leading / should override the meta
        assert db.get_setting("foo.bar", check_type=False)[1]["abs_test"] == "/this/is/an/abs/path"

    def test_meta_deepsubst_local(self) -> None:
        """
        Test that the deepsubst special meta "local" correctly prepends the local path.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar_meta: deepsubst
    bar:
    - adc: "yes"
      dac: "no"
      dsl: ["scala"]
      base_test: "local_path"
      base_test_deepsubst_meta: "local"
""", is_yaml=True, path="base/config/path")
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar_meta": ["append", "deepsubst"],
  "foo.bar": [{
      "dsl": ["python"],
      "dsl_meta": "append",
      "dac": "current_weighted",
      "meta_test": "local_path",
      "meta_test_deepsubst_meta": "local",
      "abs_test": "/this/is/an/abs/path",
      "abs_test_deepsubst_meta": "local"
  }]
}
""", is_yaml=False, path="meta/config/path")
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar", check_type=False)[0]["base_test"] == "base/config/path/local_path"
        assert db.get_setting("foo.bar", check_type=False)[1]["meta_test"] == "meta/config/path/local_path"
        # leading / should override the meta
        assert db.get_setting("foo.bar", check_type=False)[1]["abs_test"] == "/this/is/an/abs/path"

    def test_meta_deepsubst_subst(self) -> None:
        """
        Test that deepsubst correctly substitutes strings.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    baz: "awesome"
    qux:
        adc: "yes"
        dac: "no"
        dsl: ["scala"]
        base_test: "local_path"
""", is_yaml=True)
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar_meta": "deepsubst",
  "foo.bar": [{
      "dsl": {"x": ["python", "is", "${foo.baz}"], "y": "sometimes"},
      "dsl_meta": "append",
      "dac": "current_weighted",
      "meta_test": "local_path",
      "meta_test_deepsubst_meta": "cwd"
  }]
}
""", is_yaml=False)
        db.update_core([base, meta], self.NO_TYPES)
        assert db.get_setting("foo.bar", check_type=False)[0]["dsl"] == {"x": ["python", "is", "awesome"], "y": "sometimes"}

    def test_load_types(self) -> None:
        """
        Test that type configurations are loaded with full package paths.
        """
        db = hammer_config.HammerDatabase()
        base_types = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: int
        dac: str
""", is_yaml=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            db.update_types([base_types])
        assert db.get_setting_type("foo.bar.adc") == int.__name__
        assert db.get_setting_type("foo.bar.dac") == str.__name__

    def test_load_imported_types(self) -> None:
        """
        Test that type configurations of imported types are loaded and checked.
        """
        db = hammer_config.HammerDatabase()
        base_types = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: list
        dac: dict
""", is_yaml=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            db.update_types([base_types])
        assert db.get_setting_type("foo.bar.adc") == list.__name__
        assert db.get_setting_type("foo.bar.dac") == dict.__name__

    def test_wrong_types(self) -> None:
        """
        Test that types are checked when retrieving settings.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: [1, 2, 3]
        dac: 0
        wrong: 0
""", is_yaml=True)
        base_types = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: list[int]
        dac: int
        wrong: list[dict[str, str]]
""", is_yaml=True)

        db.update_core([base], self.NO_TYPES)
        with pytest.raises(TypeError):
            db.update_core([base], [base_types])

        assert db.get_setting("foo.bar.adc") == [1, 2, 3]

    def test_wrong_constraints(self) -> None:
        """
        Test that custom constraints are checked when retrieving settings.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: [{name: \"hi\", pin: 1}]
        dac: [{name: [\"hi\"], pin: [1, 2]}]
        any: [{name: \"hi\", pin: [1, 2]}]
        wrong: [{name: \"hi\", pin: \"vdd\"}]
""", is_yaml=True)
        base_types = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: list[dict[str, str]]
        dac: list[dict[str, list]]
        any: list[dict[str, Any]]
        wrong: int
""", is_yaml=True)

        db.update_core([base], self.NO_TYPES)
        with pytest.raises(TypeError):
            db.update_core([base], [base_types])

        assert db.get_setting("foo.bar.adc") == [{"name": "hi", "pin": 1}]
        assert db.get_setting("foo.bar.dac") == [{"name": ["hi"], "pin": [1, 2]}]
        assert db.get_setting("foo.bar.any") == [{"name": "hi", "pin": [1, 2]}]

    def test_optional_constraints(self) -> None:
        """
        Test that optional constraints are ignored properly.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc:
        quu: hi
""", is_yaml=True)
        base_types = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: Optional[str]
        quu: Optional[str]
""", is_yaml=True)

        db.update_core([base], [base_types])

        assert db.get_setting("foo.bar.adc") is None
        assert db.get_setting("foo.bar.quu") == "hi"

    def test_decimal_constraints(self) -> None:
        """
        Test that Decimal constraints are checked properly.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: 3.14
        quu: 69
""", is_yaml=True)
        base_types = hammer_config.load_config_from_string("""
foo:
    bar:
        adc: float
        quu: float
""", is_yaml=True)

        db.update_core([base], self.NO_TYPES)
        with pytest.raises(TypeError):
            db.update_core([base], [base_types])

        assert db.get_setting("foo.bar.adc") == 3.14

    def test_default_types(self) -> None:
        """
        Test that all HAMMER defaults are properly type-checked.
        """

        base, base_types = hammer_config.load_config_from_defaults("hammer.config", types=True)
        builtins_yml = importlib.resources.files("hammer.config").joinpath("builtins.yml").read_text()
        builtins = hammer_config.load_config_from_string(builtins_yml, is_yaml=True)

        db = hammer_config.HammerDatabase()
        db.update_core(base, base_types)
        db.update_builtins([builtins])

        for k, v in db.get_config().items():
            assert db.get_setting(k) == v

    def test_get_settings_from_dict(self) -> None:
        """
        Test functionality, error handling, of utility funct: `get_settings_from_dict`.
        """
        
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
key_1: True
key_2: ["i", "c", "v"]
key_3: 123
key_4: 
abc.key: "largo"
def.a_key: "west"
def.b_key: "bank"
""", is_yaml=True)

        db.update_core([base], self.NO_TYPES)
        # 1st input tests basic functionality for mandatory keys.
        # 2nd input tests requests using a shared key_prefix.
        # 3rd input tests output when an optional key is queried for but not found. 
        # Note it must NOT use a default value if it was not specified to begin with.
        inputs   = [{"key_1": False, "key_2": [], "key_3": [], "key_4": "lvs", "abc.key": ""},
                    {"a_key": "", "b_key": ""},
                    {"key_1": False, "key_2": [], "opt_key":"123"}]
        prefixes = ["", "def", ""]
        opts     = [[],[], ["opt_key"]]
        refs     = [{"key_1": True, "key_2": ["i", "c", "v"], "key_3": 123, "key_4": "lvs", "abc.key": "largo"},
                    {"a_key": "west", "b_key": "bank"},
                    {"key_1": True, "key_2": ["i", "c", "v"], "opt_key": None}]

        # Test prefix functionality.
        for (input_dict, prefix, opt, ref) in zip(inputs, prefixes, opts, refs):
            assert db.get_settings_from_dict(input_dict, prefix, opt) == ref
        
        # In the final case, test error handling when mandatory keys are not specified.
        with pytest.raises(ValueError):
            db.get_settings_from_dict({"false_key": ""}) 
        