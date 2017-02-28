# TCL fragment to synthesize a design in Vivado and spit out some files.

set_param {messaging.defaultLimit} 1000000

# Suppress "design X has port P driven by constant" warnings since they've been
# intentionally driven.
set_msg_config -new_severity "INFO" -id "Synth 8-3917"

read_ip [glob -directory $ipdir [file join * {*.xci}]]

synth_design -top $top -flatten_hierarchy rebuilt
write_checkpoint -force [file join $wrkdir post_synth]

opt_design
write_checkpoint -force [file join $wrkdir post_opt]
