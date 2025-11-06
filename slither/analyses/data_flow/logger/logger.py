"""
Centralized logging class for data flow analysis.

This module provides a unified logging interface that:
- Centralizes all log messages to avoid repetition throughout the project
- Uses Loguru for enhanced logging capabilities
- Provides IPython embed functionality for error debugging

Usage Example:
    from slither.analyses.data_flow.logger import get_logger, LogMessages

    # Get the logger instance
    logger = get_logger()

    # Use centralized messages
    logger.info(LogMessages.ENGINE_START)
    logger.info(LogMessages.ENGINE_INIT, function_name="MyFunction")
    logger.warning(LogMessages.WARNING_SKIP_NODE, node_id=123, reason="Invalid state")
    logger.error(LogMessages.ERROR_ANALYSIS_FAILED, error="Some error", embed_on_error=True)

    # Custom messages are also supported
    logger.debug("Custom debug message")
    logger.info("Processing completed in {time}s", time=1.5)
"""

import inspect
import sys
from typing import Optional, Any, Dict, Type
from loguru import logger

# Try to import IPython embed, but don't fail if it's not available
try:
    from IPython import embed

    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False
    embed = None


class LogMessages:
    """Centralized repository for all log messages."""

    # Engine-related messages
    ENGINE_START = "Starting data flow analysis engine"
    ENGINE_COMPLETE = "Data flow analysis engine completed"
    ENGINE_INIT = "Initializing engine for function: {function_name}"
    ENGINE_NODE_PROCESSING = "Processing node {node_id} in function {function_name}"

    # Analysis-related messages
    ANALYSIS_START = "Starting analysis: {analysis_name}"
    ANALYSIS_COMPLETE = "Analysis completed: {analysis_name}"
    ANALYSIS_TRANSFER_FUNCTION = "Applying transfer function for operation: {operation_type}"
    ANALYSIS_STATE_UPDATE = "Updating analysis state at node {node_id}"

    # Domain-related messages
    DOMAIN_BOTTOM = "Domain is at bottom value"
    DOMAIN_JOIN = "Joining domain states"
    DOMAIN_STATE_UPDATE = "Domain state updated: {variant}"

    # Reentrancy-specific messages
    REENTRANCY_DETECTED = "Reentrancy vulnerability detected in function: {function_name}"
    REENTRANCY_ETH_DETECTED = "Reentrancy with ETH transfer detected in function: {function_name}"
    REENTRANCY_STATE_READ = "State variable {variable} read at node {node_id}"
    REENTRANCY_STATE_WRITE = "State variable {variable} written at node {node_id}"
    REENTRANCY_CALL_DETECTED = "External call detected at node {node_id}"
    REENTRANCY_ETH_TRANSFER = "ETH transfer detected at node {node_id}"

    # Error messages
    ERROR_ENGINE_INIT = "Failed to initialize engine: {error}"
    ERROR_ANALYSIS_FAILED = "Analysis failed: {error}"
    ERROR_TRANSFER_FUNCTION = "Error in transfer function: {error}"
    ERROR_NODE_PROCESSING = "Error processing node {node_id}: {error}"
    ERROR_DOMAIN_OPERATION = "Error in domain operation: {error}"
    ERROR_UNEXPECTED = "Unexpected error occurred: {error}"

    # Warning messages
    WARNING_SKIP_NODE = "Skipping node {node_id}: {reason}"
    WARNING_INVALID_STATE = "Invalid state encountered: {state}"
    WARNING_BACKWARD_ANALYSIS = "Backward analysis not implemented, skipping"

    # Debug messages
    DEBUG_WORKLIST_UPDATE = "Worklist updated: {count} nodes remaining"
    DEBUG_STATE_COMPARISON = "State comparison: {comparison}"
    DEBUG_FUNCTION_ENTRY = "Entering function: {function_name}"
    DEBUG_FUNCTION_EXIT = "Exiting function: {function_name}"


class DataFlowLogger:
    """
    Centralized logging handler for data flow analysis.

    This class provides a single point of access for all logging needs in the
    data flow analysis module. It wraps Loguru and provides additional features
    like IPython embed for error debugging.
    """

    def __init__(self, enable_ipython_embed: bool = True, log_level: str = "INFO"):
        """
        Initialize the logger.

        Args:
            enable_ipython_embed: Whether to enable IPython embed on errors
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.enable_ipython_embed = enable_ipython_embed and IPYTHON_AVAILABLE
        self.log_level = log_level

        # Configure Loguru logger
        logger.remove()  # Remove default handler
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True,
        )

        # Store the configured logger
        self._logger = logger

    @classmethod
    def get_logger(
        cls, enable_ipython_embed: bool = True, log_level: str = "INFO"
    ) -> "DataFlowLogger":
        """
        Get or create a logger instance.

        Args:
            enable_ipython_embed: Whether to enable IPython embed on errors
            log_level: Logging level

        Returns:
            DataFlowLogger instance
        """
        if not hasattr(cls, "_instance"):
            cls._instance = cls(enable_ipython_embed=enable_ipython_embed, log_level=log_level)
        return cls._instance

    def debug(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log a debug message.

        Args:
            message: Debug message (can use format placeholders)
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this message
            **kwargs: Keyword arguments for message formatting
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.debug(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, **kwargs)

    def info(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log an info message.

        Args:
            message: Info message (can use format placeholders)
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this message
            **kwargs: Keyword arguments for message formatting
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.info(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, **kwargs)

    def warning(self, message: str, *args, embed_on_error: bool = False, **kwargs) -> None:
        """
        Log a warning message.

        Args:
            message: Warning message (can use format placeholders)
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this message
            **kwargs: Keyword arguments for message formatting
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.warning(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, **kwargs)

    def error(self, message: str, *args, embed_on_error: bool = True, **kwargs) -> None:
        """
        Log an error message.

        Args:
            message: Error message (can use format placeholders)
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this error
            **kwargs: Keyword arguments for message formatting
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.error(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, **kwargs)

    def error_and_raise(
        self,
        message: str,
        exception_class: Type[Exception],
        *args,
        embed_on_error: bool = False,
        **kwargs,
    ) -> None:
        """
        Log an error message and raise an exception.

        Automatically includes file and line number information in the exception message.

        Args:
            message: Error message (can use format placeholders)
            exception_class: Exception class to raise
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this error
            **kwargs: Keyword arguments for message formatting (will be passed to exception)

        Raises:
            exception_class: The specified exception with the formatted message
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.error(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, **kwargs)

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

        # Extract kwargs that might be intended for exception, but use formatted message
        raise exception_class(enhanced_message)

    def critical(self, message: str, *args, embed_on_error: bool = True, **kwargs) -> None:
        """
        Log a critical error message.

        Args:
            message: Critical message (can use format placeholders)
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this error
            **kwargs: Keyword arguments for message formatting
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.critical(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, **kwargs)

    def exception(self, message: str, *args, embed_on_error: bool = True, **kwargs) -> None:
        """
        Log an exception with traceback.

        Args:
            message: Error message (can use format placeholders)
            *args: Positional arguments for message formatting
            embed_on_error: Whether to trigger IPython embed on this error
            **kwargs: Keyword arguments for message formatting
        """
        formatted_message = message.format(*args, **kwargs) if args or kwargs else message
        self._logger.exception(formatted_message)

        if embed_on_error and self.enable_ipython_embed:
            self._embed_for_debugging(message=formatted_message, exc_info=sys.exc_info(), **kwargs)

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
            "Starting IPython embed session for debugging. "
            "Type 'exit' or press Ctrl+D to continue."
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

    def patch(self, record: Dict[str, Any]) -> None:
        """
        Patch logger to add custom record information.

        Args:
            record: Dictionary of record attributes to patch
        """
        self._logger = self._logger.patch(lambda r: r.update(record))

    def set_level(self, level: str) -> None:
        """
        Set the logging level.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = level
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=level,
            colorize=True,
        )
        self._logger = logger


# Create a module-level instance for easy access
_logger_instance: Optional[DataFlowLogger] = None


def get_logger(enable_ipython_embed: bool = True, log_level: str = "INFO") -> DataFlowLogger:
    """
    Get the global logger instance.

    Args:
        enable_ipython_embed: Whether to enable IPython embed on errors
        log_level: Logging level

    Returns:
        DataFlowLogger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = DataFlowLogger.get_logger(
            enable_ipython_embed=enable_ipython_embed, log_level=log_level
        )
    return _logger_instance
