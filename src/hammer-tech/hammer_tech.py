#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Python interface to the hammer technology abstraction.
#
#  Copyright 2017-2018 Edward Wang <edward.c.wang@compdigitec.com>

from abc import ABCMeta, abstractmethod
import json
import os
import subprocess
from typing import List, NamedTuple, Union

import hammer_config

from hammer_logging import HammerVLSILoggingContext

import python_jsonschema_objects  # type: ignore

builder = python_jsonschema_objects.ObjectBuilder(json.loads(open(os.path.dirname(__file__) + "/schema.json").read()))
ns = builder.build_classes()

# Pull definitions from the autoconstructed classes.
TechJSON = ns.Techjson
# Semiconductor IP library
Library = ns.Library


class LibraryPrefix(metaclass=ABCMeta):
    """
    Base type for all library path prefixes.
    """

    @property
    @abstractmethod
    def prefix(self) -> str:
        """
        Get the prefix that this LibraryPrefix instance provides.
        For example, if this is a path prefix for "myprefix" -> "/usr/share/myprefix", then
        this method returns "myprefix".
        :return: Prefix of this LibraryPrefix.
        """
        pass

    @abstractmethod
    def prepend(self, rest_of_path: str) -> str:
        """
        Prepend the path held by this LibraryPrefix to the given rest_of_path.
        The exact implementation of this depends on the subclass. For example,
        a path prefix may just append the path it holds, while a variable
        prefix might do some lookups.
        :param rest_of_path: Rest of the path
        :return: Path held by this prefix prepended to rest_of_path.
        """
        pass


# Internal backend of PathPrefix. Do not use.
_PathPrefixInternal = NamedTuple('PathPrefix', [
    ('prefix', str),
    ('path', str)
])


class PathPrefix(LibraryPrefix):
    """
    # Struct that holds a path-based prefix.
    """
    __slots__ = ('internal',)

    def __init__(self, prefix: str, path: str) -> None:
        """
        Initialize a new PathPrefix.
        e.g. a PathPrefix might map 'mylib' to '/usr/lib/mylib'.
        :param prefix: Prefix to hold e.g. 'mylib'
        :param path: Path to map this prefix to - e.g. '/usr/lib/mylib'.
        """
        self.internal = _PathPrefixInternal(
            prefix=str(prefix),
            path=str(path)
        )

    def __eq__(self, other) -> bool:
        return self.internal == other.internal

    @property
    def prefix(self) -> str:
        return self.internal.prefix

    @property
    def path(self) -> str:
        return self.internal.path

    def to_setting(self) -> dict:
        return {
            "prefix": self.prefix,
            "path": self.path
        }

    @staticmethod
    def from_setting(d: dict) -> "PathPrefix":
        return PathPrefix(
            prefix=str(d["prefix"]),
            path=str(d["path"])
        )

    def prepend(self, rest_of_path: str) -> str:
        return os.path.join(self.path, rest_of_path)


# TODO(edwardw): deprecate these functions once Library is no longer auto-generated.
def copy_library(lib: Library) -> Library:
    """Perform a deep copy of a Library."""
    return Library.from_json(lib.serialize())


def library_from_json(json: str) -> Library:
    """
    Creatre a library from a JSON string.
    :param json: JSON string.
    :return: hammer_tech library.
    """
    return Library.from_json(json)


class HammerTechnology:
    # Properties.
    @property
    def cache_dir(self) -> str:
        """
        Get the location of a cache dir for this library.

        :return: Path to the location of the cache dir.
        """
        try:
            return self._cachedir
        except AttributeError:
            raise ValueError("Internal error: cache dir location not set by hammer-vlsi")

    @cache_dir.setter
    def cache_dir(self, value: str) -> None:
        """Set the directory as a persistent cache dir for this library."""
        self._cachedir = value  # type: str
        # Ensure the cache_dir exists.
        os.makedirs(value, exist_ok=True)

    # hammer-vlsi properties.
    # TODO: deduplicate/put these into an interface to share with HammerTool?
    @property
    def logger(self) -> HammerVLSILoggingContext:
        """Get the logger for this tool."""
        try:
            return self._logger
        except AttributeError:
            raise ValueError("Internal error: logger not set by hammer-vlsi")

    @logger.setter
    def logger(self, value: HammerVLSILoggingContext) -> None:
        """Set the logger for this tool."""
        self._logger = value  # type: HammerVLSILoggingContext

    # Methods.
    def __init__(self):
        """Don't call this directly. Use other constructors like load_from_dir()."""
        # Name of the technology
        self.name = ""  # type: str

        # Path to the technology folder
        self.path = ""  # type: str

        # Configuration
        self.config = None  # type: TechJSON

    @classmethod
    def load_from_dir(cls, technology_name: str, path: str) -> "HammerTechnology":
        """Load a technology from a given folder.

        :param technology_name: Technology name (e.g. "saed32")
        :param path: Path to the technology folder (e.g. foo/bar/technology/saed32)
        """

        with open(os.path.join(path, "{technology_name}.tech.json".format(technology_name=technology_name))) as f:
            json_str = f.read()

        return HammerTechnology.load_from_json(technology_name, json_str, path)

    @classmethod
    def load_from_json(cls, technology_name: str, json_str: str, path: str) -> "HammerTechnology":
        """Load a technology from a given folder.

        :param technology_name: Technology name (e.g. "saed32")
        :param json_str: JSON string to use as the technology JSON
        :param path: Path to set as the technology folder (e.g. foo/bar/technology/saed32)
        """

        tech = HammerTechnology()

        # Name of the technology
        tech.name = technology_name

        # Path to the technology folder
        tech.path = path

        # Configuration
        tech.config = TechJSON.from_json(json_str)

        return tech

    def set_database(self, database: hammer_config.HammerDatabase) -> None:
        """Set the settings database for use by the tool."""
        self._database = database  # type: hammer_config.HammerDatabase

    def get_setting(self, key: str):
        """Get a particular setting from the database.
        """
        try:
            return self._database.get(key)
        except AttributeError:
            raise ValueError("Internal error: no database set by hammer-vlsi")

    def get_config(self) -> List[dict]:
        """Get the hammer configuration for this technology. Not to be confused with the ".tech.json" which self.config refers to."""
        return hammer_config.load_config_from_defaults(self.path)

    @property
    def extracted_tarballs_dir(self) -> str:
        """Return the path to a folder under self.path where extracted tarballs are stored/cached."""
        return os.path.join(self.cache_dir, "extracted")

    @staticmethod
    def parse_library(lib: dict) -> Library:
        """
        Parse a given lib in dictionary form to a hammer_tech Library (IP library).
        :param lib: Library to parse, must be a dictionary
        :return: Parsed hammer_tech Library or exception.
        """
        if not isinstance(lib, dict):
            raise TypeError("lib must be a dict")

        # Convert the dict to JSON...
        return Library.from_json(json.dumps(lib))

    # TODO(edwardw): think about moving more of these kinds of functions out of the synthesis tool and in here instead.
    def prepend_dir_path(self, path: str) -> str:
        """
        Prepend the appropriate path (either from tarballs or installs) to the given library item.
        """
        assert len(path) > 0, "path must not be empty"

        # If the path is an absolute path, return it as-is.
        if path[0] == "/":
            return path

        base_path = path.split(os.path.sep)[0]
        rest_of_path = path.split(os.path.sep)[1:]

        if self.config.installs is not None:
            matching_installs = list(filter(lambda install: install.path == base_path, self.config.installs))
        else:
            matching_installs = []
        if self.config.tarballs is not None:
            matching_tarballs = list(filter(lambda tarball: tarball.path == base_path, self.config.tarballs))
        else:
            matching_tarballs = []

        matches = len(matching_installs) + len(matching_tarballs)
        if matches < 1:
            raise ValueError("Path {0} did not match any tarballs or installs".format(path))
        elif matches > 1:
            raise ValueError("Path {0} matched more than one tarball or install".format(path))
        else:
            if len(matching_installs) == 1:
                install = matching_installs[0]
                if install.base_var == "":
                    base = self.path
                else:
                    base = self.get_setting(install.base_var)
                return os.path.join(*([base] + rest_of_path))
            else:
                return os.path.join(self.extracted_tarballs_dir, path)

    def extract_technology_files(self) -> None:
        """Ensure that the technology files exist either via tarballs or installs."""
        if self.config.installs is not None:
            self.check_installs()
            return
        if self.config.tarballs is not None:
            self.extract_tarballs()
            return
        self.logger.error("Technology specified neither tarballs or installs")

    def check_installs(self) -> bool:
        """Check that the all directories for a pre-installed technology actually exist.

        :return: Return True if the directories is OK, False otherwise."""
        for install in self.config.installs:
            base_var = str(install.base_var)

            if len(base_var) == 0:
                # Blank install_path is okay to reference the current technology directory.
                pass
            else:
                install_path = str(self.get_setting(base_var))
                if not os.path.exists(install_path):
                    self.logger.error("installs {path} does not exist".format(path=install_path))
                    return False
        return True

    def extract_tarballs(self) -> None:
        """Extract tarballs to the given cache_dir, or verify that they've been extracted."""
        for tarball in self.config.tarballs:
            target_path = os.path.join(self.extracted_tarballs_dir, tarball.path)
            tarball_path = os.path.join(self.get_setting(tarball.base_var), tarball.path)
            self.logger.debug("Extracting/verifying tarball %s" % (tarball_path))
            if os.path.isdir(target_path):
                # If the folder already seems to exist, continue
                continue
            else:
                # Else, extract the tarballs.
                os.makedirs(target_path, exist_ok=True)  # Make sure it exists or tar will not be happy.
                subprocess.check_call("tar -xf %s -C %s" % (tarball_path, target_path), shell=True)
                subprocess.check_call("chmod u+rwX -R %s" % (target_path), shell=True)
