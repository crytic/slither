"""Regression guard: the data-flow end-to-end tests emit no loguru noise.

The rounding end-to-end tests used to dump colorized loguru INFO lines into the
pytest report: the analyses log through a stderr sink that nothing removed and
that no test asserted on. ``tests/e2e/data_flow/conftest.py`` now installs an
autouse, session-scoped ``silence_data_flow_logging`` fixture which drops every
loguru sink and disables records originating in the ``slither`` package for this
whole subtree. This module lives in that subtree, so the fixture applies to it
and the tests below only pass while it is doing its job:

* a real ``get_logger()`` call made from a data-flow module reaches no stderr,
  even when a sink is present, because ``slither`` records are disabled;
* a record from outside the ``slither`` package still reaches the capture, which
  is what makes the silence above evidence rather than an empty assertion;
* no loguru sink survives the fixture at all, which is its other half;
* the fixture is active without being requested (autouse) and is declared at
  session scope.

Global-state note: the loguru logger is process-wide, and
``DataFlowLogger.__init__`` calls ``loguru.logger.remove()``, dropping every sink
in the process. ``rebuilt_data_flow_logger`` therefore removes the sink it causes
to be installed and lets ``monkeypatch`` put the previous singleton back, ending
in the sink-free state that the session fixture installs.
"""

from __future__ import annotations

import importlib
import io
import types
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from loguru import logger as loguru_logger

from slither.analyses.data_flow.engine import engine as engine_module
from slither.analyses.data_flow.logger import DataFlowLogger, get_logger
from slither.analyses.data_flow.logger import logger as logger_module


CONFTEST_MODULE = "tests.e2e.data_flow.conftest"
SILENCE_FIXTURE = "silence_data_flow_logging"
PROBE_MESSAGE = "data-flow logging guard probe"


@pytest.fixture
def rebuilt_data_flow_logger(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Make ``get_logger()`` build the production logger inside the test body.

    ``DataFlowLogger`` installs its sink on whatever ``sys.stderr`` is bound to at
    construction time. The singleton is usually built while a test module is
    imported, so its sink points at a stream ``capsys`` cannot see; dropping the
    singleton first means the sink under observation is the real one, attached to
    the stream ``capsys`` owns.

    Yields:
        None, after clearing the module-level singleton.
    """
    monkeypatch.setattr(logger_module, "_logger_instance", None)
    try:
        yield
    finally:
        loguru_logger.remove()


def _emit_info(data_flow_logger: DataFlowLogger, message: str) -> None:
    """Log ``message`` at INFO, standing in for an analysis call site."""
    data_flow_logger.info(message)


def _log_info_from_data_flow_module(data_flow_logger: DataFlowLogger, message: str) -> None:
    """Emit an INFO record that originates inside the ``slither`` package.

    ``logger.disable("slither")`` filters on the module a record comes from, and
    the ``DataFlowLogger`` methods use ``opt(depth=1)`` so that module is their
    caller's, not the logger's. Running the probe with the engine module's
    globals therefore produces exactly the record shape the analyses produce.

    Args:
        data_flow_logger: The process-wide data-flow logger.
        message: Text to log.
    """
    probe = types.FunctionType(_emit_info.__code__, engine_module.__dict__)
    probe(data_flow_logger, message)


def _fixture_body(fixture: object) -> Callable[[], Iterator[None]]:
    """Return the generator function that ``@pytest.fixture`` wrapped.

    Args:
        fixture: Object bound to the fixture name in the conftest module.

    Returns:
        The undecorated fixture function.

    Raises:
        AssertionError: If no wrapped function can be recovered.
    """
    for attribute in ("_fixture_function", "__wrapped__"):
        function = getattr(fixture, attribute, None)
        if function is not None:
            return function
    raise AssertionError(f"{fixture!r} does not wrap a fixture function")


def _fixture_marker(fixture: object) -> Any:
    """Return the ``@pytest.fixture`` marker attached to a fixture object.

    pytest 8.4 moved the marker onto the ``FixtureFunctionDefinition`` wrapper,
    so the older attribute name is tried as well.

    Args:
        fixture: Object bound to the fixture name in the conftest module.

    Returns:
        The marker carrying ``scope`` and ``autouse``.

    Raises:
        AssertionError: If the object is not a pytest fixture.
    """
    for attribute in ("_fixture_function_marker", "_pytestfixturefunction"):
        marker = getattr(fixture, attribute, None)
        if marker is not None:
            return marker
    raise AssertionError(f"{fixture!r} is not a pytest fixture")


def test_data_flow_call_site_writes_nothing_to_stderr(
    capsys: pytest.CaptureFixture[str],
    rebuilt_data_flow_logger: None,
) -> None:
    """A data-flow log call produces no stderr output while the fixture is active."""
    data_flow_logger = get_logger()

    _log_info_from_data_flow_module(data_flow_logger, PROBE_MESSAGE)

    captured = capsys.readouterr()
    assert captured.err == "", f"data-flow logging leaked to stderr: {captured.err!r}"


def test_capture_sees_a_record_from_outside_the_slither_package(
    capsys: pytest.CaptureFixture[str],
    rebuilt_data_flow_logger: None,
) -> None:
    """The same logger does emit for a caller the fixture is not silencing.

    Without this, the silence asserted above could just as well come from a probe
    that never reached a sink, or from a capture that never sees loguru at all.
    """
    data_flow_logger = get_logger()

    data_flow_logger.info(PROBE_MESSAGE)

    captured = capsys.readouterr()
    assert PROBE_MESSAGE in captured.err, "the probe never reached the sink"


def test_the_fixture_removes_every_sink_not_only_slither_records() -> None:
    """The fixture drops sinks outright, on top of disabling ``slither`` records.

    Both halves are load-bearing, and the tests above exercise only the
    ``disable`` half: they rebuild the singleton, which installs a sink of its
    own and whose teardown drops every sink again. Live handler state is
    therefore worthless by the time this runs, so the conftest fixture's own body
    is driven here against a sink it did not install.
    """
    conftest = importlib.import_module(CONFTEST_MODULE)
    fixture_body = _fixture_body(getattr(conftest, SILENCE_FIXTURE))
    loguru_logger.add(io.StringIO())

    generator = fixture_body()
    next(generator)
    try:
        assert not loguru_logger._core.handlers, "the fixture left a sink writing"
    finally:
        for _ in generator:
            pass
        # The teardown half re-enables the package: put the session's silence back.
        loguru_logger.remove()
        loguru_logger.disable("slither")


def test_silence_fixture_is_active_without_being_requested(
    request: pytest.FixtureRequest,
) -> None:
    """Every test in this directory gets the fixture without asking for it."""
    assert SILENCE_FIXTURE in request.fixturenames


def test_silence_fixture_is_session_scoped_and_autouse() -> None:
    """The conftest declares the fixture as autouse for the whole session."""
    conftest = importlib.import_module(CONFTEST_MODULE)
    fixture = getattr(conftest, SILENCE_FIXTURE, None)
    assert fixture is not None, f"{CONFTEST_MODULE} no longer defines {SILENCE_FIXTURE}"

    marker = _fixture_marker(fixture)
    assert marker.scope == "session", "a narrower scope re-runs the removal for every test"
    assert marker.autouse is True, "tests would have to request the fixture by hand"
