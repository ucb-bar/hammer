import os

from hammer.logging import HammerVLSILogging, Level, HammerVLSIFileLogger


class TestHammerVLSILogging:
    def test_colours(self):
        """
        Test that we can log with and without colour.
        """
        msg = "This is a test message"  # type: str

        log = HammerVLSILogging.context("test")

        HammerVLSILogging.enable_buffering = True  # we need this for test
        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        HammerVLSILogging.enable_colour = True
        log.info(msg)
        assert HammerVLSILogging.get_colour_escape(Level.INFO) + "[test] " + msg + HammerVLSILogging.COLOUR_CLEAR == HammerVLSILogging.get_buffer()[0]

        HammerVLSILogging.enable_colour = False
        log.info(msg)
        assert "[test] " + msg == HammerVLSILogging.get_buffer()[0]

    def test_subcontext(self):
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.enable_tag = True

        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(HammerVLSILogging.callback_buffering)

        # Get top context
        log = HammerVLSILogging.context("top")

        # Create sub-contexts.
        logA = log.context("A")
        logB = log.context("B")

        msgA = "Hello world from A"
        msgB = "Hello world from B"

        logA.info(msgA)
        logB.error(msgB)

        assert HammerVLSILogging.get_buffer() == ['[top] [A] ' + msgA, '[top] [B] ' + msgB]

    def test_file_logging(self, tmp_path):
        log_path = tmp_path / "log.log"

        filelogger = HammerVLSIFileLogger(str(log_path))

        HammerVLSILogging.clear_callbacks()
        HammerVLSILogging.add_callback(filelogger.callback)
        log = HammerVLSILogging.context()
        log.info("Hello world")
        log.info("Eternal voyage to the edge of the universe")
        filelogger.close()

        with open(log_path, 'r') as f:
            assert f.read().strip() == """
[<global>] Level.INFO: Hello world
[<global>] Level.INFO: Eternal voyage to the edge of the universe
""".strip()
