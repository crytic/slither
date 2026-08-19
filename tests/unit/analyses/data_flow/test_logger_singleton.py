"""Regression guard: one data-flow logger, reconfigured explicitly.

The data-flow logger used to keep two caches of the same singleton: the
module-level ``_logger_instance`` and a ``DataFlowLogger._instance`` populated
by a ``DataFlowLogger.get_logger()`` classmethod. Both were filled by the first
caller and both then ignored the ``enable_ipython_embed`` / ``log_level``
arguments of every later call. ``registry/catalog.py`` builds the logger at
import time, so the rounding analysis asking for
``get_logger(enable_ipython_embed=False)`` was silently answered with whatever
catalog had already created, and the argument was dropped without a word.

The fix collapses the two caches into one and moves configuration out of the
lookup: :func:`get_logger` takes no arguments, and :func:`configure_logger`
applies each setting it is given to the live instance. These tests pin both
halves — a configured ``get_logger()`` call is now a loud ``TypeError`` instead
of a silent no-op, and ``configure_logger`` mutates the object other callers
already hold rather than handing back a differently configured one.

Global state:
    The logger is process-wide, and :class:`DataFlowLogger`'s constructor calls
    loguru's ``logger.remove()``, which drops every sink in the process. The
    autouse fixture below hands each test a fresh singleton and puts the
    previous one back afterwards. Sinks that existed before a test built an
    instance cannot be recreated — the constructor already destroyed them — so
    the fixture instead guarantees the test leaves no sink of its own behind,
    the same sink-free state ``tests/e2e/data_flow/conftest.py`` establishes for
    the whole session.
"""

from __future__ import annotations

import contextlib
from collections.abc import Iterator

import pytest
from loguru import logger as loguru_logger

from slither.analyses.data_flow.logger import (
    DataFlowLogger,
    configure_logger,
    get_logger,
)
from slither.analyses.data_flow.logger import logger as logger_module


@pytest.fixture(autouse=True)
def isolated_data_flow_logger() -> Iterator[None]:
    """Give each test a fresh singleton and leave no sink behind.

    Restores the previously cached instance on the way out. That instance's own
    stderr sink is gone by then — building a logger removes every sink — but it
    stays usable: ``set_level`` tolerates an already-removed handler id.

    Yields:
        None, once the module-level cache has been cleared.
    """
    saved_instance = logger_module._logger_instance
    logger_module._logger_instance = None
    try:
        yield
    finally:
        built_instance = logger_module._logger_instance
        logger_module._logger_instance = saved_instance
        if built_instance is not None:
            loguru_logger.remove()


def test_get_logger_returns_the_one_module_level_instance() -> None:
    """Repeated lookups hand back the same object, and it is the module cache."""
    first = get_logger()
    second = get_logger()

    assert isinstance(first, DataFlowLogger)
    assert second is first
    assert logger_module._logger_instance is first


@pytest.mark.parametrize(
    "kwargs",
    [
        pytest.param({"enable_ipython_embed": False}, id="enable_ipython_embed"),
        pytest.param({"log_level": "DEBUG"}, id="log_level"),
        pytest.param({"enable_ipython_embed": False, "log_level": "DEBUG"}, id="both"),
    ],
)
def test_get_logger_rejects_configuration_arguments(kwargs: dict[str, object]) -> None:
    """Configuring through the lookup is a hard error, not a silently dropped request."""
    with pytest.raises(TypeError):
        get_logger(**kwargs)

    assert logger_module._logger_instance is None, (
        "the rejected call must not have built a logger; the old signature accepted "
        "these arguments and then ignored them"
    )


def test_get_logger_rejects_positional_arguments() -> None:
    """The old signature's leading positional parameter is gone too."""
    with pytest.raises(TypeError):
        get_logger(False)

    assert logger_module._logger_instance is None


def test_dataflow_logger_class_keeps_no_second_cache() -> None:
    """The class-level lookup and its private cache are both gone.

    ``DataFlowLogger.get_logger()`` used to stash the instance on
    ``cls._instance``, a second cache that the module-level one shadowed.
    Obtaining the logger through the supported entry point first is what makes
    this meaningful: that call is exactly what used to populate the class
    attribute.
    """
    get_logger()

    assert not hasattr(DataFlowLogger, "get_logger"), (
        "DataFlowLogger.get_logger is a second, configurable entry point; "
        "the module-level get_logger() is the only supported lookup"
    )
    assert not hasattr(DataFlowLogger, "_instance"), (
        "DataFlowLogger._instance is a second cache of the singleton; "
        "logger._logger_instance is the only one"
    )


def test_configure_logger_without_settings_returns_the_singleton() -> None:
    """With every setting left at ``None`` the call is a plain lookup."""
    created = configure_logger()

    assert isinstance(created, DataFlowLogger)
    assert created is logger_module._logger_instance
    assert created is get_logger()


def test_configure_logger_applies_log_level_to_the_live_instance() -> None:
    """A new level lands on the object earlier callers already hold."""
    existing = get_logger()
    baseline = existing.log_level
    assert baseline != "WARNING", "the test level must differ from the starting one"

    reconfigured = configure_logger(log_level="WARNING")

    assert reconfigured is existing, "configure_logger must reconfigure, not replace"
    assert existing.log_level == "WARNING", (
        "the requested level was dropped; callers holding a reference from before "
        "the call would keep the stale one"
    )
    assert logger_module._logger_instance is existing


def test_configure_logger_applies_ipython_embed_to_the_live_instance() -> None:
    """The embed flag is applied in both directions, on the same object.

    ``enable_ipython_embed`` is gated by IPython being importable, so the
    enabling case is asserted against the module's own ``IPYTHON_AVAILABLE``
    rather than a hard ``True``. The disabling case sets the flag directly
    first, so it is a real transition even where IPython is missing.
    """
    existing = get_logger()

    enabled = configure_logger(enable_ipython_embed=True)

    assert enabled is existing
    assert existing.enable_ipython_embed is logger_module.IPYTHON_AVAILABLE

    existing.enable_ipython_embed = True
    disabled = configure_logger(enable_ipython_embed=False)

    assert disabled is existing
    assert existing.enable_ipython_embed is False, (
        "the rounding analysis asks for embedding to be off; that request must win "
        "over whatever the first importer configured"
    )


def test_configure_logger_leaves_omitted_settings_alone() -> None:
    """Passing one setting does not reset the other."""
    existing = configure_logger(log_level="ERROR")
    existing.enable_ipython_embed = True

    configure_logger(log_level="DEBUG")

    assert existing.log_level == "DEBUG"
    assert existing.enable_ipython_embed is True, "an omitted setting must not be reset"


def test_configure_logger_keeps_foreign_sinks_and_the_instance_usable() -> None:
    """Reconfiguring reaches loguru without tearing down unrelated sinks.

    The capture sink is added *after* the singleton is built, because building
    it removes every sink in the process. It then stands in for any other sink
    the host application installed: reconfiguring the data-flow logger must
    leave it in place, and messages must still reach it.

    This says nothing about the stderr sink's own level — levels are per-sink
    state, and the capture sink is deliberately added at DEBUG so it sees the
    record either way.
    """
    instance = get_logger()
    records: list[str] = []
    sink_id = loguru_logger.add(records.append, format="{message}", level="DEBUG")
    try:
        reconfigured = configure_logger(log_level="WARNING")
        reconfigured.warning("reconfigured and still logging")
    finally:
        with contextlib.suppress(ValueError):
            loguru_logger.remove(sink_id)

    assert reconfigured is instance
    assert any("reconfigured and still logging" in record for record in records), (
        "the message never reached the foreign sink: reconfiguration either removed "
        f"it or silenced the logger; captured {records!r}"
    )
