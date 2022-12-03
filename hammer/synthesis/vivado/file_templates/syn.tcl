# TCL fragment to synthesize a design in Vivado and spit out some files.

synth_design -top $top -flatten_hierarchy rebuilt
write_checkpoint -force [file join $wrkdir post_synth]

opt_design
write_checkpoint -force [file join $wrkdir post_opt]
write_verilog -force "obj/${top}_post_synth.v"
