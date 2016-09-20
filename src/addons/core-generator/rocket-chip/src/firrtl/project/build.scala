import sbt._
import Keys._
import complete._
import complete.DefaultParsers._
import xerial.sbt.Pack._
import sbtassembly.AssemblyPlugin.autoImport._

object BuildSettings extends Build {
  override lazy val settings = super.settings ++ Seq(
    organization := "berkeley",
    version      := "1.2",
    scalaVersion := "2.11.7",
    parallelExecution in Global := false,
    traceLevel   := 15,
    scalacOptions ++= Seq("-deprecation","-unchecked"),
    libraryDependencies ++= Seq("org.scala-lang" % "scala-reflect" % scalaVersion.value)
  )

  lazy val firrtl       = project in file("firrtl")
  lazy val @@TOP_NAME_LOWER@@ = (project in file(".")).dependsOn(firrtl)
  mainClass in (Compile, run) := Some("@@TOP_NAME_UPPER@@")
}
