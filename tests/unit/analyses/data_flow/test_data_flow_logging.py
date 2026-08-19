"""Regression guards for data-flow logging.

The data-flow analyses used to log through loguru, a second logging system
alongside the stdlib tree that the rest of Slither configures. They now use
``logging.getLogger("DataFlow")`` like every other Slither subsystem. These
tests pin that:

* every data-flow module logs through the one shared ``DataFlow`` logger;
* nothing in the shipped package imports loguru, and it is not a dependency;
* arguments are passed to the logger rather than interpolated by the call site,
  so a record dropped by the level costs nothing to produce.

The record collector below attaches to the ``DataFlow`` logger directly instead
of using ``caplog``, which reads from the root logger: the end-to-end data-flow
suite sets ``propagate = False`` for the whole session, so anything relying on
propagation here would break depending on test order.
"""

from __future__ import annotations

import importlib
import logging
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest

import slither

LOGGER_NAME = "DataFlow"

DATA_FLOW_MODULES = [
    "slither.analyses.data_flow.engine.engine",
    "slither.analyses.data_flow.engine.direction",
    "slither.analyses.data_flow.registry.catalog",
    "slither.analyses.data_flow.analyses.rounding.analysis.analysis",
    "slither.analyses.data_flow.analyses.rounding.analysis.domain",
    "slither.analyses.data_flow.analyses.rounding.output.annotate",
    "slither.analyses.data_flow.analyses.rounding.operations.registry",
    "slither.analyses.data_flow.analyses.rounding.operations.interprocedural",
    "slither.analyses.data_flow.analyses.rounding.operations.tag_operations",
    "slither.analyses.data_flow.analyses.rounding.operations.binary.handler",
    "slither.analyses.data_flow.analyses.rounding.operations.binary.division",
    "slither.analyses.data_flow.analyses.rounding.operations.binary.addition",
    "slither.analyses.data_flow.analyses.rounding.operations.binary.multiplication",
    "slither.analyses.data_flow.analyses.rounding.operations.binary.subtraction",
]

SLITHER_ROOT = Path(slither.__file__).parent
PROJECT_ROOT = SLITHER_ROOT.parent


class _RecordCollector(logging.Handler):
    """Handler that keeps every record it is given."""

    def __init__(self) -> None:
        super().__init__(level=logging.NOTSET)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


class _Tripwire:
    """Argument that reports whether anything asked for its text."""

    def __init__(self) -> None:
        self.rendered = False

    def __str__(self) -> str:
        self.rendered = True
        return "rendered"


@pytest.fixture(name="collector")
def fixture_collector() -> Iterator[_RecordCollector]:
    """Attach a collecting handler to the ``DataFlow`` logger.

    Yields:
        The handler, whose ``records`` list holds everything logged.
    """
    logger = logging.getLogger(LOGGER_NAME)
    previous_level = logger.level
    handler = _RecordCollector()
    logger.addHandler(handler)
    try:
        yield handler
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


@pytest.mark.parametrize("module_name", DATA_FLOW_MODULES)
def test_module_logs_through_the_shared_stdlib_logger(module_name: str) -> None:
    """Each data-flow module binds the one ``DataFlow`` logger, not its own."""
    module = importlib.import_module(module_name)

    assert hasattr(module, "logger"), f"{module_name} defines no module logger"
    assert module.logger is logging.getLogger(LOGGER_NAME)
    assert isinstance(module.logger, logging.Logger)


def test_the_analysis_does_not_carry_a_private_logger() -> None:
    """``RoundingAnalysis`` no longer hands a logger object to its handlers.

    Operation handlers used to reach back through ``self.analysis._logger``,
    which is what a second logging system forced them to do.
    """
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )

    analysis = RoundingAnalysis()

    assert not hasattr(analysis, "_logger")


def test_no_shipped_module_imports_loguru() -> None:
    """loguru is gone from the package source."""
    offenders = [
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in SLITHER_ROOT.rglob("*.py")
        if "loguru" in path.read_text(encoding="utf-8")
    ]

    assert offenders == [], f"loguru is still imported by: {offenders}"


def test_loguru_is_not_a_declared_dependency() -> None:
    """loguru is gone from the project dependencies."""
    manifest = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = manifest["project"]["dependencies"]

    assert not [name for name in dependencies if "loguru" in name]


def test_arguments_are_not_interpolated_for_a_dropped_record(
    collector: _RecordCollector,
) -> None:
    """A message below the level costs nothing: its arguments stay untouched.

    This is the property that pre-formatting at the call site would lose, which
    matters because the debug calls sit inside the fixpoint loop.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    tripwire = _Tripwire()

    logger.debug("resolved via %s", tripwire)

    assert tripwire.rendered is False
    assert collector.records == []


def test_arguments_are_interpolated_for_an_emitted_record(
    collector: _RecordCollector,
) -> None:
    """A record that passes the level still renders its arguments."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)
    tripwire = _Tripwire()

    logger.debug("resolved via %s", tripwire)

    assert len(collector.records) == 1
    assert collector.records[0].getMessage() == "resolved via rendered"
    assert tripwire.rendered is True


def test_records_are_attributed_to_the_calling_module(
    collector: _RecordCollector,
) -> None:
    """Logging straight to the stdlib logger keeps the caller's identity.

    A wrapper class in between would report its own file and function here.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.WARNING)

    logger.warning("probe")

    assert len(collector.records) == 1
    record = collector.records[0]
    assert record.name == LOGGER_NAME
    assert record.funcName == "test_records_are_attributed_to_the_calling_module"
    assert Path(record.pathname).name == "test_data_flow_logging.py"
