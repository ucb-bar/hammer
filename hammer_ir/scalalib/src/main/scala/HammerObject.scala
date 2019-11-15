// See LICENSE for licence details.

package hammer_ir

import scala.reflect.ClassTag

import play.api.libs.json.{Json, JsObject, JsValue}

/**
 * All Hammer IR types that can be converted to a JsValue.
 */
trait JSONConvertible {
  /**
   * Turn this object into a Play JSON object.
   */
  private[hammer_ir] def toJSON: JsValue
}

/**
 * All Hammer IR objects implement this trait which allows them to be
 * serialized to/deserialized from JSON.
 */
trait HammerObject {
  /**
   * Turn this object into a Play JSON object.
   */
  private[hammer_ir] def toJSON: JsObject

  /**
   * Turn this object into a JSON string.
   */
  override def toString = Json.prettyPrint(toJSON)

  /**
   * Write this object as a JSON string into the given file.
   */
  def toFile(filename: String) = reflect.io.File(filename).writeAll(toString)
}

/**
 * Abstract class mixed into companion classes of Hammer IR objects.
 */
abstract class HammerObjectCompanion[T <: HammerObject : ClassTag] {
  /**
   * Create this object from a Play JSON object.
   */
  private[hammer_ir] def fromJSON(json: JsObject): T

  /**
   * Create this object from a JSON string.
   */
  def fromString(json: String): T = fromJSON(Json.parse(json).as[JsObject])

  /**
   * Create this object from a JSON file.
   */
  def fromFile(filename: String): T = {
    val source = scala.io.Source.fromFile(filename)
    val lines = try source.mkString finally source.close()
    fromString(lines)
  }
}
