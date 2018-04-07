#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  Python interface to the hammer technology abstraction.
#
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

import json
import os
import subprocess
from typing import List

import hammer_config

from hammer_vlsi import HammerVLSILoggingContext

import python_jsonschema_objects # type: ignore

builder = python_jsonschema_objects.ObjectBuilder(json.loads(open(os.path.dirname(__file__) + "/schema.json").read()))
ns = builder.build_classes()

# Pull definitions from the autoconstructed classes.
TechJSON = ns.Techjson
Library = ns.Library

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
        self._cachedir = value # type: str
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
        self._logger = value # type: HammerVLSILoggingContext

    # Methods.
    def __init__(self):
        """Don't call this directly. Use other constructors like load_from_dir()."""
        # Name of the technology
        self.name = "" # type: str

        # Path to the technology folder
        self.path = "" # type: str

        # Configuration
        self.config = None # type: TechJSON

    @classmethod
    def load_from_dir(cls, technology_name: str, path: str):
        """Load a technology from a given folder.

        :param technology_name: Technology name (e.g. "saed32")
        :param path: Path to the technology folder (e.g. foo/bar/technology/saed32)
        """

        tech = HammerTechnology()

        # Name of the technology
        tech.name = technology_name

        # Path to the technology folder
        tech.path = path

        # Configuration
        with open(os.path.join(path, "%s.tech.json" % (tech.name))) as f:
            tech.config = TechJSON.from_json(f.read())

        return tech

    def set_database(self, database: hammer_config.HammerDatabase) -> None:
        """Set the settings database for use by the tool."""
        self._database = database # type: hammer_config.HammerDatabase

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
            install_path = str(self.get_setting(install.base_var))
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
                os.makedirs(target_path, exist_ok=True) # Make sure it exists or tar will not be happy.
                subprocess.check_call("tar -xf %s -C %s" % (tarball_path, target_path), shell=True)
                subprocess.check_call("chmod u+rwX -R %s" % (target_path), shell=True)
