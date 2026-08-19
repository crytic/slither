"""
Centralized logging for data flow analysis.

This module owns a single process-wide :class:`DataFlowLogger`, retrieved with
:func:`get_logger`. Reconfiguration is explicit: :func:`configure_logger` is the
only way to change the level or the interactive-debug behaviour once the
instance exists, and it applies the change rather than dropping it.

Call convention:
    Messages are loguru brace-style templates. Formatting is deferred to loguru
    and only happens when positional or keyword arguments are supplied, so a
    message logged without arguments is emitted verbatim (literal braces are
    safe) and a message filtered out by the level is never formatted at all.

        logger = get_logger()
        logger.info("Starting analysis of {name}", name=function.name)
        logger.debug("Worklist: {count} nodes remaining", count=len(worklist))

    Never combine an already-interpolated f-string with extra arguments: loguru
    would then format the rendered text, and literal braces in it (a rendered
    tag set such as "{UP, DOWN}") would raise a formatting error.

Interactive debugging:
    ``embed_on_error=True`` only opens an IPython session when the environment
    variable ``SLITHER_DATA_FLOW_DEBUG=1`` is set. Without that opt-in the flag
    is ignored, so automated runs (CI, MCP servers) can never block on stdin.
"""

import inspect
import os
import sys
from typing import Any
from loguru import logger

# Try to import IPython embed, but don't fail if it's not available
try:
    from IPython import embed

    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False
    embed = None

INTERACTIVE_DEBUG_ENV_VAR = "SLITHER_DATA_FLOW_DEBUG"

_LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def _interactive_debug_enabled() -> bool:
    """
    Report whether the operator opted in to interactive debugging.

    Read at call time so that setting the environment variable takes effect
    without rebuilding the logger.

    Returns:
        True when SLITHER_DATA_FLOW_DEBUG is set to "1"
    """
    return os.environ.get(INTERACTIVE_DEBUG_ENV_VAR) == "1"


def _render(message: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
    """
    Render a message template the way loguru would.

    Only used on paths that need the text eagerly (exception messages, IPython
    embed context); regular logging leaves formatting to loguru.

    Args:
        message: Message template
        args: Positional formatting arguments
        kwargs: Keyword formatting arguments

    Returns:
        The formatted message, or the template unchanged when no arguments were
        supplied
    """
    return message.format(*args, **kwargs) if args or kwargs else message


class DataFlowLogger:
    """
    Centralized logging handler for data flow analysis.

    This class provides a single point of access for all logging needs in the
    data flow analysis module. It wraps Loguru and provides additional features
    like IPython embed for error debugging.
    """

    def __init__(self, enable_ipython_embed: bool = False, log_level: str = "INFO"):
        """
        Initialize the logger.

        Args:
            enable_ipython_embed: Whether call sites may request IPython embed on
                errors. Embedding additionally requires the
                SLITHER_DATA_FLOW_DEBUG=1 opt-in.
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.enable_ipython_embed = enable_ipython_embed and IPYTHON_AVAILABLE
        self.log_level = log_level

        logger.remove()  # Remove default handler
        self._handler_id: int = self._add_sink(log_level)

        # Store the configured logger
        self._logger = logger

    @staticmethod
    def _add_sink(log_level: str) -> int:
        """
        Install the stderr sink used by data flow analysis.

        Args:
            log_level: Logging level for the sink

        Returns:
            The loguru handler id, needed to replace the sink later
        """
        return logger.add(sys.stderr, format=_LOG_FORMAT, level=log_level, colorize=True)

    def set_level(self, level: str) -> None:
        """
        Set the logging level, replacing this logger's stderr sink.

        Reachable from the command line through ``--data-flow-log-level``.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            logger.remove(self._handler_id)
        except ValueError:
            # The sink was already removed (tests silence loguru this way);
            # installing a fresh one below is still the correct outcome.
            pass
        self.log_level = level
        self._handler_id = self._add_sink(level)

    def _should_embed(self, embed_on_error: bool) -> bool:
        """
        Decide whether a log call may open an interactive session.

        Args:
            embed_on_error: What the call site requested

        Returns:
            True only when the call site asked for it, this logger allows it,
            and the operator opted in via the environment
        """
        return embed_on_error and self.enable_ipython_embed and _interactive_debug_enabled()

    def debug(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log a debug message.

        Args:
            message: Message template; formatting is deferred to loguru
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting
        """
        self._logger.opt(depth=1).debug(message, *args, **kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(_render(message, args, kwargs), **kwargs)

    def info(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log an info message.

        Args:
            message: Message template; formatting is deferred to loguru
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting
        """
        self._logger.opt(depth=1).info(message, *args, **kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(_render(message, args, kwargs), **kwargs)

    def warning(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log a warning message.

        Args:
            message: Message template; formatting is deferred to loguru
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting
        """
        self._logger.opt(depth=1).warning(message, *args, **kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(_render(message, args, kwargs), **kwargs)

    def error(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log an error message.

        Args:
            message: Message template; formatting is deferred to loguru
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting
        """
        self._logger.opt(depth=1).error(message, *args, **kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(_render(message, args, kwargs), **kwargs)

    def error_and_raise(
        self,
        message: str,
        exception_class: type[Exception],
        *args,
        embed_on_error: bool = False,
        **kwargs,
    ) -> None:
        """
        Log an error message and raise an exception.

        Automatically includes file and line number information in the exception
        message. The template is rendered eagerly here because the exception
        carries the text.

        Args:
            message: Message template; formatting is deferred to loguru
            exception_class: Exception class to raise
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting

        Raises:
            exception_class: The specified exception with the formatted message
        """
        self._logger.opt(depth=1).error(message, *args, **kwargs)
        formatted_message = _render(message, args, kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(formatted_message, **kwargs)

        # Automatically include file and line number information
        # Use stack()[1] to get the caller's frame (skip this method itself)
        stack: list[inspect.FrameInfo] = inspect.stack()
        if len(stack) > 1:
            caller_frame: inspect.FrameInfo = stack[1]
            filename: str = caller_frame.filename
            line_number: int = caller_frame.lineno
            file_info: str = f"{filename}:{line_number}"
            enhanced_message: str = f"{formatted_message} (at {file_info})"
        else:
            enhanced_message = formatted_message

        raise exception_class(enhanced_message)

    def critical(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log a critical error message.

        Args:
            message: Message template; formatting is deferred to loguru
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting
        """
        self._logger.opt(depth=1).critical(message, *args, **kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(_render(message, args, kwargs), **kwargs)

    def exception(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log an exception with traceback.

        Args:
            message: Message template; formatting is deferred to loguru
            *args: Positional arguments for message formatting
            embed_on_error: Request IPython embed (requires the environment opt-in)
            **kwargs: Keyword arguments for message formatting
        """
        self._logger.opt(depth=1).exception(message, *args, **kwargs)

        if self._should_embed(embed_on_error):
            self._embed_for_debugging(
                _render(message, args, kwargs), exc_info=sys.exc_info(), **kwargs
            )

    def _embed_for_debugging(self, message: str, **context: Any) -> None:
        """
        Launch IPython embed for interactive debugging.

        Args:
            message: The error message that triggered the embed
            **context: Additional context variables to make available in the embed session
        """
        if not IPYTHON_AVAILABLE:
            self._logger.warning("IPython not available, cannot start embed session")
            return

        self._logger.info(
            "Starting IPython embed session for debugging. Type 'exit' or press Ctrl+D to continue."
        )

        # Make useful variables available in the embed session
        embed_locals = {"message": message, "logger": self, **context}

        # Start IPython embed with local context
        embed(user_ns=embed_locals, colors="neutral")

    def bind(self, **kwargs) -> Any:
        """
        Bind contextual information to logger.

        This creates a new logger instance with bound context that will be
        included in all log messages.

        Args:
            **kwargs: Context variables to bind

        Returns:
            Bound logger instance
        """
        return self._logger.bind(**kwargs)

    def patch(self, record: dict[str, Any]) -> None:
        """
        Patch logger to add custom record information.

        Args:
            record: Dictionary of record attributes to patch
        """
        self._logger = self._logger.patch(lambda r: r.update(record))


# The single process-wide instance; there is no second cache on the class.
_logger_instance: DataFlowLogger | None = None


def get_logger() -> DataFlowLogger:
    """
    Get the process-wide data flow logger, creating it on first use.

    Takes no configuration: passing settings here would silently lose whichever
    import happened second. Use :func:`configure_logger` to change settings.

    Returns:
        DataFlowLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DataFlowLogger()
    return _logger_instance


def configure_logger(
    *,
    log_level: str | None = None,
    enable_ipython_embed: bool | None = None,
) -> DataFlowLogger:
    """
    Reconfigure the process-wide data flow logger, applying every setting given.

    Unlike a configured ``get_logger()``, this never drops a setting because the
    logger already exists: each argument that is not None is applied to the
    existing instance.

    Args:
        log_level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_ipython_embed: Whether call sites may request IPython embed.
            Embedding still requires the SLITHER_DATA_FLOW_DEBUG=1 opt-in.

    Returns:
        The reconfigured DataFlowLogger instance
    """
    instance = get_logger()
    if log_level is not None:
        instance.set_level(log_level)
    if enable_ipython_embed is not None:
        instance.enable_ipython_embed = enable_ipython_embed and IPYTHON_AVAILABLE
    return instance
