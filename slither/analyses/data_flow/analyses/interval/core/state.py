"""State tracking for interval analysis."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.smt_solver.facts import (
    AbstractValueId,
    AnalysisContextId,
    Fact,
    FactId,
    FactOwnerKind,
    FactRegistry,
    SemanticStateId,
    StaticOperationId,
)
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry


if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.types import SMTTerm


@dataclass(frozen=True)
class ComparisonInfo:
    """Stores comparison information for condition narrowing.

    When a comparison operation (e.g., x < 10) is processed, we store
    the condition SMT term so it can be used later for branch narrowing.
    """

    condition: SMTTerm
    operation_id: StaticOperationId | None = None


class State:
    """Tracks variable SMT terms for interval analysis."""

    def __init__(
        self,
        variables: dict[str, TrackedSMTVariable] | None = None,
        comparisons: dict[str, ComparisonInfo] | None = None,
        *,
        facts: tuple[Fact[SMTTerm], ...] = (),
        dependencies: dict[str, set[str]] | None = None,
        storage_slots: dict[str, list[str]] | None = None,
        branch_fact_ids: set[FactId] | None = None,
        context_id: AnalysisContextId | None = None,
    ) -> None:
        if any(fact.fact_id.owner is not FactOwnerKind.STATE_LOCAL for fact in facts):
            raise ValueError("State construction accepts only STATE_LOCAL facts")
        self._variables: dict[str, TrackedSMTVariable] = variables or {}
        self._comparisons: dict[str, ComparisonInfo] = comparisons or {}
        self._facts: FactRegistry[SMTTerm] = FactRegistry(facts)
        self._dependencies: dict[str, set[str]] = dependencies or {}
        self._storage_slots: dict[str, list[str]] = storage_slots or {}
        self._branch_fact_ids: set[FactId] = branch_fact_ids or set()
        self._context_id = context_id or AnalysisContextId.unbound()

    @property
    def context_id(self) -> AnalysisContextId:
        """Return the structured analysis context for this state."""
        return self._context_id

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

    def get_path_constraints(self) -> list[SMTTerm]:
        """Get path constraints for this branch."""
        return [fact.formula for fact in self._facts.values()]

    def get_facts(self) -> tuple[Fact[SMTTerm], ...]:
        """Return state-owned facts with their semantic identities."""
        return self._facts.values()

    def get_fact_ids(self) -> frozenset[FactId]:
        """Return active state-owned fact identities."""
        return self._facts.ids()

    def add_state_fact(self, fact: Fact[SMTTerm]) -> bool:
        """Add a state-owned fact, returning True only on first insertion."""
        if fact.fact_id.owner is not FactOwnerKind.STATE_LOCAL:
            raise ValueError("State facts must use the STATE_LOCAL owner")
        added = self._facts.register(fact)
        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_fact_registration(fact.fact_id, duplicate=not added)
        return added

    def add_path_constraint(self, fact: Fact[SMTTerm]) -> bool:
        """Compatibility name for adding a typed state-owned fact."""
        return self.add_state_fact(fact)

    def get_branch_constraints(self) -> list[SMTTerm]:
        """Get relational branch guards (from if/while conditions)."""
        return [fact.formula for fact in self.get_branch_facts()]

    def get_branch_facts(self) -> tuple[Fact[SMTTerm], ...]:
        """Return typed relational guards for overflow-property sessions."""
        return tuple(
            fact for fact in self._facts.values() if fact.fact_id in self._branch_fact_ids
        )

    def get_branch_fact_ids(self) -> frozenset[FactId]:
        """Return identities classified as branch guards."""
        return frozenset(self._branch_fact_ids)

    def add_branch_constraint(self, fact: Fact[SMTTerm]) -> bool:
        """Add a relational branch guard from apply_condition.

        Kept separate from path_constraints because checked-arithmetic
        path constraints (e.g. ``result <= left``) would trivially
        prove no-overflow if mixed in during the overflow SAT check.
        """
        added = self.add_state_fact(fact)
        self._branch_fact_ids.add(fact.fact_id)
        return added

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

    def deep_copy(self) -> State:
        """Create a deep copy of the state."""
        copied_deps = {k: set(v) for k, v in self._dependencies.items()}
        copied_storage = {k: list(v) for k, v in self._storage_slots.items()}
        return State(
            variables=dict(self._variables),
            comparisons=dict(self._comparisons),
            facts=self._facts.values(),
            dependencies=copied_deps,
            storage_slots=copied_storage,
            branch_fact_ids=set(self._branch_fact_ids),
            context_id=self._context_id,
        )

    def semantic_id(self, reachability: str = "state") -> SemanticStateId:
        """Return complete semantic identity without using formula text."""
        abstract_values = tuple(
            self._abstract_value_id(name, variable)
            for name, variable in sorted(self._variables.items())
        )
        storage_summary = tuple(
            (slot, tuple(writes)) for slot, writes in sorted(self._storage_slots.items())
        )
        comparisons = tuple(
            (name, info.operation_id) for name, info in sorted(self._comparisons.items())
        )
        dependencies = tuple(
            (name, tuple(sorted(values))) for name, values in sorted(self._dependencies.items())
        )
        return SemanticStateId(
            reachability=reachability,
            context_id=self._context_id,
            abstract_values=abstract_values,
            active_fact_ids=self._facts.ids(),
            storage_summary=storage_summary,
            comparisons=comparisons,
            dependencies=dependencies,
        )

    def semantic_id_for_facts(
        self,
        facts: tuple[Fact[SMTTerm], ...],
        reachability: str,
    ) -> SemanticStateId:
        """Return a non-mutating semantic view over an intentional fact subset."""
        return replace(
            self.semantic_id(reachability),
            active_fact_ids=frozenset(fact.fact_id for fact in facts),
        )

    @staticmethod
    def _abstract_value_id(
        program_name: str,
        variable: TrackedSMTVariable,
    ) -> AbstractValueId:
        """Build the identity of one tracked abstract value."""
        metadata = variable.base.metadata
        bit_width = metadata.get("bit_width")
        minimum = metadata.get("min_value")
        maximum = metadata.get("max_value")
        return AbstractValueId(
            program_name=program_name,
            symbol_name=variable.name,
            sort_kind=variable.sort.kind.value,
            sort_parameters=tuple(variable.sort.parameters),
            is_signed=bool(metadata.get("is_signed", False)),
            bit_width=bit_width if isinstance(bit_width, int) else None,
            minimum=minimum if isinstance(minimum, int) else None,
            maximum=maximum if isinstance(maximum, int) else None,
        )
