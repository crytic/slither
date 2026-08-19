"""Regression guard: the data-flow end-to-end tests emit no log noise.

The rounding end-to-end tests used to dump log lines into the pytest report:
the analyses warn on every rounding inconsistency, and these tests provoke them
on purpose. ``tests/e2e/data_flow/conftest.py`` now installs an autouse,
session-scoped ``silence_data_flow_logging`` fixture. This module lives in that
subtree, so the fixture applies to it and the tests below only pass while it is
doing its job:

* a warning logged from a data-flow module reaches neither stderr nor the root
  handlers;
* a logger outside the ``DataFlow`` tree is untouched, which is what makes the
  silence above evidence rather than an empty assertion;
* both halves of the fixture are load-bearing, checked by driving its body
  against handler and propagation state it did not install;
* the fixture is active without being requested (autouse) and is declared at
  session scope.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Callable, Iterator
from typing import Any

import pytest

from slither.analyses.data_flow.engine import engine as engine_module

CONFTEST_MODULE = "tests.e2e.data_flow.conftest"
SILENCE_FIXTURE = "silence_data_flow_logging"
DATA_FLOW_LOGGER_NAME = "DataFlow"
PROBE_MESSAGE = "data-flow logging guard probe"


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


def test_a_data_flow_warning_reaches_neither_stderr_nor_the_root_handlers(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The level at which the analyses actually log produces no output.

    WARNING is the interesting level: it clears the default root threshold, so
    without the fixture ``logging.lastResort`` would print it to stderr.
    """
    root_records: list[logging.LogRecord] = []
    root_handler = logging.Handler()
    root_handler.emit = root_records.append  # type: ignore[method-assign]
    logging.getLogger().addHandler(root_handler)
    try:
        engine_module.logger.warning(PROBE_MESSAGE)
    finally:
        logging.getLogger().removeHandler(root_handler)

    assert capsys.readouterr().err == "", "data-flow logging leaked to stderr"
    assert root_records == [], "data-flow logging reached the root handlers"


def test_a_logger_outside_the_data_flow_tree_still_reaches_stderr() -> None:
    """The silence above is scoped, not a capture that never sees logging.

    Without this, a broken probe or a swallowed handler would look identical to
    a working fixture.
    """
    other_records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = other_records.append  # type: ignore[method-assign]
    logging.getLogger().addHandler(handler)
    try:
        logging.getLogger("Slither").warning(PROBE_MESSAGE)
    finally:
        logging.getLogger().removeHandler(handler)

    assert len(other_records) == 1, "the probe never reached the root handlers"


def test_both_halves_of_the_fixture_are_applied() -> None:
    """Running the fixture's body silences a logger it did not prepare.

    The tests above cannot tell the handler half from the propagation half, so
    the body is driven here against state it did not install.
    """
    conftest = importlib.import_module(CONFTEST_MODULE)
    fixture_body = _fixture_body(getattr(conftest, SILENCE_FIXTURE))
    logger = logging.getLogger(DATA_FLOW_LOGGER_NAME)
    handlers_before = list(logger.handlers)
    logger.handlers = []
    logger.propagate = True

    generator = fixture_body()
    next(generator)
    try:
        assert logger.handlers, "no handler: WARNING records would hit lastResort"
        assert logger.propagate is False, "records would still reach the root handlers"
    finally:
        for _ in generator:
            pass
        # The teardown restores what the body changed; put the session's silence back.
        logger.handlers = handlers_before
        logger.propagate = False


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
    assert marker.scope == "session", "a narrower scope re-runs the setup for every test"
    assert marker.autouse is True, "tests would have to request the fixture by hand"
