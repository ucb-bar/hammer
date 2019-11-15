#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Test placement constraints in Hammer IR.
#
#  See LICENSE for licence details.

import json
import os
import sys

# TODO(edwardw): separate hammer_ir out of hammer_vlsi
from hammer_vlsi import PlacementConstraint, PlacementConstraintType

# TODO(edwardw): move these to a separate file/library
prepped = False  # type: bool
def prep() -> None:
    assert os.system("./prep.sh") == 0
    global prepped
    prepped = True

def run_scala(scala: str) -> None:
    assert prepped, "Must prep before running test functions"

    with open("tmp_script.scala", "w") as f:
        f.write(scala)

    if os.system("./amm tmp_script.scala") != 0:
        print("Scala script below failed: \n{}".format(scala), file=sys.stderr)
        sys.exit(1)

prep()

# Generate some constraints
c1 = PlacementConstraint(
    path="Top/rtl/a/b",
    type=PlacementConstraintType.Placement,
    x=15.123,
    y=14.567,
    width=42.900,
    height=888.100,
    orientation=None,
    margins=None,
    top_layer=None,
    layers=None,
    obs_types=None
)

# TODO(edwardw): the optional parameters are only valid for certain
# types of constraints.
# e.g. orientation is only valid for hardmacros
# e.g. obs_types is only valid for obstructions
# We need to create some extra testcases to capture those usecases.

# Export to JSON
with open("tmp_c1.json", "w") as f:
    f.write(json.dumps(c1.to_dict()))

# Check that it's still usable in Scala-land
run_scala("""
import hammer_ir._

// Read and write back
val p = PlacementConstraint.fromFile("tmp_c1.json")

assert(p.path == "Top/rtl/a/b")
assert(p.`type` == PlacementConstraintType.Placement)
assert(p.x == 15.123)
assert(p.y == 14.567)
assert(p.width == 42.900)
assert(p.height == 888.100)

p.toFile("tmp_c1-out.json")
""")

# Check that it's still the same
with open("tmp_c1-out.json", "r") as f:
    c1_out = PlacementConstraint.from_dict(json.loads(f.read()))

print(c1_out)
assert c1 == c1_out
