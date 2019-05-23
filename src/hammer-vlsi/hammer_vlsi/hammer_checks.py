#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  hammer_vlsi_impl.py
#  hammer-vlsi implementation file. Users should import hammer_vlsi instead.
#
#  See LICENSE for licence details.

from decimal import Decimal
from hammer_utils import check_on_grid, lcm_grid
from hammer_tech import RoutingDirection
from .constraints import *
from .hammer_tool import HammerTool

class HammerChecks(HammerTool):

    def run_all(self) -> bool:
        return self.floorplan_checks()

    def floorplan_checks(self) -> bool:

        floorplan_constraints = self.get_placement_constraints()

        ############## Rule-check the constraints before generation ################
        fp_checks_pass = True
        site = self.technology.get_placement_site()
        for constraint in floorplan_constraints:
            # Enumerate all possible constraint types here
            if constraint.type == PlacementConstraintType.TopLevel:
                # Rule FP.TOP.X: Width of top-level must be an integer multiple of the site x dimension
                if not check_on_grid(constraint.width, site.x):
                    suggest_l = Decimal(int(Decimal(constraint.height) / site.x)) * site.x
                    suggest_h = suggest_l + site.y
                    self.logger.error("Floorplanning rule FP.TOP.X: Width of top-level must be an integer multiple of the site x dimension: {x}. Try {suggest_l} or {suggest_h}.".format(
                        mod=constraint.path, x=site.x, suggest_l=suggest_l, suggest_h = suggest_h))
                    fp_checks_pass = False
                # Rule FP.TOP.Y: Height of top-level must be an integer multiple of the site y dimension
                if not check_on_grid(constraint.height, site.y):
                    suggest_l = Decimal(int(Decimal(constraint.width) / site.y)) * site.y
                    suggest_h = suggest_l + site.y
                    self.logger.error("Floorplanning rule FP.TOP.Y: Height of top-level must be an integer multiple of the site y dimension: {y}. Try {suggest_l} or {suggest_h}.".format(
                        mod=constraint.path, y=site.y, suggest_l=suggest_l, suggest_h = suggest_h))
                    fp_checks_pass = False
            elif constraint.type == PlacementConstraintType.Dummy:
                pass
            elif constraint.type == PlacementConstraintType.Placement:
                pass
            elif constraint.type == PlacementConstraintType.HardMacro:
                pass
            elif constraint.type == PlacementConstraintType.Hierarchical:
                # TODO some of these might need to be checking HierarchicalMode instead of constraint type
                # Rule FP.HIER.WIDTH: Width of hierarchical module must be an integer multiple of the site x dimension
                if not check_on_grid(constraint.width, site.x):
                    suggest_l = Decimal(int(Decimal(constraint.height) / site.x)) * site.x
                    suggest_h = suggest_l + site.y
                    self.logger.error("Floorplanning rule FP.HIER.WIDTH: Width of hierarchical module {mod} must be an integer multiple of the site x dimension: {x}. Try {suggest_l} or {suggest_h}.".format(
                        mod=constraint.path, y=site.y, suggest_l=suggest_l, suggest_h = suggest_h))
                    fp_checks_pass = False
                # Rule FP.HIER.HEIGHT: Height of hierarchical module must be an integer multiple of the site y dimension
                if not check_on_grid(constraint.height, site.y):
                    suggest_l = Decimal(int(Decimal(constraint.width) / site.y)) * site.y
                    suggest_h = suggest_l + site.y
                    self.logger.error("Floorplanning rule FP.HIER.HEIGHT: Height of hierarchical module {mod} must be an integer multiple of the site y dimension: {y}. Try {sugggest_l} or {suggest_h}.".format(
                        mod=constraint.path, y=site.y, suggest_l=suggest_l, suggest_h = suggest_h))
                    fp_checks_pass = False
                # Rule FP.HIER.PLACEMENT.X: Origin X of hierarchical module must be on the site grid
                if not check_on_grid(constraint.x, site.x):
                    suggest_l = Decimal(int(Decimal(constraint.x) / site.x)) * site.x
                    suggest_h = suggest_l + site.x
                    self.logger.error("Floorplanning rule FP.HIER.PLACEMENT.X: Origin X of hierarchical module {mod} must be on the site grid: {x}. Try {suggest_l} or {suggest_h}.".format(
                        mod=constraint.path, x=site.x, suggest_l=suggest_l, suggest_h=suggest_h))
                    fp_checks_pass = False
                # Rule FP.HIER.PLACEMENT.Y: Origin Y of hierarchical module must be on the site grid
                if not check_on_grid(constraint.y, site.y):
                    suggest_l = Decimal(int(Decimal(constraint.y) / site.y)) * site.y
                    suggest_h = suggest_l + site.y
                    self.logger.error("Floorplanning rule FP.HIER.PLACEMENT.Y: Origin Y of hierarchical module {mod} must be on the site grid: {y}. Try {suggest_l} or {suggest_h}.".format(
                        mod=constraint.path, y=site.y, suggest_l=suggest_l, suggest_h=suggest_h))
                    fp_checks_pass = False
                # Rule FP.HIER.PLACEMENT.???: Routing track offsets of pin layers must line up with parent
                # TODO(johnwright) (in a future PR)
                # Rule FP.HIER.POWER.PINS: Hierarchical cells must have power strap pins enabled
                # TODO(johnwright) (in a future PR)
                # Determine if this is a singly- or multiply-instantiated module
                # TODO(johnwright) This rule can be relaxed for multiply-instantiated modules that are not tiled, but we need other checks for those (e.g. all offsets must be the same)
                num_occurrences = 2 # TODO how to get this?
                if num_occurrences > 1:
                    # Rule FP.TILE.WIDTH: Width of tiled hierarchical module must be an integer multiple of the LCM of:
                    #   - site x dimension
                    #   - all vertical routing pitches of pin layers
                    #   - all vertical power strap group pitches of layers intended to abut at the top level (for now assume pin layers) (TODO when this is more useful)
                    #   - the bump pitch (only if bumps are directly connected to the tiled cell) TODO add a property for this, not currently implemented
                    # TODO(johnwright) when hier power straps exist, use the hier power straps pins (throw a warning if hier power straps pins is different than regular pins)
                    grid_unit_x = lcm_grid(self.technology.get_grid_unit(),
                        site.x,
                        *map(lambda x: x.pitch, filter(lambda x: x.direction == RoutingDirection.Vertical, self.get_pin_metals())))
                        #*map(self.get_by_tracks_drawn_pitch, filter(lambda x: x.direction == RoutingDirection.Vertical, self.get_pin_metals())))
                    if not check_on_grid(constraint.width, grid_unit_x):
                        suggest_l = Decimal(int(Decimal(constraint.width) / grid_unit_x)) * grid_unit_x
                        suggest_h = suggest_l + grid_unit_x
                        self.logger.error("Floorplanning rule FP.TILE.WIDTH: Width of tiled hierarchical module {mod} must be an integer multiple of {x} (computed). Try {suggest_l} or {suggest_h}.".format(
                            mod=constraint.path, x=grid_unit_x, suggest_l=suggest_l, suggest_h=suggest_h))
                        fp_checks_pass = False
                    # Rule FP.TILE.HEIGHT: Height of tiled hierarchical module must be an integer multiple of the LCM of:
                    #   - site y dimension
                    #   - all horizontal routing pitches of pin layers
                    #   - all horizontal power strap group pitches of layers intended to abut at the top level (for now assume pin layers) (TODO when this is more useful)
                    #   - the bump pitch (only if bumps are directly connected to the tiled cell) TODO add a property for this, not currently implemented
                    # TODO(johnwright) when hier power straps exist, use the hier power straps pins (throw a warning if hier power straps pins is different than regular pins)
                    grid_unit_y = lcm_grid(self.technology.get_grid_unit(),
                        site.y,
                        *map(lambda x: x.pitch, filter(lambda x: x.direction == RoutingDirection.Horizontal, self.get_pin_metals())))
                        #*map(self.get_by_tracks_drawn_pitch, filter(lambda x: x.direction == RoutingDirection.Horizontal, self.get_pin_metals())))
                    if not check_on_grid(constraint.height, grid_unit_y):
                        suggest_l = Decimal(int(Decimal(constraint.height) / grid_unit_y)) * grid_unit_y
                        suggest_h = suggest_l + grid_unit_y
                        self.logger.error("Floorplanning rule FP.TILE.HEIGHT: Height of tiled hierarchical module {mod} must be an integer multiple of {y} (computed). Try {suggest_l} or {suggest_h}.".format(
                            mod=constraint.path, y=grid_unit_y, suggest_l=suggest_l, suggest_h=suggest_h))
                        fp_checks_pass = False
                    # Rule FP.TILE.PLACEMENT.X: Width of tiled hierarchical module must be an integer multiple of the LCM of:
                    #   - site x dimension
                    #   - all vertical routing pitches of pin layers
                    #   - all vertical power strap group pitches of layers intended to abut at the top level (for now assume pin layers) (TODO when this is more useful)
                    #   - the bump pitch (only if bumps are directly connected to the tiled cell) TODO add a property for this, not currently implemented
                    # TODO(johnwright) when hier power straps exist, use the hier power straps pins (throw a warning if hier power straps pins is different than regular pins)
                    grid_unit_x = lcm_grid(self.technology.get_grid_unit(),
                        site.x,
                        *map(lambda x: x.pitch, filter(lambda x: x.direction == RoutingDirection.Vertical, self.get_pin_metals())))
                        #*map(self.get_by_tracks_drawn_pitch, filter(lambda x: x.direction == RoutingDirection.Vertical, self.get_pin_metals())))
                    if not check_on_grid(constraint.x, grid_unit_x):
                        suggest_l = Decimal(int(Decimal(constraint.x) / grid_unit_x)) * grid_unit_x
                        suggest_h = suggest_l + grid_unit_x
                        self.logger.error("Floorplanning rule FP.TILE.PLACEMENT.X: Origin X of tiled hierarchical module {mod} must be an integer multiple of {x} (computed). Try {suggest_l} or {suggest_h}.".format(
                            mod=constraint.path, x=grid_unit_x, suggest_l=suggest_l, suggest_h=suggest_h))
                        fp_checks_pass = False
                    # Rule FP.TILE.PLACEMENT.Y: Height of tiled hierarchical module must be an integer multiple of the LCM of:
                    #   - site y dimension
                    #   - all horizontal routing pitches of pin layers
                    #   - all horizontal power strap group pitches of layers intended to abut at the top level (for now assume pin layers) (TODO when this is more useful)
                    #   - the bump pitch (only if bumps are directly connected to the tiled cell) TODO add a property for this, not currently implemented
                    # TODO(johnwright) when hier power straps exist, use the hier power straps pins (throw a warning if hier power straps pins is different than regular pins)
                    grid_unit_y = lcm_grid(self.technology.get_grid_unit(),
                        site.y,
                        *map(lambda x: x.pitch, filter(lambda x: x.direction == RoutingDirection.Horizontal, self.get_pin_metals())))
                        #*map(self.get_by_tracks_drawn_pitch, filter(lambda x: x.direction == RoutingDirection.Horizontal, self.get_pin_metals())))
                    if not check_on_grid(constraint.y, grid_unit_y):
                        suggest_l = Decimal(int(Decimal(constraint.y) / grid_unit_y)) * grid_unit_y
                        suggest_h = suggest_l + grid_unit_y
                        self.logger.error("Floorplanning rule FP.TILE.PLACEMENT.Y: Origin Y of tiled hierarchical module {mod} must be an integer multiple of {y} (computed). Try {suggest_l} or {suggest_h}.".format(
                            mod=constraint.path, y=grid_unit_y, suggest_l=suggest_l, suggest_h=suggest_h))
                        fp_checks_pass = False
            elif constraint.type == PlacementConstraintType.Obstruction:
                pass
            else:
                assert False, "Invalid constraint type: {}. Perhaps you added a new one and forgot to update the rules above?".format(constraint.type)

        return fp_checks_pass

