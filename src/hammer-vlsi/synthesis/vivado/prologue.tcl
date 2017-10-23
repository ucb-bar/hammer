#set commondir [file dirname $scriptdir]
set srcdir [file join $scriptdir src]
set constrsdir [file join $scriptdir constrs]

set wrkdir [file join [pwd] obj]
set ipdir [file join $wrkdir ip]

set top {system}

set_property -dict [list \
  IP_REPO_PATHS $ipdir \
] [current_project]

proc recglob { basedir pattern } {
  set dirlist [glob -nocomplain -directory $basedir -type d *]
  set findlist [glob -nocomplain -directory $basedir $pattern]
  foreach dir $dirlist {
    set reclist [recglob $dir $pattern]
    set findlist [concat $findlist $reclist]
  }
  return $findlist
}


if {[get_filesets -quiet sources_1] eq ""} {
  create_fileset -srcset sources_1
}
set obj [current_fileset]

# Currently not used since system.v is generated and passed in as a source file.
#add_files -norecurse -fileset $obj [glob -directory $srcdir {*.v}]

set srcverilogfiles_split [split $srcmainverilogfiles]
foreach vsrc $srcverilogfiles_split {
  add_files -norecurse -fileset $obj $vsrc
}

if {[info exists ::env(EXTRA_VSRCS)]} {
  set extra_vsrcs [split $::env(EXTRA_VSRCS)]
  foreach extra_vsrc $extra_vsrcs {
    add_files -norecurse -fileset $obj $extra_vsrc
  }
}
## TODO: These paths and files should come from the caller, not within this script.
#if {[file exists [file join $srcdir include verilog]]} {
#  add_files -norecurse -fileset $obj [file join $srcdir include verilog DebugTransportModuleJtag.v]
#  add_files -norecurse -fileset $obj [file join $srcdir include verilog AsyncResetReg.v]
#}

set vsrc_top $srcmainverilogfile

set_property verilog_define [list "VSRC_TOP=${vsrc_top}"] $obj

add_files -norecurse -fileset $obj $vsrc_top

# Add the .dcp files for the SRAM IPs.
add_files -norecurse -fileset $obj [glob -directory $dcpdir {*.dcp}]

if {[get_filesets -quiet sim_1] eq ""} {
  create_fileset -simset sim_1
}
set obj [current_fileset -simset]

set_property TOP {tb} $obj

if {[get_filesets -quiet constrs_1] eq ""} {
  create_fileset -constrset constrs_1
}
set obj [current_fileset -constrset]
add_files -norecurse -fileset $obj [glob -directory $constrsdir {*.xdc}]
