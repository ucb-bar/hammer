#  Hammer logging code.
#
#  See LICENSE for licence details.

from functools import reduce
from enum import Enum
from typing import Callable, Iterable, List, NamedTuple, Type, Optional

class Level(Enum):
    """
    Logging levels.
    """
    # Explanation of logging levels:
    # DEBUG - for debugging only, too verbose for general use
    # INFO - general informational messages (e.g. "starting synthesis")
    # WARNING - things the user should check out (e.g. a setting uses something very usual)
    # ERROR - something gone wrong but the process can still continue (e.g. synthesis run failed), though the user should definitely check it out.
    # FATAL - an error which will abort the process immediately without warning (e.g. assertion failure)
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    FATAL = 4


# Message including additional metadata such as level and context.
FullMessage = NamedTuple('FullMessage', [
    ('message', str),
    ('level', Level),
    ('context', List[str])
])


# Need a way to bind the callbacks to the class...
def with_default_callbacks(cls):
    # TODO: think about how to remove default callbacks
    cls.add_callback(cls.callback_print)
    cls.add_callback(cls.callback_buffering)
    return cls


class HammerVLSIFileLogger:
    """A file logger for HammerVLSILogging."""

    def __init__(self, output_path: str, format_msg_callback: Optional[Callable[[FullMessage], str]] = None) -> None:
        """
        Create a new file logger.

        :param output_path: Output path of the logger.
        :param format_msg_callback: Optional callback to run to build the message. None to use HammerVLSILogging.build_log_message.
        """
        self._file = open(output_path, "a")
        self._format_msg_callback = format_msg_callback

    def __enter__(self):
        return self

    def close(self) -> None:
        """
        Close this file logger.
        """
        self._file.close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def callback(self) -> Callable[[FullMessage], None]:
        """Get the callback for HammerVLSILogging.add_callback."""

        def file_callback(fullmessage: FullMessage) -> None:
            if self._format_msg_callback is not None:
                self._file.write(self._format_msg_callback(fullmessage) + "\n")
            else:
                self._file.write(HammerVLSILogging.build_log_message(fullmessage) + "\n")

        return file_callback


@with_default_callbacks
class HammerVLSILogging:
    """Singleton which handles logging in hammer-vlsi.

    This class is generally not intended to be used directly for logging, but through HammerVLSILoggingContext instead.
    """

    # Enable colour in logging?
    enable_colour = True  # type: bool

    # If buffering is enabled, instead of printing right away, we will store it
    # into a buffer for later retrieval.
    enable_buffering = False  # type: bool

    # Enable printing the tag (e.g. "[synthesis] ...).
    enable_tag = True  # type: bool

    # Various escape characters for colour output.
    COLOUR_BLUE = "\033[96m"
    COLOUR_GREY = "\033[37m"
    COLOUR_YELLOW = "\033[33m"
    COLOUR_RED = "\033[91m"
    COLOUR_RED_BG = "\033[101m"
    # Restore the default terminal colour.
    COLOUR_CLEAR = "\033[0m"

    # Some default callback implementations.
    @classmethod
    def callback_print(cls, fullmessage: FullMessage) -> None:
        """Default callback which prints a colour message."""
        print(cls.build_message(fullmessage))

    output_buffer = []  # type: List[str]

    @classmethod
    def callback_buffering(cls, fullmessage: FullMessage) -> None:
        """Get the current contents of the logging buffer and clear it."""
        if not cls.enable_buffering:
            return
        cls.output_buffer.append(cls.build_message(fullmessage))

    @classmethod
    def build_log_message(cls, fullmessage: FullMessage) -> str:
        """Build a plain message for logs, without colour."""
        template = "{context} {level}: {message}"

        return template.format(context=cls.get_tag(fullmessage.context), level=fullmessage.level,
                               message=fullmessage.message)

    # List of callbacks to call for logging.
    callbacks = []  # type: List[Callable[[FullMessage], None]]

    @classmethod
    def clear_callbacks(cls) -> None:
        """Clear the list of callbacks."""
        cls.callbacks = []

    @classmethod
    def add_callback(cls, callback: Callable[[FullMessage], None]) -> None:
        """Add a callback."""
        cls.callbacks.append(callback)

    @classmethod
    def context(cls, new_context: str = "") -> "HammerVLSILoggingContext":
        """
        Create a new context.

        :param new_context: Context name. Leave blank to get the global context.
        """
        if new_context == "":
            return HammerVLSILoggingContext([], cls)
        else:
            return HammerVLSILoggingContext([new_context], cls)

    @classmethod
    def get_colour_escape(cls, level: Level) -> str:
        """Colour table to translate level -> colour in logging."""
        table = {
            Level.DEBUG: cls.COLOUR_GREY,
            Level.INFO: cls.COLOUR_BLUE,
            Level.WARNING: cls.COLOUR_YELLOW,
            Level.ERROR: cls.COLOUR_RED,
            Level.FATAL: cls.COLOUR_RED_BG
        }
        if level in table:
            return table[level]
        else:
            return ""

    @classmethod
    def log(cls, fullmessage: FullMessage) -> None:
        """
        Log the given message at the given level in the given context.
        """
        for callback in cls.callbacks:
            callback(fullmessage)

    @classmethod
    def build_message(cls, fullmessage: FullMessage) -> str:
        """Build a colour message."""
        message = fullmessage.message
        level = fullmessage.level
        context = fullmessage.context

        context_tag = cls.get_tag(context)  # type: str

        output = ""  # type: str
        output += cls.get_colour_escape(level) if cls.enable_colour else ""
        if cls.enable_tag and context_tag != "":
            output += context_tag + " "
        output += message
        output += cls.COLOUR_CLEAR if cls.enable_colour else ""

        return output

    @staticmethod
    def get_tag(context: List[str]) -> str:
        """Helper function to get the tag for outputting a message given a context."""
        if len(context) > 0:
            return str(reduce(lambda a, b: a + " " + b, map(lambda x: "[%s]" % (x), context)))
        else:
            return "[<global>]"

    @classmethod
    def get_buffer(cls) -> Iterable[str]:
        """Get the current contents of the logging buffer and clear it."""
        if not cls.enable_buffering:
            raise ValueError("Buffering is not enabled")
        output = list(cls.output_buffer)
        cls.output_buffer = []
        return output


class HammerVLSILoggingContext:
    """
    Logging interface to hammer-vlsi which contains a context (list of strings denoting hierarchy where the log occurred).
    e.g. ["synthesis", "subprocess run-synthesis"]
    """

    def __init__(self, context: List[str], logging_class: Type[HammerVLSILogging]) -> None:
        """
        Create a new interface with the given context.
        """
        self._context = context  # type: List[str]
        self.logging_class = logging_class  # type: Type[HammerVLSILogging]

    def context(self, new_context: str) -> "HammerVLSILoggingContext":
        """
        Create a new subcontext from this context.
        """
        context2 = list(self._context)
        context2.append(new_context)
        return HammerVLSILoggingContext(context2, self.logging_class)

    def debug(self, message: str) -> None:
        """Create an debug-level log message."""
        return self.log(message, Level.DEBUG)

    def info(self, message: str) -> None:
        """Create an info-level log message."""
        return self.log(message, Level.INFO)

    def warning(self, message: str) -> None:
        """Create an warning-level log message."""
        return self.log(message, Level.WARNING)

    def error(self, message: str) -> None:
        """Create an error-level log message."""
        return self.log(message, Level.ERROR)

    def fatal(self, message: str) -> None:
        """Create an fatal-level log message."""
        return self.log(message, Level.FATAL)

    def log(self, message: str, level: Level) -> None:
        return self.logging_class.log(FullMessage(message, level, self._context))
