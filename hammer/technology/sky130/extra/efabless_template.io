
(globals
    version = 3
    io_order = default
)
(row_margin
    (top
    (io_row ring_number = 1 margin = 0)
    )
    (right
    (io_row ring_number = 1 margin = 0)
    )
    (bottom
    (io_row ring_number = 1 margin = 0)
    )
    (left
    (io_row ring_number = 1 margin = 0)
    )
)
(iopad
    (topleft
    (locals ring_number = 1)
        (inst name = "corner_topleft"   orientation=R90 cell="s8iom0s8_corner_bus_overlay")
    )

    (top
    (locals ring_number = 1)
        (inst name = "<pad_inst>"   orientation=R0  offset=381)
        (inst name = "<pad_inst>"   orientation=R0  offset=638)
        (inst name = "<pad_inst>"   orientation=R0  offset=852)
        (inst name = "<pad_inst>"   orientation=R0  offset=1152)
        (inst name = "<pad_inst>"   orientation=R0  offset=1410)
        (inst name = "clamp_0"      orientation=R0  cell="s8iom0s8_top_ground_hvc_wpad"  offset=1667)
        (inst name = "<pad_inst>"   orientation=R0  offset=1919)
        (inst name = "<pad_inst>"   orientation=R0  offset=2364)
        (inst name = "<pad_inst>"   orientation=R0  offset=2621)
        (inst name = "clamp_1"      orientation=R0  cell="s8iom0s8_top_ground_hvc_wpad"  offset=2878)
        (inst name = "<pad_inst>"   orientation=R0  offset=3130)
    )

    (topright
    (locals ring_number = 1)
        (inst name = "corner_topright"   orientation=R0 cell="s8iom0s8_corner_bus_overlay")
    )

    (right
    (locals ring_number = 1)
        (inst name = "<pad_inst>"   orientation=R270    offset=580)
        (inst name = "<pad_inst>"   orientation=R270    offset=806)
        (inst name = "<pad_inst>"   orientation=R270    offset=1031)
        (inst name = "<pad_inst>"   orientation=R270    offset=1257)
        (inst name = "<pad_inst>"   orientation=R270    offset=1482)
        (inst name = "<pad_inst>"   orientation=R270    offset=1707)
        (inst name = "<pad_inst>"   orientation=R270    offset=1933)
        (inst name = "clamp_2"      orientation=R270    cell="s8iom0s8_top_ground_lvc_wpad"  offset=2374)
        (inst name = "clamp_3"      orientation=R270    cell="s8iom0s8_top_power_hvc_wpad"  offset=2594)
        (inst name = "<pad_inst>"   orientation=R270    offset=2819)
        (inst name = "<pad_inst>"   orientation=R270    offset=3045)
        (inst name = "<pad_inst>"   orientation=R270    offset=3270)
        (inst name = "<pad_inst>"   orientation=R270    offset=3496)
        (inst name = "<pad_inst>"   orientation=R270    offset=3721)
        (inst name = "<pad_inst>"   orientation=R270    offset=3946)
        (inst name = "clamp_4"      orientation=R270    cell="s8iom0s8_top_power_hvc_wpad"  offset=4167)
        (inst name = "<pad_inst>"   orientation=R270    offset=4392)
        (inst name = "clamp_5"      orientation=R270    cell="s8iom0s8_top_power_lvc_wpad"  offset=4613)
        (inst name = "<pad_inst>"   orientation=R270    offset=4838)
    )

    (bottomright
    (locals ring_number = 1)
        (inst name = "corner_bottomright"   orientation=R270 cell="s8iom0s8_corner_bus_overlay")
    )

    (bottom
    (locals ring_number = 1)
        (inst name = "clamp_6"      orientation=R180    cell="s8iom0s8_top_ground_hvc_wpad"   offset=469)
        (inst name = "reset"        orientation=R180    cell="s8iom0s8_top_xres4v2"   offset=738)
        (inst name = "<pad_inst>"   orientation=R180    offset=1012)
        (inst name = "clamp_7"      orientation=R180    cell="s8iom0s8_top_ground_lvc_wpad"   offset=1281)
        (inst name = "<pad_inst>"   orientation=R180    offset=1555)
        (inst name = "<pad_inst>"   orientation=R180    offset=1829)
        (inst name = "<pad_inst>"   orientation=R180    offset=2103)
        (inst name = "<pad_inst>"   orientation=R180    offset=2377)
        (inst name = "<pad_inst>"   orientation=R180    offset=2651)
        (inst name = "clamp_8"      orientation=R180    cell="s8iom0s8_top_ground_hvc_wpad"   offset=2920)
        (inst name = "clamp_9"      orientation=R180    cell="s8iom0s8_top_power_hvc_wpad"   offset=3189)
    )

    (bottomleft
    (locals ring_number = 1)
        (inst name = "corner_bottomleft"   orientation=R180 cell="s8iom0s8_corner_bus_overlay")
    )

    (left
    (locals ring_number = 1)
        (inst name = "clamp_10"     orientation=R90     cell="s8iom0s8_top_power_lvc_wpad"   offset=340)
        (inst name = "clamp_11"     orientation=R90     cell="s8iom0s8_top_power_hvc_wpad"   offset=551)
        (inst name = "<pad_inst>"   orientation=R90     offset=908)
        (inst name = "<pad_inst>"   orientation=R90     offset=1124)
        (inst name = "<pad_inst>"   orientation=R90     offset=1340)
        (inst name = "<pad_inst>"   orientation=R90     offset=1556)
        (inst name = "<pad_inst>"   orientation=R90     offset=1772)
        (inst name = "<pad_inst>"   orientation=R90     offset=1988)
        (inst name = "clamp_12"     orientation=R90     cell="s8iom0s8_top_ground_lvc_wpad"   offset=2204)
        (inst name = "clamp_13"     orientation=R90     cell="s8iom0s8_top_power_lvc_wpad"   offset=2415)
        (inst name = "<pad_inst>"   orientation=R90     offset=2626)
        (inst name = "<pad_inst>"   orientation=R90     offset=2842)
        (inst name = "<pad_inst>"   orientation=R90     offset=3058)
        (inst name = "<pad_inst>"   orientation=R90     offset=3274)
        (inst name = "<pad_inst>"   orientation=R90     offset=3490)
        (inst name = "<pad_inst>"   orientation=R90     offset=3706)
        (inst name = "<pad_inst>"   orientation=R90     offset=3922)
        (inst name = "clamp_14"     orientation=R90     cell="s8iom0s8_top_ground_hvc_wpad"   offset=4138)
        (inst name = "clamp_15"     orientation=R90     cell="s8iom0s8_top_power_hvc_wpad"   offset=4349)
        (inst name = "clamp_16"     orientation=R90     cell="s8iom0s8_top_power_hvc_wpad"   offset=4560)
        (inst name = "<pad_inst>"   orientation=R90     offset=4771)
    )
)
