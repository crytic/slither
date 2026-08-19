"""Regression tests for the ``--data-flow-log-level`` command line flag.

Data-flow analyses log through loguru, which is independent of the stdlib
logging tree that ``--debug`` configures. Before the flag existed the loguru
sink was pinned at INFO for the whole process, so a user had no way to quiet
or to deepen data-flow output. These tests pin both halves of the contract:

* ``parse_args`` exposes the flag as ``args.data_flow_log_level``, defaulting
  to ``"INFO"`` and restricted to the five loguru level names.
* ``main_impl`` forwards the parsed value to ``configure_logger``.

Nothing here touches the real loguru state: the wiring test replaces
``configure_logger`` with a recorder, so no sink is added or removed.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from slither import __main__ as slither_main
from slither.utils.colors import Colors
from slither.utils.output import OutputConfig

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _StopAfterConfigure(Exception):
    """Raised by the ``configure_logger`` stub to halt ``main_impl`` early."""


@pytest.fixture(name="isolated_cwd")
def fixture_isolated_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Run argument parsing from an empty directory.

    ``parse_args`` ends with ``read_config_file``, which picks up a
    ``slither.config.json`` sitting in the current directory. Parsing from a
    tmp_path keeps the assertions independent of where pytest was invoked.
    """
    monkeypatch.chdir(tmp_path)
    yield


@pytest.fixture(name="restored_cli_globals")
def fixture_restored_cli_globals(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Undo the process-wide state ``main_impl`` sets before it reaches the logger.

    ``main_impl`` toggles output colorization, the detector-message location
    flag, and the level of the stdlib "Slither" logger. Each is global, so it
    is snapshotted here and restored after the test.
    """
    monkeypatch.setattr(Colors, "COLORIZATION_ENABLED", Colors.COLORIZATION_ENABLED)
    monkeypatch.setattr(OutputConfig, "EXCLUDE_LOCATION", OutputConfig.EXCLUDE_LOCATION)
    slither_logger = logging.getLogger("Slither")
    previous_level = slither_logger.level
    yield
    slither_logger.setLevel(previous_level)


def _parse(monkeypatch: pytest.MonkeyPatch, *flags: str) -> argparse.Namespace:
    """Parse a bare ``slither x.sol`` command line plus the given flags.

    Args:
        monkeypatch: Fixture used to swap ``sys.argv``
        *flags: Extra command line arguments to append

    Returns:
        The populated argparse namespace
    """
    monkeypatch.setattr(sys, "argv", ["slither", "x.sol", *flags])
    return slither_main.parse_args([], [], [])


def test_log_level_defaults_to_info(monkeypatch: pytest.MonkeyPatch, isolated_cwd: None) -> None:
    """An unadorned command line still exposes the flag, defaulting to INFO."""
    args = _parse(monkeypatch)

    assert args.data_flow_log_level == "INFO"


@pytest.mark.parametrize("level", LOG_LEVELS)
def test_log_level_flag_is_parsed(
    level: str, monkeypatch: pytest.MonkeyPatch, isolated_cwd: None
) -> None:
    """Every accepted level round-trips into ``args.data_flow_log_level``."""
    args = _parse(monkeypatch, "--data-flow-log-level", level)

    assert args.data_flow_log_level == level


def test_unknown_log_level_is_rejected_as_an_invalid_choice(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    isolated_cwd: None,
) -> None:
    """A level outside the loguru names fails argparse validation.

    The "invalid choice" wording matters: an argparse run that does not know
    the flag at all also exits, but complains about an unrecognized argument
    instead of validating the value.
    """
    with pytest.raises(SystemExit) as excinfo:
        _parse(monkeypatch, "--data-flow-log-level", "TRACE")

    assert excinfo.value.code == 2
    stderr = capsys.readouterr().err
    assert "--data-flow-log-level" in stderr
    assert "invalid choice" in stderr


@pytest.mark.parametrize("level", ["DEBUG", "WARNING"])
def test_main_impl_forwards_log_level_to_configure_logger(
    level: str,
    monkeypatch: pytest.MonkeyPatch,
    isolated_cwd: None,
    restored_cli_globals: None,
) -> None:
    """``main_impl`` hands the parsed level to ``configure_logger``.

    The stub raises as soon as it is called, which stops ``main_impl`` before
    it compiles anything and keeps the real loguru sinks untouched.
    """
    recorded: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def _record(*args: Any, **kwargs: Any) -> None:
        recorded.append((args, kwargs))
        raise _StopAfterConfigure

    monkeypatch.setattr(slither_main, "configure_logger", _record)
    monkeypatch.setattr(sys, "argv", ["slither", "x.sol", "--data-flow-log-level", level])

    with pytest.raises(_StopAfterConfigure):
        slither_main.main_impl(all_detector_classes=[], all_printer_classes=[])

    assert recorded == [((), {"log_level": level})]
