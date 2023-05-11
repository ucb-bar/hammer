# Run me in innovus

set json "./stackup.json"
set rdl_layer AP

set json [open $json "w"]

set layers {}

foreach layer [get_db layers] {
    set index [get_db $layer .route_index]
    set direction [get_db $layer .direction]
    set name [get_db $layer .name]
    # If the index is -1 it's not a routing layer
    if {$index >= 0 && $direction != "unassigned"} {
        if {$direction == "vertical"} {
            set offset [get_db $layer .offset_x]
        } else {
            set offset [get_db $layer .offset_y]
        }
        if {$name == $rdl_layer} {
            set offset 0.0
            set direction "redistribution"
        }
        set min_width [get_db $layer .min_width]
        set max_width [get_db $layer .max_width]
        set min_spacing [get_db $layer .min_spacing]
        # Note: there is a pitch field in the database, but it's for same-colored metals
        #       We are writing this to be color-agnostic, so we'll assume that the pitch is the
        #       Red-to-Green pitch
        set pitch [expr $min_width + $min_spacing]
        set spacing_table [get_db $layer .spacing_tables]
        # FIXME This might be broken? What do we do with more than one spacing table?
        # For now take the last one, since that appears to have correct data for colored metals
        set spacing_table [lrange [lindex [lindex $spacing_table 0] end] 2 end]
        set widths_and_spacings {}
        if { [llength $spacing_table] == 0} {
            lappend widths_and_spacings "\{\"width_at_least\": 0.0, \"min_spacing\": $min_spacing\}"
        } else {
            foreach line $spacing_table {
                lappend widths_and_spacings "\{\"width_at_least\": [lindex $line 1], \"min_spacing\": [lindex $line end]\}"
            }
        }
        set output "        \{"
        append output "\"name\": \"$name\", "
        append output "\"index\": $index, "
        append output "\"direction\": \"$direction\", "
        append output "\"min_width\": $min_width, "
        append output "\"max_width\": $max_width, "
        append output "\"pitch\": $pitch, "
        append output "\"offset\": $offset, "
        append output {"power_strap_widths_and_spacings": [}
        append output [join $widths_and_spacings ", "]
        append output "\]\}"

        lappend layers $output
    }
}

puts $json "    \{"
puts $json {      "name" : "TODO",}
puts $json {      "metals": [}

puts $json [join $layers ",\n"]

puts $json "      \]"
puts $json "    \}"

close $json
