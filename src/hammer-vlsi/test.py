#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  Tests for hammer-vlsi
#  
#  Copyright 2017 Edward Wang <edward.c.wang@compdigitec.com>

import hammer_vlsi

import unittest

class HammerVLSILoggingTest(unittest.TestCase):
    def test_colours(self):
        """
        Test that we can log with and without colour.
        """
        msg = "This is a test message" # type: str

        logging = hammer_vlsi.HammerVLSILogging

        hammer_vlsi.HammerVLSILogging.enable_buffering = True # we need this for test
        hammer_vlsi.HammerVLSILogging.clear_callbacks()
        hammer_vlsi.HammerVLSILogging.add_callback(hammer_vlsi.HammerVLSILogging.callback_buffering)

        hammer_vlsi.HammerVLSILogging.enable_colour = True
        logging.info(msg)
        self.assertEqual(logging.get_colour_escape(logging.Level.INFO) + "[<global>] " + msg + logging.COLOUR_CLEAR, logging.get_buffer()[0])

        hammer_vlsi.HammerVLSILogging.enable_colour = False
        logging.info(msg)
        self.assertEqual("[<global>] " + msg, logging.get_buffer()[0])

if __name__ == '__main__':
    unittest.main()
