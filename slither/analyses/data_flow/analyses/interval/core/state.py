"""State tracking for interval analysis."""

from __future__ import annotations

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)


class State:
    """Tracks variable SMT terms for interval analysis."""

    def __init__(self, variables: dict[str, TrackedSMTVariable] | None = None):
        self._variables: dict[str, TrackedSMTVariable] = variables or {}

    def get_variable(self, name: str) -> TrackedSMTVariable | None:
        """Get tracked variable by name, or None if not tracked."""
        return self._variables.get(name)

    def set_variable(self, name: str, var: TrackedSMTVariable) -> None:
        """Set or update a tracked variable."""
        self._variables[name] = var

    def variable_names(self) -> set[str]:
        """Return all tracked variable names."""
        return set(self._variables.keys())

    def get_range_variables(self) -> dict[str, TrackedSMTVariable]:
        """Get all tracked variables."""
        return self._variables

    def get_used_variables(self) -> set[str]:
        """Get used variable names. Currently returns all tracked."""
        return set(self._variables.keys())

    def get_path_constraints(self) -> list:
        """Get path constraints. Currently empty."""
        return []

    def deep_copy(self) -> "State":
        """Create a deep copy of the state."""
        return State(dict(self._variables))
