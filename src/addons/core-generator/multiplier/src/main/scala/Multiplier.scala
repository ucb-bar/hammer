import Chisel._
import java.io.{File, FileWriter}

class Multiplier extends Module {
  val io = new Bundle {
    val a = UInt(INPUT,  width = 32)
    val b = UInt(INPUT,  width = 32)
    val q = UInt(OUTPUT, width = 64)
  }

  io.q := io.a * io.b
}

object Main extends App {
  val longName = "Multiplier"
  val circuit = Driver.elaborate(() => new Multiplier)
  Driver.dumpFirrtl(circuit, Some(new File(args(0), s"$longName.fir")))
}
