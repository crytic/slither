"""Regression guard: ``set_level`` is real code, reachable from the CLI.

``DataFlowLogger.set_level`` used to be dead weight: it was defined, but nothing
in the repository ever called it, so the data-flow logger was permanently stuck
at whichever level the first ``get_logger()`` happened to build. These tests pin
the two halves of the fix:

* :func:`configure_logger` is the reconfiguration entry point and it delegates
  the level to ``set_level`` (and only when a level was actually requested);
* ``set_level`` genuinely swaps this logger's own sink, so a lower-severity
  record stops reaching it while a higher-severity one still does;
* ``slither/__main__.py`` calls ``configure_logger`` with the value parsed from
  the ``--data-flow-log-level`` flag, which is what makes the whole chain
  reachable by a user.

Global-state note: the loguru logger is process-wide and
``DataFlowLogger.__init__`` calls ``loguru.logger.remove()``, dropping every
sink in the process. The fixture below therefore removes every sink it leaves
behind, ending in the same silent state that
``tests/e2e/data_flow/conftest.py`` installs for its own session, and restores
the module-level ``_logger_instance`` singleton through ``monkeypatch``.
"""

from __future__ import annotations

import ast
import io
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from loguru import logger as loguru_logger

import slither
from slither.analyses.data_flow.logger import DataFlowLogger, configure_logger
from slither.analyses.data_flow.logger import logger as logger_module

LOGGER_PACKAGE = "slither.analyses.data_flow.logger"
CLI_FLAG = "--data-flow-log-level"
CLI_DEST = "data_flow_log_level"


@pytest.fixture
def build_buffered_logger(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Callable[[], tuple[DataFlowLogger, io.StringIO]]]:
    """Return a factory building a DataFlowLogger whose only sink is a buffer.

    ``DataFlowLogger`` installs its sink on whatever ``sys.stderr`` names at the
    time, and ``set_level`` resolves it again, so patching ``sys.stderr`` puts
    both sinks in the buffer. The level change is then observed through
    production code rather than through a second sink added by the test, which
    would keep loguru's global ``min_level`` low and hide the filtering.

    The patch must be applied from the test body, which is why this is a factory
    rather than a ready-made logger: pytest reassigns ``sys.stderr`` when it
    resumes global capture at the start of the call phase, undoing anything a
    fixture patched during setup.

    Yields:
        A callable returning the installed logger and the buffer it writes to.
    """

    def build() -> tuple[DataFlowLogger, io.StringIO]:
        buffer = io.StringIO()
        monkeypatch.setattr(sys, "stderr", buffer)
        instance = DataFlowLogger()
        monkeypatch.setattr(logger_module, "_logger_instance", instance)
        return instance, buffer

    try:
        yield build
    finally:
        loguru_logger.remove()


def _main_source() -> str:
    """Read ``slither/__main__.py`` without importing or executing it.

    Returns:
        The source text of the CLI entry point module.
    """
    return (Path(slither.__file__).parent / "__main__.py").read_text(encoding="utf-8")


def test_configure_logger_applies_requested_level_through_set_level(
    build_buffered_logger: Callable[[], tuple[DataFlowLogger, io.StringIO]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``configure_logger(log_level=...)`` reaches ``set_level`` on the singleton."""
    instance, _ = build_buffered_logger()
    calls: list[tuple[DataFlowLogger, str]] = []

    def record_level(self: DataFlowLogger, level: str) -> None:
        calls.append((self, level))

    monkeypatch.setattr(DataFlowLogger, "set_level", record_level)

    assert configure_logger() is instance
    assert calls == [], "configure_logger() with no level must not touch the sink"

    assert configure_logger(log_level="ERROR") is instance
    assert calls == [(instance, "ERROR")]


def test_set_level_replaces_the_sink_and_filters_lower_severity(
    build_buffered_logger: Callable[[], tuple[DataFlowLogger, io.StringIO]],
) -> None:
    """After ``set_level("ERROR")`` an info record is dropped and an error record is not.

    A leftover INFO sink would still emit ``info-after``, so this also catches a
    ``set_level`` that adds a sink without removing the previous one.
    """
    instance, buffer = build_buffered_logger()

    instance.info("info-before")
    assert "info-before" in buffer.getvalue()

    instance.set_level("ERROR")
    instance.info("info-after")
    instance.error("error-after")

    output = buffer.getvalue()
    assert instance.log_level == "ERROR"
    assert "info-after" not in output, "the INFO-level sink survived set_level"
    assert "error-after" in output, "set_level left the logger with no working sink"


def test_cli_flag_is_wired_to_configure_logger() -> None:
    """``slither/__main__.py`` feeds the parsed flag value into ``configure_logger``."""
    source = _main_source()
    tree = ast.parse(source)

    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == LOGGER_PACKAGE
        for alias in node.names
    }
    assert "configure_logger" in imported, f"__main__ no longer imports it from {LOGGER_PACKAGE}"

    wired = [
        keyword
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        if node.func.id == "configure_logger"
        for keyword in node.keywords
        if keyword.arg == "log_level"
        and isinstance(keyword.value, ast.Attribute)
        and keyword.value.attr == CLI_DEST
    ]
    assert wired, f"__main__ never calls configure_logger(log_level=args.{CLI_DEST})"

    # An exact match, not a substring: argparse accepts unambiguous prefixes, so a renamed
    # option keeps answering to the old spelling and a substring check never notices.
    declared = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == CLI_FLAG
    ]
    assert declared, f"no add_argument declares {CLI_FLAG} exactly, so args.{CLI_DEST} is unset"

    dest = next(
        (kw.value for kw in declared[0].keywords if kw.arg == "dest"),
        None,
    )
    assert isinstance(dest, ast.Constant) and dest.value == CLI_DEST
