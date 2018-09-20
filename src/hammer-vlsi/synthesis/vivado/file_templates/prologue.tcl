#set commondir [file dirname $scriptdir]
set srcdir [file join $scriptdir src]
set constrsdir [file join $scriptdir constrs]

set ipdir [file join $wrkdir ip]

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
