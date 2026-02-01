"""Core data structures for interval analysis."""

from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

__all__ = ["State", "TrackedSMTVariable"]
