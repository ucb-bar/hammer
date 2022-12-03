# TCL fragment to set messaging parameters

set_param {messaging.defaultLimit} 1000000

# Suppress "design X has port P driven by constant" warnings since they've been
# intentionally driven.
set_msg_config -new_severity "INFO" -id "Synth 8-3917"
