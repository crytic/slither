"""State tracking for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.types import SMTTerm


class ComparisonInfo:
    """Stores comparison information for condition narrowing.

    When a comparison operation (e.g., x < 10) is processed, we store
    the condition SMT term so it can be used later for branch narrowing.
    """

    def __init__(self, condition: "SMTTerm") -> None:
        self.condition = condition


class State:
    """Tracks variable SMT terms for interval analysis."""

    def __init__(
        self,
        variables: dict[str, TrackedSMTVariable] | None = None,
        comparisons: dict[str, ComparisonInfo] | None = None,
        path_constraints: list["SMTTerm"] | None = None,
        dependencies: dict[str, set[str]] | None = None,
        storage_slots: dict[str, list[str]] | None = None,
        memory_slots: dict[str, list[str]] | None = None,
    ):
        self._variables: dict[str, TrackedSMTVariable] = variables or {}
        self._comparisons: dict[str, ComparisonInfo] = comparisons or {}
        self._path_constraints: list["SMTTerm"] = path_constraints or []
        self._dependencies: dict[str, set[str]] = dependencies or {}
        self._storage_slots: dict[str, list[str]] = storage_slots or {}
        self._memory_slots: dict[str, list[str]] = memory_slots or {}

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

    def get_path_constraints(self) -> list["SMTTerm"]:
        """Get path constraints for this branch."""
        return self._path_constraints

    def add_path_constraint(self, constraint: "SMTTerm") -> None:
        """Add a path constraint for branch narrowing."""
        self._path_constraints.append(constraint)

    def set_comparison(self, name: str, info: ComparisonInfo) -> None:
        """Store comparison info for a boolean result variable."""
        self._comparisons[name] = info

    def get_comparison(self, name: str) -> ComparisonInfo | None:
        """Get comparison info for a boolean result variable."""
        return self._comparisons.get(name)

    def add_dependency(self, variable: str, depends_on: str) -> None:
        """Record that variable depends on depends_on."""
        if variable not in self._dependencies:
            self._dependencies[variable] = set()
        self._dependencies[variable].add(depends_on)

    def add_dependencies(self, variable: str, depends_on: set[str]) -> None:
        """Record that variable depends on multiple variables."""
        if variable not in self._dependencies:
            self._dependencies[variable] = set()
        self._dependencies[variable].update(depends_on)

    def get_dependencies(self, variable: str) -> set[str]:
        """Get direct dependencies for a variable."""
        return self._dependencies.get(variable, set())

    def has_transitive_dependency(self, source: str, target: str) -> bool:
        """Check if source transitively depends on target."""
        visited: set[str] = set()
        stack = [source]

        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)

            deps = self._dependencies.get(current, set())
            if target in deps:
                return True
            stack.extend(deps)

        return False

    def add_storage_write(self, slot_key: str, variable_name: str) -> None:
        """Record a storage write: slot_key was written with variable_name."""
        if slot_key not in self._storage_slots:
            self._storage_slots[slot_key] = []
        self._storage_slots[slot_key].append(variable_name)

    def get_storage_writes(self, slot_key: str) -> list[str]:
        """Get list of variable names written to this slot."""
        return self._storage_slots.get(slot_key, [])

    def add_memory_write(self, offset_key: str, variable_name: str) -> None:
        """Record a memory write: offset_key was written with variable_name."""
        if offset_key not in self._memory_slots:
            self._memory_slots[offset_key] = []
        self._memory_slots[offset_key].append(variable_name)

    def get_memory_writes(self, offset_key: str) -> list[str]:
        """Get list of variable names written to this memory offset."""
        return self._memory_slots.get(offset_key, [])

    def deep_copy(self) -> "State":
        """Create a deep copy of the state."""
        copied_deps = {k: set(v) for k, v in self._dependencies.items()}
        copied_storage = {k: list(v) for k, v in self._storage_slots.items()}
        copied_memory = {k: list(v) for k, v in self._memory_slots.items()}
        return State(
            dict(self._variables),
            dict(self._comparisons),
            list(self._path_constraints),
            copied_deps,
            copied_storage,
            copied_memory,
        )
