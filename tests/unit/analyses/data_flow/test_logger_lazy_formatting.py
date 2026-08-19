"""Regression tests: DataFlowLogger hands templates to loguru unformatted.

Every :class:`DataFlowLogger` method used to render its message eagerly with
``message.format(*args, **kwargs)`` and then pass loguru a plain string. That
was wrong in two observable ways:

* the template was rendered even when the level would drop the record, so a
  template loguru would never have looked at could still raise (``KeyError`` on
  a missing key, or on the literal braces of a rendered tag set such as
  ``"{UP, DOWN}"``);
* the record was attributed to ``logger.py`` instead of the call site, because
  the wrapper frame was not skipped.

The methods now call ``self._logger.opt(depth=1).<level>(message, *args,
**kwargs)``. loguru's ``_log`` returns before any formatting when the level is
below the minimum handler level, and only calls ``message.format`` when
positional or keyword arguments were actually supplied.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from loguru import logger as loguru_logger

from slither.analyses.data_flow.logger import logger as logger_module
from slither.analyses.data_flow.logger.logger import DataFlowLogger


LoggerFactory = Callable[[str], tuple[DataFlowLogger, list[dict[str, Any]]]]

# Rendering this needs a key named "UP, DOWN"; formatting it raises KeyError.
UNFORMATTABLE_TEMPLATE = "joined tags {UP, DOWN} for {name}"


@pytest.fixture
def build_capturing_logger() -> Iterator[LoggerFactory]:
    """Yield a factory building a DataFlowLogger that logs into a record list.

    ``DataFlowLogger.__init__`` calls loguru's ``logger.remove()``, which drops
    every sink in the process, so this fixture cannot leave global state exactly
    as it found it. It does the next best thing: it snapshots the module-level
    singleton, and on teardown removes every sink it installed and restores the
    singleton. What remains is the sink-less loguru state that constructing any
    DataFlowLogger already produces, which is also what the data-flow end-to-end
    conftest deliberately installs.

    The factory takes the level for both the logger and the capture sink and may
    only be called once per test, since each call clears the existing sinks.

    Yields:
        A callable mapping a level name to the logger and the list of records
        its sink received
    """
    saved_instance = logger_module._logger_instance

    def build(level: str) -> tuple[DataFlowLogger, list[dict[str, Any]]]:
        dataflow_logger = DataFlowLogger(enable_ipython_embed=False, log_level=level)
        loguru_logger.remove()
        records: list[dict[str, Any]] = []
        loguru_logger.add(
            lambda message: records.append(message.record),
            level=level,
            format="{message}",
        )
        return dataflow_logger, records

    try:
        yield build
    finally:
        loguru_logger.remove()
        logger_module._logger_instance = saved_instance


def _emit_from_helper(dataflow_logger: DataFlowLogger) -> int:
    """Log one info record from this helper and report the call's line number.

    The ``info`` call must stay on the line directly below the ``call_line``
    assignment, which is what makes the returned number exact.

    Args:
        dataflow_logger: Logger to emit through

    Returns:
        The line number of the ``info`` call in this file
    """
    frame = inspect.currentframe()
    assert frame is not None, "this test needs CPython frame introspection"
    call_line = frame.f_lineno + 1
    dataflow_logger.info("emitted from a helper")
    return call_line


@pytest.mark.parametrize("method_name", ["debug", "info", "warning", "error", "exception"])
def test_dropped_record_never_formats_its_template(
    build_capturing_logger: LoggerFactory, method_name: str
) -> None:
    """A template below the sink level is not rendered, so it cannot raise."""
    dataflow_logger, records = build_capturing_logger("CRITICAL")

    getattr(dataflow_logger, method_name)(UNFORMATTABLE_TEMPLATE, name="transferFrom")

    assert records == []


def test_dropped_debug_tolerates_a_missing_placeholder_key(
    build_capturing_logger: LoggerFactory,
) -> None:
    """A debug template whose keys do not match its kwargs is never rendered."""
    dataflow_logger, records = build_capturing_logger("INFO")

    dataflow_logger.debug("worklist has {count} nodes remaining", nodes=3)

    assert records == []


def test_keyword_arguments_render_when_the_record_is_emitted(
    build_capturing_logger: LoggerFactory,
) -> None:
    """Deferring formatting still produces the interpolated message."""
    dataflow_logger, records = build_capturing_logger("INFO")

    dataflow_logger.info("Starting analysis of {name}", name="transferFrom")

    assert len(records) == 1
    assert records[0]["message"] == "Starting analysis of transferFrom"


def test_positional_arguments_render_when_the_record_is_emitted(
    build_capturing_logger: LoggerFactory,
) -> None:
    """Positional arguments reach loguru rather than being consumed early."""
    dataflow_logger, records = build_capturing_logger("INFO")

    dataflow_logger.info("node {} of {}", 3, 7)

    assert len(records) == 1
    assert records[0]["message"] == "node 3 of 7"


def test_message_without_arguments_passes_through_verbatim(
    build_capturing_logger: LoggerFactory,
) -> None:
    """Literal braces survive when no formatting arguments are supplied."""
    dataflow_logger, records = build_capturing_logger("INFO")

    dataflow_logger.info("joined tags {UP, DOWN} at node 4")

    assert len(records) == 1
    assert records[0]["message"] == "joined tags {UP, DOWN} at node 4"


def test_record_is_attributed_to_the_calling_site(
    build_capturing_logger: LoggerFactory,
) -> None:
    """``opt(depth=1)`` skips the wrapper frame inside logger.py."""
    dataflow_logger, records = build_capturing_logger("INFO")

    call_line = _emit_from_helper(dataflow_logger)

    assert len(records) == 1
    record = records[0]
    assert record["name"] == __name__
    assert record["function"] == "_emit_from_helper"
    assert record["line"] == call_line
