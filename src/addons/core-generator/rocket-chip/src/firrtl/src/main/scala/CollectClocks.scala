// See LICENSE for license details.

// Firrtl imports
import firrtl._
import firrtl.ir._
import firrtl.passes.Pass

// Scala imports
import scala.collection.mutable
//import java.io.Writer

// JSON serialization
import spray.json._
import DefaultJsonProtocol._

// Collects clock-typed ports that are either:
//   1) input to top level module
//   2) output to any module
class CollectClocks(macroTop: String) extends Pass {
  def name = "Collect Clocks"

  def run(c: Circuit): Circuit = {
    val clocks = mutable.HashSet[String]() //ModuleName.ClockName
    def addPorts(d: Direction)(p: Port): Unit = p match {
      case Port(info, name, dir, ClockType) if dir == d => clocks += name
      case _ =>
    }
    def onModule(m: DefModule): DefModule = {
      if(m.name == c.main) m.ports foreach addPorts(Input)
      m.ports foreach addPorts(Output)
      m
    }
    val outputFile = new java.io.PrintWriter(macroTop)
    c.copy(modules=c.modules map onModule)
    outputFile.write(clocks.toSeq.toJson.prettyPrint)
    outputFile.close()
    c
  }
}
