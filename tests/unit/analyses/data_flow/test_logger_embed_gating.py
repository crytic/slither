"""Regression guard: logging must never open an interactive session on its own.

:class:`DataFlowLogger` can drop the caller into an IPython ``embed()`` session
for post-mortem debugging. That used to be the *default* for :meth:`error`,
:meth:`critical` and :meth:`exception`, gated only by ``enable_ipython_embed``
-- which itself defaulted to ``True``. A single logged error inside an automated
run (CI, or an MCP server whose stdin is not a terminal) therefore parked the
process on an interactive prompt with no way to make progress.

The hardened contract has two halves, and both are pinned here:

1. Every logging method defaults ``embed_on_error`` to ``False``, so embedding
   is opt-in per call site rather than the fallback behaviour of an error.
2. Even an explicit ``embed_on_error=True`` is ignored unless the operator opted
   in with ``SLITHER_DATA_FLOW_DEBUG=1``, which is read at call time.

Global state: the logger is process-wide, and ``DataFlowLogger.__init__`` calls
loguru's ``logger.remove()``, which drops every sink in the process. The
``embedding_logger`` fixture below therefore restores loguru's sinks and the
module-level singleton on teardown. No test here asserts on log output, so the
fixture keeps loguru sink-free for the duration of the test body: with no
handlers installed loguru returns from ``_log()`` before formatting anything,
which keeps the deliberately-triggered error records off the pytest report while
leaving the embed decision -- the thing under test -- untouched.
"""

from __future__ import annotations

import inspect
import sys
from collections.abc import Iterator
from typing import Any

import pytest
from loguru import logger as loguru_logger

from slither.analyses.data_flow.logger import logger as logger_module
from slither.analyses.data_flow.logger.logger import DataFlowLogger


# The operator-facing opt-in. Spelled out rather than imported from the module so
# that a rename shows up as one focused failure (see the constant test below)
# instead of silently rewriting what every other test in this file checks.
INTERACTIVE_DEBUG_ENV_VAR = "SLITHER_DATA_FLOW_DEBUG"

# Every public logging method that accepts embed_on_error.
EMBEDDING_METHODS = (
    "debug",
    "info",
    "warning",
    "error",
    "error_and_raise",
    "critical",
    "exception",
)

MESSAGE = "boom"


def _log_with(instance: DataFlowLogger, method_name: str, **options: Any) -> None:
    """Invoke one logging method uniformly, absorbing error_and_raise's exception.

    Args:
        instance: Logger under test
        method_name: Name of the method to call, one of EMBEDDING_METHODS
        **options: Extra keyword arguments forwarded to the method, e.g.
            ``embed_on_error=True``
    """
    if method_name == "error_and_raise":
        with pytest.raises(RuntimeError):
            instance.error_and_raise(MESSAGE, RuntimeError, **options)
        return
    getattr(instance, method_name)(MESSAGE, **options)


def _loguru_sink_count() -> int:
    """Count the sinks currently installed on the process-wide loguru logger.

    loguru exposes no public accessor for its handler table, so this reads
    ``_core.handlers``. The fixture needs it to decide whether to reinstate a
    default sink on teardown: a session that deliberately silenced loguru (see
    ``tests/e2e/data_flow/conftest.py``) must stay silent.

    Returns:
        Number of installed loguru handlers
    """
    return len(loguru_logger._core.handlers)


@pytest.fixture
def embedding_logger(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[DataFlowLogger, list[dict[str, Any]]]]:
    """Build a logger that is allowed to embed, with ``embed()`` replaced by a spy.

    ``enable_ipython_embed`` is computed in ``__init__`` as ``arg and
    IPYTHON_AVAILABLE``, so ``IPYTHON_AVAILABLE`` is patched before construction.
    That makes the environment variable the only remaining gate, which is exactly
    what these tests exercise -- and it keeps the suite independent of whether
    IPython happens to be installed.

    Yields:
        The logger and the list of keyword-argument dicts that ``embed()`` was
        called with (empty when embedding was correctly suppressed)
    """
    calls: list[dict[str, Any]] = []

    def _record_embed(*_args: Any, **kwargs: Any) -> None:
        calls.append(kwargs)

    monkeypatch.setattr(logger_module, "IPYTHON_AVAILABLE", True)
    monkeypatch.setattr(logger_module, "embed", _record_embed)
    # A developer with the opt-in exported must not change the outcome; tests
    # that need it set it explicitly.
    monkeypatch.delenv(INTERACTIVE_DEBUG_ENV_VAR, raising=False)

    had_sinks = _loguru_sink_count() > 0
    saved_instance = logger_module._logger_instance

    instance = DataFlowLogger(enable_ipython_embed=True, log_level="DEBUG")
    loguru_logger.remove()  # drop the colorized stderr sink __init__ just installed

    try:
        yield instance, calls
    finally:
        loguru_logger.remove()
        # Constructing a DataFlowLogger does not register itself today; restoring
        # the singleton keeps that an implementation detail rather than something
        # this fixture silently depends on.
        logger_module._logger_instance = saved_instance
        if had_sinks:
            loguru_logger.add(sys.stderr)


def test_env_var_constant_matches_documented_name() -> None:
    """The opt-in variable operators set is the one the module reads."""
    assert logger_module.INTERACTIVE_DEBUG_ENV_VAR == INTERACTIVE_DEBUG_ENV_VAR


@pytest.mark.parametrize("method_name", EMBEDDING_METHODS)
def test_embed_on_error_defaults_to_false(method_name: str) -> None:
    """No logging method may request an interactive session unless asked to.

    Args:
        method_name: Logging method under inspection
    """
    parameter = inspect.signature(getattr(DataFlowLogger, method_name)).parameters["embed_on_error"]

    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is False, (
        f"DataFlowLogger.{method_name} defaults embed_on_error to "
        f"{parameter.default!r}; logging must never opt a caller into an "
        "interactive IPython session it did not ask for."
    )


@pytest.mark.parametrize("method_name", EMBEDDING_METHODS)
def test_plain_call_does_not_embed_even_with_the_opt_in_set(
    embedding_logger: tuple[DataFlowLogger, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
) -> None:
    """An ordinary log call never embeds, even for an operator who opted in.

    This is the CI-hang scenario end to end: the environment allows embedding and
    the logger allows embedding, but the call site did not ask for it.

    Args:
        embedding_logger: Logger and embed-call recorder
        monkeypatch: pytest environment patcher
        method_name: Logging method under test
    """
    instance, calls = embedding_logger
    monkeypatch.setenv(INTERACTIVE_DEBUG_ENV_VAR, "1")

    _log_with(instance, method_name)

    assert calls == [], (
        f"DataFlowLogger.{method_name} opened an IPython session for a call that "
        "never requested one"
    )


@pytest.mark.parametrize("method_name", EMBEDDING_METHODS)
def test_explicit_request_is_ignored_without_the_opt_in(
    embedding_logger: tuple[DataFlowLogger, list[dict[str, Any]]],
    method_name: str,
) -> None:
    """``embed_on_error=True`` is inert while SLITHER_DATA_FLOW_DEBUG is unset.

    Args:
        embedding_logger: Logger and embed-call recorder (opt-in removed)
        method_name: Logging method under test
    """
    instance, calls = embedding_logger

    _log_with(instance, method_name, embed_on_error=True)

    assert calls == [], (
        f"DataFlowLogger.{method_name} honoured embed_on_error=True without the "
        f"{INTERACTIVE_DEBUG_ENV_VAR}=1 opt-in"
    )


@pytest.mark.parametrize("value", ["0", "", "true", "TRUE", "yes", "2"])
def test_explicit_request_is_ignored_for_non_exact_opt_in_values(
    embedding_logger: tuple[DataFlowLogger, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
    value: str,
) -> None:
    """Only the exact string "1" enables embedding; truthy look-alikes do not.

    Args:
        embedding_logger: Logger and embed-call recorder
        monkeypatch: pytest environment patcher
        value: Environment value that must not enable embedding
    """
    instance, calls = embedding_logger
    monkeypatch.setenv(INTERACTIVE_DEBUG_ENV_VAR, value)

    instance.error(MESSAGE, embed_on_error=True)

    assert calls == [], (
        f'{INTERACTIVE_DEBUG_ENV_VAR}={value!r} enabled interactive debugging; only "1" may'
    )


@pytest.mark.parametrize("method_name", EMBEDDING_METHODS)
def test_explicit_request_embeds_once_the_operator_opts_in(
    embedding_logger: tuple[DataFlowLogger, list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
    method_name: str,
) -> None:
    """The escape hatch still works, and the env var is read at call time.

    The fixture builds the logger before this test sets the variable, so passing
    proves the opt-in is consulted per call rather than captured in ``__init__``.
    It also proves the suppression asserted above is real rather than a spy that
    could never fire.

    Args:
        embedding_logger: Logger and embed-call recorder
        monkeypatch: pytest environment patcher
        method_name: Logging method under test
    """
    instance, calls = embedding_logger
    monkeypatch.setenv(INTERACTIVE_DEBUG_ENV_VAR, "1")

    _log_with(instance, method_name, embed_on_error=True)

    assert len(calls) == 1, f"expected exactly one embed session, got {len(calls)}"
    assert calls[0]["user_ns"]["message"] == MESSAGE
