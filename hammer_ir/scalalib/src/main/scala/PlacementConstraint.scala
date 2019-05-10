// See LICENSE for licence details.

package hammer_ir

import play.api.libs.json.{JsNumber, JsObject, JsString}

sealed abstract class PlacementConstraintType extends JSONConvertible {
  override def toJSON = JsString(stringVal)
  // Force objects to implement this since toString is defined by
  // default.
  def stringVal: String
  override def toString = stringVal
}
object PlacementConstraintType {
  def fromString(input: String): PlacementConstraintType = {
    values.foreach { i =>
      if (i.stringVal == input) return i
    }
    throw new IllegalArgumentException(s"Illegal PlacementConstraintType $input")
  }

  case object Dummy extends PlacementConstraintType {
    override def stringVal = "dummy"
  }
  case object Placement extends PlacementConstraintType {
    override def stringVal = "placement"
  }
  case object TopLevel extends PlacementConstraintType {
    override def stringVal = "toplevel"
  }
  case object HardMacro extends PlacementConstraintType {
    override def stringVal = "hardmacro"
  }
  case object Hierarchical extends PlacementConstraintType {
    override def stringVal = "hierarchical"
  }
  case object Obstruction extends PlacementConstraintType {
    override def stringVal = "obstruction"
  }

  def values = Seq(
    Dummy, Placement, TopLevel, HardMacro, Hierarchical, Obstruction
  )
}

sealed abstract class ObstructionType
object ObstructionType {
  case object Place extends ObstructionType
  case object Route extends ObstructionType
  case object Power extends ObstructionType
}

case class Margins(
  left: Double,
  bottom: Double,
  right: Double,
  top: Double
)

case class PlacementConstraint(
  path: String,
  `type`: PlacementConstraintType,
  x: Double,
  y: Double,
  width: Double,
  height: Double,
  orientation: Option[String],
  margins: Option[Margins],
  top_layer: Option[String],
  layers: Option[Seq[String]],
  obs_types: Option[Seq[ObstructionType]]
) extends HammerObject {
  override def toJSON = {
    JsObject(Seq(
      "path" -> JsString(path),
      "type" -> `type`.toJSON,
      "x" -> JsNumber(x),
      "y" -> JsNumber(y),
      "width" -> JsNumber(width),
      "height" -> JsNumber(height)
      // TODO(edwardw): FIXME
    ))
  }
}

object PlacementConstraint extends HammerObjectCompanion[PlacementConstraint] {
  def apply(
    path: String,
    `type`: PlacementConstraintType,
    x: Double,
    y: Double,
    width: Double,
    height: Double
  ): PlacementConstraint = {
    new PlacementConstraint(
      path,
      `type`,
      x,
      y,
      width,
      height,
      None, // TODO(edwardw): FIXME
      None,
      None,
      None,
      None
    )
  }

  /* Helper function used to convert strings to Double
   * for forwards-compatibility with Decimal type. */
  def doubleOrString(value: play.api.libs.json.JsLookupResult): Double = {
    try {
      value.as[Double]
    } catch {
      case _: play.api.libs.json.JsResultException =>
        value.as[String].toDouble
    }
  }

  override def fromJSON(json: JsObject): PlacementConstraint = {
    new PlacementConstraint(
      (json \ "path").as[String],
      PlacementConstraintType.fromString((json \ "type").as[String]),
      doubleOrString(json \ "x"),
      doubleOrString(json \ "y"),
      doubleOrString(json \ "width"),
      doubleOrString(json \ "height"),
      None, // TODO(edwardw): FIXME
      None,
      None,
      None,
      None
    )
  }
}
