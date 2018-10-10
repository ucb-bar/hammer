#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>
#
#  Build the configuration database from a series of JSON config files.
#  Dumps the output in JSON format to standard output.
#  See README.config for more details.

# pylint: disable=invalid-name

from typing import Iterable, List, Union, Callable, Any, Dict, Set

from hammer_utils import deepdict
from .yaml2json import load_yaml # grumble grumble

from functools import reduce
import json
import os
import re
import sys

# Special key used for meta directives which require config paths like prependlocal.
CONFIG_PATH_KEY = "_config_path"


def unpack(config_dict: dict, prefix: str = "") -> dict:
    """
    Unpack the given config_dict, flattening key names recursively.
    >>> p = unpack({"one": 1, "two": 2}, prefix="snack")
    >>> p == {'snack.one': 1, 'snack.two': 2}
    True
    >>> p = unpack({"a": {"foo": 1, "bar": 2}})
    >>> p == {'a.foo': 1, 'a.bar': 2}
    True
    >>> p = unpack({"a.b": {"foo": 1, "bar": 2}})
    >>> p == {"a.b.foo": 1, "a.b.bar": 2}
    True
    >>> p = unpack({
    ...     "a": {
    ...         "foo": 1,
    ...         "bar": 2
    ...     },
    ...     "b": {
    ...         "baz": 3,
    ...         "boom": {"rocket": "chip", "hwacha": "vector"}
    ...     },
    ... })
    >>> p == {"a.foo": 1, "a.bar": 2, "b.baz": 3, "b.boom.rocket": "chip",
    ...     "b.boom.hwacha": "vector"}
    True
    """
    # We don't want an extra "." in the beginning.
    real_prefix = "" if prefix == "" else prefix + "."
    output_dict = {}
    for key, value in config_dict.items():
        if isinstance(value, dict):
            output_dict.update(unpack(value, real_prefix + key))
        else:
            output_dict[real_prefix + key] = value
    return output_dict


def reverse_unpack(input_dict: dict) -> dict:
    """
    Reverse the effects of unpack(). Mainly useful for testing purposes.
    >>> p = reverse_unpack({"a.b": 1})
    >>> p == {"a": {"b": 1}}
    True
    :param input: Unpacked input_dict dictionary
    :return: Packed equivalent of input_dict
    """
    output_dict = {}  # type: Dict[str, Any]

    def get_subdict(parts: List[str], current_root: dict) -> dict:
        if len(parts) == 0:
            return current_root
        else:
            if parts[0] not in current_root:
                current_root[parts[0]] = {}
            return get_subdict(parts[1:], current_root[parts[0]])

    for key, value in input_dict.items():
        key_parts = key.split(".")
        if len(key_parts) >= 1:
            containing_dict = get_subdict(key_parts[:-1], output_dict)
        else:
            assert False, "Cannot have blank key"
        containing_dict[key_parts[-1]] = value
    return output_dict


__VARIABLE_EXPANSION_REGEX = r'\${([a-zA-Z_\-\d.]+)}'


def update_and_expand_meta(config_dict: dict, meta_dict: dict) -> dict:
    """
    Expand the meta directives for the given config dict and return a new
    dictionary containing the updated settings with respect to the base config_dict.

    :param config_dict: Base config.
    :param meta_dict: Dictionary with potentially new meta directives.
    :return: New dictionary with meta_dict updating config_dict.
    """

    def perform_subst(value: Union[str, List[str]]) -> Union[str, List[str]]:
        """
        Perform substitutions for the given value.
        If value is a string, perform substitutions in the string. If value is a list, then perform substitutions
        in every string in the list.
        :param value: String or list
        :return: String or list but with everything substituted.
        """

        def subst_str(input_str: str) -> str:
            """Substitute ${...}"""
            return re.sub(__VARIABLE_EXPANSION_REGEX, lambda x: config_dict[x.group(1)], input_str)

        newval = ""  # type: Union[str, List[str]]

        if isinstance(value, list):
            newval = list(map(subst_str, value))
        else:
            newval = subst_str(value)
        return newval

    # Helper functions to implement each meta directive.
    def meta_append(config_dict: dict, key: str, value: Any) -> None:
        if key not in config_dict:
            config_dict[key] = []

        if not isinstance(config_dict[key], list):
            raise ValueError("Trying to append to non-list setting %s" % (key))
        if not isinstance(value, list):
            raise ValueError("Trying to append to list %s with non-list %s" % (key, str(value)))
        config_dict[key] += value

    def meta_subst(config_dict: dict, key: str, value: Any) -> None:
        config_dict[key] = perform_subst(value)

    def meta_transclude(config_dict: dict, key: str, value: Any) -> None:
        """Transclude the contents of the file pointed to by value."""
        assert isinstance(value, str), "Path to file for transclusion must be a string"
        with open(value, "r") as f:
            file_contents = str(f.read())
        config_dict[key] = file_contents

    def meta_json2list(config_dict: dict, key: str, value: Any) -> None:
        """Turn the value of the key (JSON list) into a list."""
        assert isinstance(value, str), "json2list requires a JSON string that is a list"
        parsed = json.loads(value)
        assert isinstance(parsed, list), "json2list requires a JSON string that is a list"
        config_dict[key] = parsed

    def make_meta_dynamic(dynamic_meta: str) -> Callable[[dict, str, Any], None]:
        """
        Create a meta_dynamicFOO function.
        :param dynamic_meta: Dynamic meta type e.g. "dynamicsubst"
        :return: A function for meta_directive_functions.
        """

        def meta_dynamic(config_dict: dict, key: str, value: Any) -> None:
            # Do nothing at this stage, since we need to deal with dynamicsubst only after
            # everything has been bound.
            config_dict[key] = value
            config_dict[key + "_meta"] = dynamic_meta

        return meta_dynamic

    def meta_prependlocal(config_dict: dict, key: str, value) -> None:
        """Prepend the local path of the config dict."""
        config_dict[key] = os.path.join(meta_dict[CONFIG_PATH_KEY], str(value))

    # Lookup table of meta functions.
    meta_directive_functions = {
        'append': meta_append,
        'subst': meta_subst,
        'dynamicsubst': make_meta_dynamic('dynamicsubst'),
        'transclude': meta_transclude,
        'dynamictransclude': make_meta_dynamic('dynamictransclude'),
        'json2list': meta_json2list,
        'dynamicjson2list': make_meta_dynamic('dynamicjson2list'),
        'prependlocal': meta_prependlocal
    }  # type: Dict[str, Callable[[dict, str, Any], None]]

    newdict = deepdict(config_dict)

    # Find meta directives.
    assert isinstance(meta_dict, dict)
    meta_dict = deepdict(meta_dict)  # create a copy so we can remove items.
    meta_dict_keys = list(meta_dict.keys())
    meta_keys = filter(lambda k: k.endswith("_meta"), meta_dict_keys)

    # Deal with meta directives.
    meta_len = len("_meta")
    for meta_key in meta_keys:
        setting = meta_key[:-meta_len]
        meta_type_from_dict = meta_dict[meta_key]  # type: Union[str, List[str]]
        meta_directives = []  # type: List[str]
        if isinstance(meta_type_from_dict, str):
            meta_directives = [meta_type_from_dict]
        else:
            assert isinstance(meta_type_from_dict, List)
            meta_directives = meta_type_from_dict

        # Process each meta type in order.
        for meta_type in meta_directives:
            if not isinstance(meta_type, str):
                raise TypeError("meta_type was not a string: " + repr(meta_type))
            try:
                meta_func = meta_directive_functions[meta_type]
            except KeyError:
                raise ValueError("The type of meta variable %s is not supported (%s)" % (meta_key, meta_type))
            meta_func(newdict, setting, meta_dict[setting])
            # Update meta_dict if there are multiple meta directives.
            meta_dict[setting] = newdict[setting]

        del meta_dict[meta_key]
        del meta_dict[setting]

    newdict.update(deepdict(meta_dict))  # Update everything else.
    return newdict


class HammerDatabase:
    """
    Define a database which is composed of a set of overridable configs.
    We need something like this in order to e.g. bind technology afterwards, since we never want technology to override project.
    If we just did an .update() with the technology config, we'd possibly lose the previously-bound project config.

    Terminology:
    - setting: a single key-value pair e.g. "vlsi.core.technology" -> "footech"
    - config: a single concrete dictionary of settings.
    - database: a collection of configs with a specific override hierarchy.

    Order of precedence (in increasing order):
    - builtins
    - core
    - tools
    - technology
    - environment
    - project
    - runtime (settings dynamically updated during the run a hammer run)
    """

    def __init__(self) -> None:
        self.builtins = []  # type: List[dict]
        self.core = []  # type: List[dict]
        self.tools = []  # type: List[dict]
        self.technology = []  # type: List[dict]
        self.environment = []  # type: List[dict]
        self.project = []  # type: List[dict]
        self._runtime = {}  # type: Dict[str, Any]

        self.__config_cache = {}  # type: dict
        self.__config_cache_dirty = False  # type: bool

    @property
    def runtime(self) -> List[dict]:
        return [self._runtime]

    @staticmethod
    def internal_keys() -> Set[str]:
        """Internal keys that shouldn't show up in any final config."""
        return {CONFIG_PATH_KEY}

    def get_config(self) -> dict:
        """
        Get the config of this database after all the overrides have been dealt with.
        """
        if self.__config_cache_dirty:
            self.__config_cache = combine_configs(
                [{}] + self.builtins + self.core + self.tools + self.technology + self.environment +
                self.project + self.runtime)
            self.__config_cache_dirty = False
        return self.__config_cache

    def get_database_json(self) -> str:
        """Get the database (get_config) in JSON form as a string.
        """
        return json.dumps(self.get_config(), sort_keys=True, indent=4, separators=(',', ': '))

    def get(self, key: str) -> Any:
        """Alias for get_setting()."""
        return self.get_setting(key)

    def __getitem__(self, key: str) -> Any:
        """Alias for get_setting()."""
        return self.get_setting(key)

    def __contains__(self, item: str) -> bool:
        """Alias for has_setting()."""
        return self.has_setting(item)

    def get_setting(self, key: str, nullvalue: str = "null") -> Any:
        """
        Retrieve the given key.

        :param key: Desired key.
        :param nullvalue: Value to return out for nulls.
        :return: The given config
        """
        if key not in self.get_config():
            raise KeyError("Key " + key + " is missing")
        else:
            value = self.get_config()[key]
            return nullvalue if value is None else value

    def set_setting(self, key: str, value: Any) -> None:
        """
        Set the given key. The setting will be placed into the runtime dictionary.

        :param key: Key
        :param value: Value for key
        """
        self._runtime[key] = value
        self.__config_cache_dirty = True

    def has_setting(self, key: str) -> bool:
        """
        Check if the given key exists in the database.

        :param key: Desired key.
        :return: True if the given setting exists.
        """
        return key in self.get_config()

    def update_core(self, core_config: List[dict]) -> None:
        """
        Update the core config with the given core config.
        """
        self.core = core_config
        self.__config_cache_dirty = True

    def update_tools(self, tools_config: List[dict]) -> None:
        """
        Update the tools config with the given tools config.
        """
        self.tools = tools_config
        self.__config_cache_dirty = True

    def update_technology(self, technology_config: List[dict]) -> None:
        """
        Update the technology config with the given technology config.
        """
        self.technology = technology_config
        self.__config_cache_dirty = True

    def update_environment(self, environment_config: List[dict]) -> None:
        """
        Update the environment config with the given environment config.
        """
        self.environment = environment_config
        self.__config_cache_dirty = True

    def update_project(self, project_config: List[dict]) -> None:
        """
        Update the project config with the given project config.
        """
        self.project = project_config
        self.__config_cache_dirty = True

    def update_builtins(self, builtins_config: List[dict]) -> None:
        """
        Update the builtins config with the given builtins config.
        """
        self.builtins = builtins_config
        self.__config_cache_dirty = True


def load_config_from_string(contents: str, is_yaml: bool, path: str = "unspecified") -> dict:
    """
    Load config from a string by loading it and unpacking it.

    :param contents: Contents of the config.
    :param is_yaml: True if the contents are yaml.
    :param path: Path to the folder where the config file is located.
    :return: Loaded config dictionary, unpacked.
    """
    unpacked = unpack(load_yaml(contents) if is_yaml else json.loads(contents))
    unpacked[CONFIG_PATH_KEY] = path
    return unpacked


def load_config_from_file(filename: str, strict: bool = False) -> dict:
    """
    Load config from a filename, returning a blank dictionary if the file is
    empty, instead of an error.
    Supports .yml and .json, and will raise an error otherwise.

    :param filename: Filename to the config in .yml or .json.
    :param strict: Set to true to error if the file is not found.
    :return: Loaded config dictionary, unpacked.
    """
    if filename.endswith(".yml"):
        is_yaml = True
    elif filename.endswith(".json"):
        is_yaml = False
    else:
        raise ValueError("Invalid config type " + filename)

    try:
        with open(filename, "r") as f:
            file_contents = f.read()
    except FileNotFoundError as e:
        if strict:
            raise e
        else:
            # If the config didn't exist, just return a blank dictionary.
            return {}

    if file_contents.strip() == "":
        return {}
    else:
        return load_config_from_string(file_contents, is_yaml, path=os.path.dirname(filename))


def combine_configs(configs: Iterable[dict]) -> dict:
    """
    Combine the given list of *unpacked* configs into a single config.
    Later configs in the list will override the earlier configs.

    :param configs: List of configs.
    :param handle_meta: Handle meta configs?
    :return: A loaded config dictionary.
    """
    expanded_config_reduce = reduce(update_and_expand_meta, configs, {}) # type: dict
    expanded_config = deepdict(expanded_config_reduce) # type: dict
    expanded_config_orig = deepdict(expanded_config) # type: dict

    # Now, we need to handle dynamic* metas.
    dynamic_metas = {}

    meta_dict_keys = list(expanded_config.keys())
    meta_keys = list(filter(lambda k: k.endswith("_meta"), meta_dict_keys))

    meta_len = len("_meta")
    for meta_key in meta_keys:
        setting = meta_key[:-meta_len] # type: str
        meta_type = expanded_config[meta_key] # type: str

        assert meta_type.startswith("dynamic"), "Should have only dynamic metas left now"

        # Create dynamic_metas without the dynamic part.
        # e.g. what used to be a dynamicsubst just becomes a plain subst since everything is fully resolved now.
        dynamic_metas[meta_key] = meta_type[len("dynamic"):]
        dynamic_metas[setting] = expanded_config[setting] # copy over the template too

        # Just check that we don't reference any other dynamicsubst variables for now.
        # We can always go to a DAG tree later if need be.
        if meta_type == "dynamicsubst":
            matches = re.finditer(__VARIABLE_EXPANSION_REGEX, expanded_config[setting], re.DOTALL)
            for match in matches:
                target_var = match.group(1)
                # Ensure that the target variable isn't also a dynamicsubst variable.
                if target_var + "_meta" in expanded_config_orig: # make sure the order in which we delete doesn't affect this search
                    raise ValueError("dynamicsubst variable referencing another dynamic variable not supported yet")

        # Delete from expanded_config
        del expanded_config[meta_key]
        del expanded_config[setting]

    final_dict = update_and_expand_meta(expanded_config, dynamic_metas)

    # Remove the temporary key used for path metas.
    if CONFIG_PATH_KEY in final_dict:
        del final_dict[CONFIG_PATH_KEY]

    return final_dict

def load_config_from_paths(config_paths: Iterable[str], strict: bool = False) -> List[dict]:
    """
    Load configuration from paths containing \*.yml and \*.json files.
    As noted in README.config, .json will take precedence over .yml files.

    :param config_paths: Path to \*.yml and \*.json config files.
    :param strict: Set to true to error if the file is not found.
    :return: A list of configs in increasing order of precedence.
    """
    # Put the .json configs after the .yml configs to make sure .json takes
    # precedence over .yml.
    sorted_paths = sorted(config_paths, key=lambda x: x.endswith(".json"))

    return list(map(lambda path: load_config_from_file(path, strict), sorted_paths))

def load_config_from_defaults(path: str, strict: bool = False) -> List[dict]:
    """
    Load the default configuration for a hammer-vlsi tool/library/technology in
    the given path, which consists of defaults.yml and defaults.json (with
    defaults.json taking priority).

    :param config_paths: Path to defaults.yml and defaults.json.
    :param strict: Set to true to error if the file is not found.
    :return: A list of configs in increasing order of precedence.
    """
    return load_config_from_paths([
        os.path.join(path, "defaults.yml"),
        os.path.join(path, "defaults.json")
    ])
