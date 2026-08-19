"""Shared pytest configuration for data-flow end-to-end tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from loguru import logger as loguru_logger


@pytest.fixture(autouse=True, scope="session")
def silence_data_flow_logging() -> Iterator[None]:
    """Keep the data-flow loguru output off stderr for the whole test session.

    The analyses log progress at INFO through loguru's colorized stderr sink.
    No test asserts on it, so it is pure noise in the pytest report: drop the
    sink and disable records originating from the ``slither`` package.
    """
    loguru_logger.remove()
    loguru_logger.disable("slither")
    yield
    loguru_logger.enable("slither")
