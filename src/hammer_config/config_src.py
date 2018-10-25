#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Copyright 2017-2018 Edward Wang <edward.c.wang@compdigitec.com>
#
#  Build the configuration database from a series of JSON config files.
#  Dumps the output in JSON format to standard output.
#  See README.config for more details.

# pylint: disable=invalid-name

from typing import Iterable, List, Union, Callable, Any, Dict, Set, NamedTuple

from hammer_utils import deepdict
from .yaml2json import load_yaml  # grumble grumble

from functools import reduce, lru_cache
import json
import numbers
import os
import re

# Special key used for meta directives which require config paths like prependlocal.
_CONFIG_PATH_KEY = "_config_path"


# Miscellaneous parameters involved in executing a meta directive.
class MetaDirectiveParams(NamedTuple('MetaDirectiveParams', [
    # Path of the config that contained the meta directive.
    # Used mainly for prependlocal.
    ('meta_path', str)
])):
    __slots__ = ()


# Represents a meta directive in the Hammer configuration system.
class MetaDirective(NamedTuple('MetaDirective', [
    # Action which executes/implements this meta directive.
    # config_dict is the base dictionary
    # key is the key of the meta directive
    # value is the value of that key
    # params contains miscellaneous parameters required to execute meta directives.
    # def action(config_dict: dict, key: str, value: Any, params: MetaDirectiveParams) -> None:
    #     ...
    ('action', Callable[[dict, str, Any, MetaDirectiveParams], None]),
    # Function which takes in the key and value for a meta directive and
    # returns a list of settings it depends on.
    # e.g. for subst, a value of "${a}${b}" would return
    # ['a', 'b'].
    # def target_settings(key: str, value: Any) -> List[str]:
    #     ...
    ('target_settings', Callable[[str, Any], List[str]])
])):
    __slots__ = ()


@lru_cache(maxsize=2)
def get_meta_directives() -> Dict[str, MetaDirective]:
    """
    Get all meta directives available.
    :return: Meta directives indexed by action (e.g. "subst").
    """
    directives = {}  # type: Dict[str, MetaDirective]

    # Helper functions to implement each meta directive.
    def meta_append(config_dict: dict, key: str, value: Any, params: MetaDirectiveParams) -> None:
        if key not in config_dict:
            config_dict[key] = []

        if not isinstance(config_dict[key], list):
            raise ValueError("Trying to append to non-list setting %s" % (key))
        if not isinstance(value, list):
            raise ValueError("Trying to append to list %s with non-list %s" % (key, str(value)))
        config_dict[key] += value

    # append depends only on itself
    directives['append'] = MetaDirective(action=meta_append,
                                         target_settings=lambda key, value: [key])

    def meta_subst(config_dict: dict, key: str, value: Any, params: MetaDirectiveParams) -> None:
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

        config_dict[key] = perform_subst(value)

    def subst_targets(key: str, value: Any) -> List[str]:
        assert isinstance(value, str)

        output_vars = []  # type: List[str]

        matches = re.finditer(__VARIABLE_EXPANSION_REGEX, value, re.DOTALL)
        for match in matches:
            output_vars.append(match.group(1))

        return output_vars

    directives['subst'] = MetaDirective(action=meta_subst,
                                        target_settings=subst_targets)

    def crossref_check_and_cast(k: Any) -> str:
        if not isinstance(k, str):
            raise ValueError("crossref (if used with lists) can only be used only with lists of strings")
        else:
            return k

    def meta_crossref(config_dict: dict, key: str, value: Any, params: MetaDirectiveParams) -> None:
        """
        Copy the contents of the referenced key for use as this key's value.
        If the reference is a list, then apply the crossref for each element
        of the list.
        """
        if type(value) == str:
            config_dict[key] = config_dict[value]
        elif type(value) == list:
            def check_and_get(k: Any) -> Any:
                return config_dict[crossref_check_and_cast(k)]

            config_dict[key] = list(map(check_and_get, value))
        elif isinstance(value, numbers.Number):
            # bools are instances of numbers.Number for some weird reason
            raise ValueError("crossref cannot be used with numbers and bools")
        else:
            raise NotImplementedError("crossref not implemented on other types yet")

    def crossref_targets(key: str, value: Any) -> List[str]:
        if type(value) == str:
            return [value]
        elif type(value) == list:
            return list(map(crossref_check_and_cast, value))
        elif isinstance(value, numbers.Number):
            # bools are instances of numbers.Number for some weird reason
            raise ValueError("crossref cannot be used with numbers and bools")
        else:
            raise NotImplementedError("crossref not implemented on other types yet")

    directives['crossref'] = MetaDirective(action=meta_crossref,
                                           target_settings=crossref_targets)

    def meta_transclude(config_dict: dict, key: str, value: Any, params: MetaDirectiveParams) -> None:
        """Transclude the contents of the file pointed to by value."""
        assert isinstance(value, str), "Path to file for transclusion must be a string"
        with open(value, "r") as f:
            file_contents = str(f.read())
        config_dict[key] = file_contents

    # transclude depends on external files, not other settings.
    directives['transclude'] = MetaDirective(action=meta_transclude,
                                             target_settings=lambda key, value: [])

    def meta_json2list(config_dict: dict, key: str, value: Any, params: MetaDirectiveParams) -> None:
        """Turn the value of the key (JSON list) into a list."""
        assert isinstance(value, str), "json2list requires a JSON string that is a list"
        parsed = json.loads(value)
        assert isinstance(parsed, list), "json2list requires a JSON string that is a list"
        config_dict[key] = parsed

    # json2list does not depend on anything
    directives['json2list'] = MetaDirective(action=meta_json2list,
                                            target_settings=lambda key, value: [])

    def meta_prependlocal(config_dict: dict, key: str, value, params: MetaDirectiveParams) -> None:
        """Prepend the local path of the config dict."""
        config_dict[key] = os.path.join(params.meta_path, str(value))

    # prependlocal does not depend on anything in config_dict.
    directives['prependlocal'] = MetaDirective(action=meta_prependlocal,
                                               target_settings=lambda key, value: [])

    return directives


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
    assert isinstance(config_dict, dict)
    assert isinstance(meta_dict, dict)

    newdict = deepdict(config_dict)

    # Find meta directives.
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
        seen_dynamic = False  # type: bool
        for meta_type in meta_directives:
            if not isinstance(meta_type, str):
                raise TypeError("meta_type was not a string: " + repr(meta_type))

            # If it's a dynamic meta, skip it for now since they are lazily
            # processed at the very end.
            if meta_type.startswith("dynamic"):
                if meta_type[len("dynamic"):] not in get_meta_directives():
                    raise ValueError("The type of dynamic meta variable %s is not supported (%s)" % (meta_key, meta_type))

                if seen_dynamic:
                    raise ValueError("Multiple dynamic directives in a single directive array not supported yet")
                else:
                    seen_dynamic = True

                # Store it into newdict and skip processing now.
                newdict[setting] = meta_dict[setting]
                newdict[setting + "_meta"] = meta_type
                continue
            else:
                if seen_dynamic:
                    raise ValueError("Cannot use a non-dynamic meta directive after a dynamic one")

            try:
                meta_func = get_meta_directives()[meta_type].action
            except KeyError:
                raise ValueError("The type of meta variable %s is not supported (%s)" % (meta_key, meta_type))
            meta_func(newdict, setting, meta_dict[setting],
                      MetaDirectiveParams(meta_path=meta_dict.get(_CONFIG_PATH_KEY, "unspecified")))
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
        return {_CONFIG_PATH_KEY}

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

    def get_setting(self, key: str, nullvalue: Any = "null") -> Any:
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
    unpacked[_CONFIG_PATH_KEY] = path
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
        setting = meta_key[:-meta_len]  # type: str
        dynamic_meta_type = expanded_config[meta_key]  # type: str

        assert dynamic_meta_type.startswith("dynamic"), "Should have only dynamic metas left now"

        # Create dynamic_metas without the dynamic part.
        # e.g. what used to be a dynamicsubst just becomes a plain subst since everything is fully resolved now.
        meta_type = dynamic_meta_type[len("dynamic"):]
        dynamic_metas[meta_key] = meta_type
        dynamic_metas[setting] = expanded_config[setting]  # copy over the template too

        # Just check that we don't reference any other dynamic settings for now.
        # We can always go to a DAG tree later if need be.
        for target_var in get_meta_directives()[meta_type].target_settings(setting, expanded_config[setting]):
            if target_var + "_meta" in expanded_config_orig:  # make sure the order in which we delete doesn't affect this search
                raise ValueError("dynamic setting referencing another dynamic setting not supported yet")

        # Delete from expanded_config
        del expanded_config[meta_key]
        del expanded_config[setting]

    final_dict = update_and_expand_meta(expanded_config, dynamic_metas)

    # Remove any temporary keys.
    for key in HammerDatabase.internal_keys():
        if key in final_dict:
            del final_dict[key]

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
