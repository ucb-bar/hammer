package rocketchip

import Chisel._
import cde.{Parameters, Field, Config}
import junctions.{NastiIO, NastiCrossbar}

/* These objects are used to configure the crossbar.  Here "case object" is
 * essentially an "enum" but without an actual value -- they can be used in
 * match statements later. */
case object XBarMasters extends Field[Int]
case object XBarSlaves  extends Field[Int]

/* This configuration object sets the stuff required for the crossbar
 * top-level. */
class XBarConfig(masters: Int, slaves: Int) extends Config (
  (pname, site, here) => pname match {
    case XBarMasters => masters
    case XBarSlaves  => slaves
  }
)

/* Rocket Chip works by defining configurations on the command-line.  You can
 * only provide a configuration object via its class name, so we need simple
 * textual names for every configuration object. */
class XBar2x2Config extends Config(new XBarConfig(2, 2) ++ new DefaultConfig)

/* The top-level IOs of the top-level module. */
class AXI4XBarIO(implicit p: Parameters) extends Bundle {
  val masters = Vec(p(XBarMasters), new NastiIO).flip
  val slaves  = Vec(p(XBarSlaves) , new NastiIO)
  override def cloneType = (new AXI4XBarIO).asInstanceOf[this.type]
}

/* The top level of an AXI4 crossbar.  This takes a configuration object as
 * passed from the Rocket Chip build infastructure and instantiates an AXI4
 * crossbar based on that configuration. */
class AXI4XBar(topParams: Parameters) extends Module with HasTopLevelParameters {
  /* Configuration objects are passed down using "implicit parameters".  This
   * only needs to exist at the top-level module when using Rocket Chip's
   * configuration system, it's what makes the "implicit p: Parameters" work
   * all over the place. */
  implicit val p = topParams

  /* This defines the ports of this module, it's pretty much just Chisel
   * boilerplate. */
  val io = new AXI4XBarIO

  /* A Scala function that produces a Chisel circuit.  This maps from an AXI
   * memory address to a port on the crossbar.  You could have arbitrary logic
   * here. */
  val addr2port = { addr: UInt => addr / UInt(1024) }

  /* Instantiates a crossbar with the correct number of ports and address map. */
  val xbar = Module(
    new NastiCrossbar(
      p(XBarMasters),
      p(XBarSlaves),
      addr2port
    )
  )

  /* Here's two ways to connect all the ports out from the crossbar to the top
   * level: a for loop that explicitly indexes into the Vecs, and a zip, which
   * takes two lists and turns them into one list of pairs. */
  for (i <- 0 until p(XBarMasters)) {
    TopUtils.connectNasti(xbar.io.masters(i), io.masters(i))
  }

  for ((xbar, top) <- xbar.io.slaves zip io.slaves) {
    /* This Scala function wires up the various AXI members.  Since Chisel
     * objects are just Scala objects, you can pass them to a function and do
     * whatever you want. */
    TopUtils.connectNasti(top, xbar)
  }
}
