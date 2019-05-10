// See LICENSE for licence details.

import $cp.`hammer_ir.jar`

import hammer_ir._

// Read and write back
val p = PlacementConstraint.fromFile("c1.json")

p.`type` match {
  case PlacementConstraintType.Placement => println("Am placement")
  case _ => println("Am not placement")
}

p.toFile("c1-out.json")
