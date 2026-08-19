"""Shared pytest configuration for data-flow end-to-end tests."""

from __future__ import annotations

import logging
from collections.abc import Iterator

import pytest

DATA_FLOW_LOGGER_NAME = "DataFlow"


@pytest.fixture(autouse=True, scope="session")
def silence_data_flow_logging() -> Iterator[None]:
    """Keep data-flow log records out of the pytest report for the whole session.

    The analyses warn about every rounding inconsistency they find, which these
    tests deliberately provoke. No test asserts on that output, so it is pure
    noise in the report. A handler of its own keeps the records away from
    ``logging.lastResort`` (which would print WARNING and above to stderr), and
    ``propagate = False`` keeps them away from the root handlers pytest installs.
    """
    logger = logging.getLogger(DATA_FLOW_LOGGER_NAME)
    previous_propagate = logger.propagate
    handler = logging.NullHandler()

    logger.addHandler(handler)
    logger.propagate = False
    yield
    logger.removeHandler(handler)
    logger.propagate = previous_propagate
