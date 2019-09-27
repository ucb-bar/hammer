#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  design.py
#  A block that is pushed through the flow. it can be the full-chip, a 
#  hierarchical partition, or a leaf pnr-block.
#
#  See LICENSE for licence details.

import os.path
import shutil

from hammer_config import HammerDatabase

__all__ = ['HammerDesign']

class HammerDesign():

    def __init__(self, name:str, db:HammerDatabase, 
            tech:HammerTechnology) -> None:
        """
        db/tech are PRIVATE instances to this design. so no other design
        will see any modifications to db/tech made by this design
        """
        self.name = name
        self.children = []
        self.parents = []
        self.db = db
        self.db.set_setting("vlsi.dynamic.top_module", self.name)
        self.tech = tech
        self.tools = {}

    def clone(self) -> HammerDesign:
        """ deep clones the design. only needed when cloning for a tool"""
        db = self.db.clone()
        tech = self.tech.clone(db=db)
        return HammerDesign(self.name, db=db, tech=tech)

    def is_top(self):
        return len(self.parents) == 0

    def is_leaf(self):
        return len(self.children) == 0

    def set_tool(self, tool:HammerTool) -> None:
        if self.tools[tool.stage] is not None:
            raise Exception("{} already added tool for stage {}"
                .format(self.name, tool.stage))

    def get_tool(self, stage:str) -> HammerTool:
        if self.tools[stage] is None:
            raise Exception("{} has no tool for stage {}"
                .format(self.name, stage))
        return self.tools[stage]

    #-------------------------------------------------------------------------
    # routines for dealing with children/parents
    #-------------------------------------------------------------------------

    def get_parents(self) -> List[HammerDesign]:
        return self.parents

    def has_parent(self, design: HammerDesign) -> bool:
        return len(filter(lambda x: x.name == design.name, self.parents)) > 0

    def has_deep_parent(self, design: HammerDesign) -> bool:
        for p in self.parents:
            if p.name == design.name or p.has_deep_parent(design):
                return True
        return False

    def get_children(self) -> List[HammerDesign]:
        return self.children

    def has_child(self, design: HammerDesign) -> bool:
        return len(filter(lambda x: x.name == design.name, self.children)) > 0

    def has_deep_child(self, design: HammerDesign) -> bool:
        for c in self.children:
            if c.name == design.name or c.has_deep_children(design):
                return True
        return False

    def add_child(self, child: HammerDesign) -> None:
        """
        1) It is ok for a child to exist a multiple levels of hierarchy below
           this module. that just means that block is instantiated in multiple 
           locations.
        2) A block that is a parent and a child will cause an infinitie loop
        3) a block can't be a direct child more than once. 
        """
        if self.has_child(child):
            raise Excpetion("child {} is already a direct child of {}".format(
                child.name, self.name)
        if self.has_deep_parent(child):
            raise Excpetion("child {} is already a deep parent of {}".format(
                child.name, self.name)
        self.children.append(child)
        child._add_parent(self)

    def _add_parent(self, parent: HammerDesign) -> None:
        """
        NOTE: this is called automatically by add_child

        1) It is ok for a parent to exist a multiple levels of hierarchy above
           this module. that just means this block is instantiated in multiple 
           locations.
        2) A block that is a parent and a child will cause an infinitie loop
        3) a block can't be a direct parent more than once. 
        """
        if self.has_deep_child(parent):
            raise Excpetion("parent {} is already a deep child of {}".format(
                parent.name, self.name)
        if self.has_parent(parent):
            raise Excpetion("parent {} is already a direct parent of {}".format(
                parent.name, self.name)
        self.parents.append(parent)

