// See LICENSE for licence details.

package hammer_ir.test

import org.scalatest.{FlatSpec, Matchers}
import play.api.libs.json.{JsObject, JsString}

import hammer_ir._

class HammerObjectSpec extends FlatSpec with Matchers {
  behavior of "HammerObject"

  case class Test(foobar: String) extends HammerObject {
    override def toJSON = JsObject(Seq(
      "foobar" -> JsString(foobar)
    ))
  }
  object Test extends HammerObjectCompanion[Test] {
    override def fromJSON(json: JsObject): Test = {
      new Test(
        (json \ "foobar").as[String]
      )
    }
  }

  it should "serialize and deserialize correctly" in {
    val t = Test("helloworld")
    // Need these replaces to be robust to spacing variations
    assert(t.toString
      .replaceAll("\n", "").replaceAll(" ", "")
      === """{"foobar":"helloworld"}""")
    assert(Test.fromJSON(t.toJSON) == t)
  }
}
