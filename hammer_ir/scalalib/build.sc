import mill._, scalalib._

object hammer_ir extends SbtModule {
  def scalaVersion = "2.12.6"

  // Unrooted submodule
  override def millSourcePath = super.millSourcePath / ammonite.ops.up

  def ivyDeps = Agg(
    ivy"com.typesafe.play::play-json:2.6.10"
  )

  object test extends Tests {
    def ivyDeps = Agg(ivy"org.scalatest::scalatest:3.0.4")
    def testFrameworks = Seq("org.scalatest.tools.Framework")
  }
}
