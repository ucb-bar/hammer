#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Unit tests for the hammer_config module.
#
#  See LICENSE for licence details.

import os
import tempfile
import unittest
import warnings

import hammer_config


class HammerDatabaseTest(unittest.TestCase):

    def test_overriding(self) -> None:
        """
        Test that we can add a project first and technology after and still have it override.
        """
        db = hammer_config.HammerDatabase()
        db.update_project([{"tech.x": "foo"}])
        self.assertEqual(db.get_setting("tech.x", check_type=False), "foo")
        db.update_technology([{"tech.x": "bar"}])
        self.assertEqual(db.get_setting("tech.x", check_type=False), "foo")

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
        db.update_core([config])
        self.assertEqual(db.get_setting("foo.bar.adc", check_type=False), "yes")
        self.assertEqual(db.get_setting("foo.bar.dac", check_type=False), "no")

    def test_no_config_junk(self) -> None:
        """Test that no _config_path junk variables get left behind."""
        db = hammer_config.HammerDatabase()
        db.update_core([hammer_config.load_config_from_string("key1: value1", is_yaml=True)])
        db.update_technology([hammer_config.load_config_from_string("key2: value2", is_yaml=True)])
        db.update_project([hammer_config.load_config_from_string("key3: value3", is_yaml=True)])
        for key in hammer_config.HammerDatabase.internal_keys():
            self.assertFalse(db.has_setting(key), "Should not have internal key " + key)

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
        db.update_core([base])
        self.assertEqual(db.get_setting("a.b.c", check_type=False), [])
        db.update_project([meta])
        self.assertEqual(db.get_setting("a.b.c", check_type=False), ["test"])
        db.update_technology([])
        self.assertEqual(db.get_setting("a.b.c", check_type=False), ["test"])
        db.update_environment([])
        self.assertEqual(db.get_setting("a.b.c", check_type=False), ["test"])

    def test_no_json_yaml_precedence(self) -> None:
        """
        Test that neither JSON nor YAML take precedence over each other.
        """
        yfp, ypath = tempfile.mkstemp(".yml")
        with open(ypath, 'w') as fy:
            fy.write("""
foo.bar: "i'm yaml"
""")
        jfp, jpath = tempfile.mkstemp(".json")
        with open(jpath, 'w') as fj:
            fj.write("""
{
    "foo.bar": "i'm json"
}
""")
        db1 = hammer_config.HammerDatabase()
        configs = hammer_config.load_config_from_paths([ypath, jpath])
        db1.update_core([hammer_config.combine_configs(configs)])
        self.assertEqual(db1.get_setting("foo.bar", check_type=False), "i'm json")

        db2 = hammer_config.HammerDatabase()
        configs = hammer_config.load_config_from_paths([jpath, ypath])
        db2.update_core([hammer_config.combine_configs(configs)])
        self.assertEqual(db2.get_setting("foo.bar", check_type=False), "i'm yaml")

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.flash", check_type=False), "yes")
        self.assertEqual(db.get_setting("foo.max", check_type=False), "min")
        self.assertEqual(db.get_setting("foo.pipeline", check_type=False), ["1", "2"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.flash", check_type=False), "yes")
        self.assertEqual(db.get_setting("foo.max", check_type=False), "min")
        self.assertEqual(db.get_setting("foo.pipeline", check_type=False), ["1", "2"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.flash", check_type=False), "yes")
        self.assertEqual(db.get_setting("foo.pipeline", check_type=False), "yesman")
        self.assertEqual(db.get_setting("foo.uint", check_type=False), ["1", "2"])

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
        db.update_core([base, meta])
        db.update_project([project])
        self.assertEqual(db.get_setting("foo.flash", check_type=False), "yes")
        self.assertEqual(db.get_setting("foo.pipeline", check_type=False), "yesman")
        self.assertEqual(db.get_setting("foo.reginit", check_type=False), "WireInit")
        self.assertEqual(db.get_setting("foo.later", check_type=False), "later")
        self.assertEqual(db.get_setting("foo.methodology", check_type=False), "agile design")

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
        db.update_core([d])
        self.assertEqual(db.get_setting("array", check_type=False), ["foobar"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar.dac", check_type=False), "current_weighted")
        self.assertEqual(db.get_setting("foo.bar.dsl", check_type=False), ["scala", "python"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar.dsl", check_type=False), ["scala"])
        self.assertEqual(db.get_setting("foo.bar.languages", check_type=False), ["scala", "python"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar.dsl", check_type=False), ["scala"])
        self.assertEqual(db.get_setting("foo.bar.languages", check_type=False), ["scala", "python"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("just.numbers", check_type=False), ["1", "2", "3"])
        self.assertEqual(db.get_setting("copies.numbers", check_type=False), [["1", "2", "3"], ["world"]])
        self.assertEqual(db.get_setting("bools", check_type=False), [False, True])
        self.assertEqual(db.get_setting("indirect.numbers", check_type=False), False)

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("lazy.numbers", check_type=False), ["1", "2", "3"])

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
        with self.assertRaises(ValueError):
            meta = hammer_config.load_config_from_string("""
{
  "no_crossrefing_using_int": 123,
  "no_crossrefing_using_int_meta": "crossref"
}
""", is_yaml=False)
            db.update_core([base, meta])
            db.get_setting("no_crossrefing_using_int", check_type=False)
        with self.assertRaises(ValueError):
            meta = hammer_config.load_config_from_string("""
{
  "no_crossrefing_using_bool": false,
  "no_crossrefing_using_bool_meta": "crossref"
}
""", is_yaml=False)
            db.update_core([base, meta])
            db.get_setting("no_crossrefing_using_bool", check_type=False)
        with self.assertRaises(ValueError):
            meta = hammer_config.load_config_from_string("""
{
  "bad_list": [1, 2],
  "bad_list_meta": "crossref"
}
""", is_yaml=False)
            db.update_core([base, meta])
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
        db.update_core([base, meta, array])
        self.assertEqual(db.get_setting("foo.bar.dac", check_type=False), "current_weighted")
        self.assertEqual(db.get_setting("foo.bar.dsl", check_type=False), ["scala", "python"])
        self.assertEqual(db.get_setting("foo.bar.base_test", check_type=False), "base/config/path/local_path")
        self.assertEqual(db.get_setting("foo.bar.meta_test", check_type=False), "meta/config/path/local_path")
        self.assertEqual(db.get_setting("foo.bar.array_test", check_type=False), ["array/config/path/local_path", "array/config/path/express_path"])

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
""", is_yaml=True, path="base/config/path")
        meta = hammer_config.load_config_from_string("""
{
  "chips.tree": "<path>",
  "chips.tree_meta": "transclude"
}
""".replace("<path>", path), is_yaml=False, path="meta/config/path")

        db.update_core([base, meta])

        # Trigger merge before cleanup
        self.assertEqual(db.get_setting("chips.potato", check_type=False), "tuber")

        # Cleanup
        os.remove(path)

        self.assertEqual(db.get_setting("chips.bear", check_type=False), "yeah")
        self.assertEqual(db.get_setting("chips.tree", check_type=False), file_contents)

    def test_meta_transclude_prependlocal(self) -> None:
        """
        Test that the meta attribute "transclude" works with "prependlocal".
        """
        # Put some text into the file.
        file_contents = "The quick brown fox jumps over the lazy dog"
        local_path = "meta/config/path"
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
  "chips.tree_meta": ["transclude", "prependlocal"]
}
""".replace("<path>", path), is_yaml=False, path=local_path)

        db.update_core([base, meta])

        # Trigger merge before cleanup
        self.assertEqual(db.get_setting("chips.potato", check_type=False), "tuber")

        # Cleanup
        os.remove(path)

        self.assertEqual(db.get_setting("chips.bear", check_type=False), "yeah")
        self.assertEqual(db.get_setting("chips.tree", check_type=False), os.path.join(local_path, file_contents))

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
""".replace("<path>", path), is_yaml=False, path=local_path)

        db.update_core([base, meta])

        # Trigger merge before cleanup
        self.assertEqual(db.get_setting("food.dish", check_type=False), "chips")

        # Cleanup
        os.remove(path)

        self.assertEqual(db.get_setting("food.announcement", check_type=False), file_contents_sol)

    def test_meta_as_array_1(self) -> None:
        """
        Test meta attributes that are an array.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        base_test: "local_path"
""", is_yaml=True, path="base/config/path")
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.meta_test": "${foo.bar.base_test}",
  "foo.bar.meta_test_meta": ["subst"]
}
""", is_yaml=False, path="meta/config/path")
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar.base_test", check_type=False), "local_path")
        self.assertEqual(db.get_setting("foo.bar.meta_test", check_type=False), "local_path")

    def test_meta_subst_and_prependlocal(self) -> None:
        """
        Test meta attributes that are an array.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
foo:
    bar:
        base_test: "local_path"
""", is_yaml=True, path="base/config/path")
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.meta_test": ["${foo.bar.base_test}", "express_path"],
  "foo.bar.meta_test_meta": ["subst", "prependlocal"]
}
""", is_yaml=False, path="meta/config/path")
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar.base_test", check_type=False), "local_path")
        self.assertEqual(db.get_setting("foo.bar.meta_test", check_type=False), ["meta/config/path/local_path", "meta/config/path/express_path"])

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
        db.update_core([base, meta])
        with self.assertRaises(ValueError) as cm:
            self.assertEqual(db.get_setting("base", check_type=False), "hello2")
            self.assertEqual(db.get_setting("test", check_type=False), "def")
        msg = cm.exception.args[0]
        self.assertTrue("Multiple lazy directives in a single directive array not supported yet" in msg)

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
        with self.assertRaises(ValueError):
            hammer_config.combine_configs([base, meta])

        meta = hammer_config.load_config_from_string("""
{
  "foo.bar.dsl": "c++",
  "foo.bar.dsl_meta": "append",
  "foo.bar.dac": "current_weighted"
}
""", is_yaml=False)
        with self.assertRaises(ValueError):
            hammer_config.combine_configs([base, meta])

    def test_load_yaml_empty_dict(self) -> None:
        """
        Test that load_yaml works with empty dictionaries.
        """
        self.assertEqual(hammer_config.load_yaml("x: {}"), {"x": {}})

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("global", check_type=False), "foobar")
        self.assertEqual(db.get_setting("tool1.common", check_type=False), "foobar tool1")
        self.assertEqual(db.get_setting("tool1.a", check_type=False), "foobar tool1 abc")
        self.assertEqual(db.get_setting("tool1.b", check_type=False), "foobar tool1 bcd")
        self.assertEqual(db.get_setting("tool2.common", check_type=False), "foobar tool2")
        self.assertEqual(db.get_setting("tool2.x", check_type=False), "foobar tool2 xyz")
        self.assertEqual(db.get_setting("tool2.z", check_type=False), "foobar tool2 zyx")
        self.assertEqual(db.get_setting("conglomerate", check_type=False), "foobar tool1 + foobar tool2")

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
        db.update_core([base])
        db.update_project([project])
        self.assertEqual(db.get_setting("lolcat", check_type=False), "whatever")
        self.assertEqual(db.get_setting("foo.twelve", check_type=False), "whatever")
        self.assertEqual(db.get_setting("later", check_type=False), "whatever")

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
        db.update_core([base])
        self.assertEqual(db.get_setting("global", check_type=False), ["hello", "world", "scala"])
        self.assertEqual(db.get_setting("tool", check_type=False), ["hello", "world", "scala", "python"])

    def test_meta_lazycrossappendref_prepend_local(self) -> None:
        """
        Test that lazy crossappendref works to prepend the local path.
        """
        db = hammer_config.HammerDatabase()
        base = hammer_config.load_config_from_string("""
# These lines are present to test that the dependency graph with
# crossappendref is correct.
# If crossappendref doesn't declare a dependency, aaa* might not be recognized
# as a dependency of test.
aaa0: "tmp.tmptmp"
aaa0_meta: lazycrossref
aaa1: "tmp.tmptmp"
aaa1_meta: lazycrossref
test: ["aaa0", "aaa1"]
test_meta: "lazycrossappendref"

base: ["bin", "usr_bin"]
tmp.tmptmp2: "myfolder"
tmp.tmptmp2_meta: "prependlocal"
tmp.tmptmp: ["tmp.tmptmp2"]
tmp.tmptmp_meta: "lazycrossref"
paths: ["base", "tmp.tmptmp"]
paths_meta: "lazycrossappendref"
""", is_yaml=True, path="opt")
        db.update_core([base])
        self.assertEqual(db.get_setting("base", check_type=False), ["bin", "usr_bin"])
        self.assertEqual(db.get_setting("paths", check_type=False), ["bin", "usr_bin", "opt/myfolder"])
        self.assertEqual(db.get_setting("test", check_type=False), ["opt/myfolder", "opt/myfolder"])

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
        db.update_core([base])
        self.assertEqual(db.get_setting("global", check_type=False), ["hello", "world", "scala"])
        self.assertEqual(db.get_setting("tool", check_type=False), ["hello", "world", "scala", "python"])

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("global", check_type=False), ["hello", "world", "scala"])
        self.assertEqual(db.get_setting("tool", check_type=False), ["hello", "world", "scala", "python"])

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
        db.update_core([base, config1, config2])
        self.assertEqual(db.get_setting("derivative_str", check_type=False), "hello_1_2")

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
        db.update_core([base, config1, config2])
        self.assertEqual(db.get_setting("base", check_type=False), "tower")

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
        db.update_core([base, config1])
        db.update_project([config2])
        self.assertEqual(db.get_setting("global", check_type=False), ["hello", "world", "scala", "python"])

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
""", is_yaml=True, path="base/config/path")
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
""", is_yaml=False, path="meta/config/path")
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[0]["base_test"], os.path.join(cwd, "some_relative_path"))
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[1]["meta_test"], os.path.join(cwd, "some/relative/path"))
        # leading / should override the meta
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[1]["abs_test"], "/this/is/an/abs/path")

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
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[0]["base_test"], "base/config/path/local_path")
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[1]["meta_test"], "meta/config/path/local_path")
        # leading / should override the meta
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[1]["abs_test"], "/this/is/an/abs/path")


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
""", is_yaml=True, path="base/config/path")
        meta = hammer_config.load_config_from_string("""
{
  "foo.bar_meta": "deepsubst",
  "foo.bar": [{
      "dsl": {"x": ["python", "is", "${foo.baz}"], "y": "sometimes"},
      "dsl_meta": "append",
      "dac": "current_weighted",
      "meta_test": "local_path",
      "meta_test_deepsubst_meta": "local"
  }]
}
""", is_yaml=False, path="meta/config/path")
        db.update_core([base, meta])
        self.assertEqual(db.get_setting("foo.bar", check_type=False)[0]["dsl"], {"x": ["python", "is", "awesome"], "y": "sometimes"})

    def test_load_types(self) -> None:
        """
        Test that type configurations are loaded with full package paths.
        """
        db = hammer_config.HammerDatabase()
        base_types = hammer_config.load_config_types_from_string("""
foo:
    bar:
        adc: int
        dac: str
""", is_yaml=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            db.update_types([base_types])
        self.assertEqual(db.get_setting_type("foo.bar.adc"), int.__name__)
        self.assertEqual(db.get_setting_type("foo.bar.dac"), str.__name__)
        
    def test_load_imported_types(self) -> None:
        """
        Test that type configurations of imported types are loaded and checked.
        """
        db = hammer_config.HammerDatabase()
        base_types = hammer_config.load_config_types_from_string("""
foo:
    bar:
        adc: list
        dac: dict
""", is_yaml=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            db.update_types([base_types])
        self.assertEqual(db.get_setting_type("foo.bar.adc"), list.__name__)
        self.assertEqual(db.get_setting_type("foo.bar.dac"), dict.__name__)

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

        db.update_core([base])
        with self.assertRaises(TypeError):
            db.update_types([base_types])

        self.assertEqual(db.get_setting("foo.bar.adc"), [1, 2, 3])

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

        db.update_core([base])
        with self.assertRaises(TypeError):
            db.update_types([base_types])

        self.assertEqual(db.get_setting("foo.bar.adc"), [{"name": "hi", "pin": 1}])
        self.assertEqual(db.get_setting("foo.bar.dac"), [{"name": ["hi"], "pin": [1, 2]}])
        self.assertEqual(db.get_setting("foo.bar.any"), [{"name": "hi", "pin": [1, 2]}])

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

        db.update_core([base])
        db.update_types([base_types])
        
        self.assertIsNone(db.get_setting("foo.bar.adc"))
        self.assertEqual(db.get_setting("foo.bar.quu"), "hi")

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

        db.update_core([base])
        with self.assertRaises(TypeError):
            db.update_types([base_types])
        
        self.assertEqual(db.get_setting("foo.bar.adc"), 3.14)

    def test_default_types(self) -> None:
        """
        Test that all HAMMER defaults are properly type-checked.
        """
        CFG_PATH = os.path.join(os.path.dirname(os.getcwd()), "hammer-vlsi")
        BL_PATH = os.path.join(os.path.dirname(os.getcwd()), "hammer-vlsi", "builtins.yml")

        base = hammer_config.load_config_from_defaults(CFG_PATH)
        base_types = hammer_config.load_config_types_from_defaults(CFG_PATH)
        builtins = hammer_config.load_config_from_file(BL_PATH)

        db = hammer_config.HammerDatabase()
        db.update_core(base[1:])
        db.update_builtins([builtins])
        db.update_types(base_types)

        for k, v in db.get_config().items():
            self.assertEqual(db.get_setting(k), v)

if __name__ == '__main__':
    unittest.main()
