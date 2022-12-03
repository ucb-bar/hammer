#  Test helper code for Hammer logging.
#  This is considered a part of Hammer internals.
#
#  See LICENSE for licence details.

from typing import List

from .logging import HammerVLSILogging

class HammerLoggingCaptureContext:
    """
    Helper class to direct HammerVLSILogging to also log to a buffer, disable
    colours, and restore the original setting at the end of this context.
    Mainly useful in test contexts where the file outputs might not be
    available if we are running multiple tests in one process.
    """
    def __init__(self) -> None:
        self.old_enable_buffering = False  # type: bool
        self.old_enable_colour = True  # type: bool
        self.logs = []  # type: List[str]

    def log_contains(self, s: str) -> bool:
        """
        Check if the captured log contains the given string.
        :param s: String to check
        :return: True if found
        """
        return len(list(filter(lambda str: s in str, self.logs))) > 0

    def __enter__(self) -> "HammerLoggingCaptureContext":
        """
        Initialize the context by saving the old values for buffering and
        colour and enable buffering and disable colours.
        Also clears the buffer.
        """
        self.old_enable_buffering = HammerVLSILogging.enable_buffering
        self.old_enable_colour = HammerVLSILogging.enable_colour
        HammerVLSILogging.enable_buffering = True
        HammerVLSILogging.enable_colour = False
        HammerVLSILogging.output_buffer.clear()
        return self

    def __exit__(self, type, value, traceback) -> bool:
        """Restore the old settings for buffering and colour and clear
        the buffer."""
        self.logs = list(HammerVLSILogging.output_buffer)
        HammerVLSILogging.enable_buffering = self.old_enable_buffering
        HammerVLSILogging.output_buffer.clear()
        HammerVLSILogging.enable_colour = self.old_enable_colour
        # Return True (normal execution) if no exception occurred.
        return True if type is None else False
