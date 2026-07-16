"""Semantic state tracking for interval analysis."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from z3 import BitVecVal, UGE, ULE

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.smt_solver.facts import (
    AbstractValueId,
    AnalysisContextId,
    Fact,
    FactId,
    FactKind,
    FactOriginKind,
    FactOwnerKind,
    FactProvenance,
    FactRegistry,
    SemanticStateId,
    StaticOperationId,
)
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry


if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.types import SMTTerm


@dataclass(frozen=True)
class IntervalRefinement:
    """Branch-specific interval restriction derived from one comparison."""

    variable_name: str
    true_interval: NumericInterval
    false_interval: NumericInterval
    true_reachable: bool = True
    false_reachable: bool = True


@dataclass(frozen=True)
class ComparisonInfo:
    """Comparison term and stable operation identity used for branch narrowing."""

    condition: SMTTerm
    operation_id: StaticOperationId
    refinements: tuple[IntervalRefinement, ...] = ()

    def matches(self, other: ComparisonInfo) -> bool:
        """Return whether both records denote the same semantic comparison."""
        return self.operation_id == other.operation_id and self.refinements == other.refinements


@dataclass(frozen=True)
class StorageSlotSummary:
    """May-write storage summary for one symbolic or concrete slot."""

    writes: frozenset[str]
    may_be_unwritten: bool = False

    def join(self, other: StorageSlotSummary | None) -> StorageSlotSummary:
        """Return the conservative may-write union for two paths."""
        if other is None:
            return StorageSlotSummary(self.writes, may_be_unwritten=True)
        return StorageSlotSummary(
            self.writes | other.writes,
            may_be_unwritten=self.may_be_unwritten or other.may_be_unwritten,
        )


class State:
    """Mutable transfer builder with complete deterministic semantic identity."""

    def __init__(
        self,
        variables: dict[str, TrackedSMTVariable] | None = None,
        comparisons: dict[str, ComparisonInfo] | None = None,
        *,
        facts: tuple[Fact[SMTTerm], ...] = (),
        dependencies: dict[str, set[str]] | None = None,
        storage_slots: Mapping[str, Sequence[str] | StorageSlotSummary] | None = None,
        branch_fact_ids: set[FactId] | None = None,
        context_id: AnalysisContextId | None = None,
    ) -> None:
        self._validate_explicit_facts(facts)
        self._variables = dict(variables or {})
        self._comparisons = dict(comparisons or {})
        self._facts: FactRegistry[SMTTerm] = FactRegistry(facts)
        self._dependencies = {name: set(values) for name, values in (dependencies or {}).items()}
        self._storage_slots = self._copy_storage(storage_slots or {})
        self._context_id = context_id or AnalysisContextId.unbound()
        self._validate_branch_view(branch_fact_ids)

    @staticmethod
    def _validate_explicit_facts(facts: tuple[Fact[SMTTerm], ...]) -> None:
        if any(fact.fact_id.owner is not FactOwnerKind.STATE_LOCAL for fact in facts):
            raise ValueError("State construction accepts only STATE_LOCAL facts")
        if any(
            fact.fact_id.provenance.origin_kind is FactOriginKind.ABSTRACT_STATE for fact in facts
        ):
            raise ValueError("Abstract range facts are derived from tracked values")

    @staticmethod
    def _copy_storage(
        storage: Mapping[str, Sequence[str] | StorageSlotSummary],
    ) -> dict[str, StorageSlotSummary]:
        result = {}
        for slot, summary in storage.items():
            if isinstance(summary, StorageSlotSummary):
                result[slot] = summary
            else:
                result[slot] = StorageSlotSummary(frozenset(summary))
        return result

    def _validate_branch_view(self, branch_fact_ids: set[FactId] | None) -> None:
        if branch_fact_ids is None:
            return
        derived_ids = {
            fact.fact_id
            for fact in self._facts.values()
            if fact.fact_id.kind is FactKind.BRANCH_GUARD
        }
        if branch_fact_ids != derived_ids:
            raise ValueError("Branch facts must be derived from the active fact registry")

    @property
    def context_id(self) -> AnalysisContextId:
        """Return the structured analysis context for this state."""
        return self._context_id

    def get_variable(self, name: str) -> TrackedSMTVariable | None:
        """Return one tracked SSA variable, or ``None`` when absent."""
        return self._variables.get(name)

    def set_variable(self, name: str, variable: TrackedSMTVariable) -> None:
        """Set or update one tracked SSA variable in this transfer builder."""
        self._variables[name] = variable

    def refine_variable(self, name: str, interval: NumericInterval) -> bool:
        """Intersect one variable with a branch interval; return feasibility."""
        variable = self._variables.get(name)
        if variable is None:
            return True
        refined = variable.interval.intersection(interval)
        if refined is None:
            return False
        self._variables[name] = variable.with_interval(refined)
        return True

    def variable_names(self) -> set[str]:
        """Return all tracked variable names."""
        return set(self._variables)

    def get_range_variables(self) -> dict[str, TrackedSMTVariable]:
        """Return a shallow snapshot of all immutable tracked values."""
        return dict(self._variables)

    def get_used_variables(self) -> set[str]:
        """Return all currently tracked variable names."""
        return set(self._variables)

    def get_path_constraints(self) -> list[SMTTerm]:
        """Return all state-owned formulas active in this state."""
        return [fact.formula for fact in self.get_facts()]

    def get_explicit_facts(self) -> tuple[Fact[SMTTerm], ...]:
        """Return path, continuation, and other producer-owned state facts."""
        return self._sorted_facts(self._facts.values())

    def get_explicit_fact_ids(self) -> frozenset[FactId]:
        """Return fact identities subject to ordinary predecessor intersection."""
        return self._facts.ids()

    def get_facts(self) -> tuple[Fact[SMTTerm], ...]:
        """Return explicit facts plus range facts derived from abstract values."""
        return self._sorted_facts((*self._facts.values(), *self._range_facts()))

    def get_fact_ids(self) -> frozenset[FactId]:
        """Return every active state-owned fact identity."""
        return frozenset(fact.fact_id for fact in self.get_facts())

    def add_state_fact(self, fact: Fact[SMTTerm]) -> bool:
        """Add a producer-owned state fact idempotently."""
        if fact.fact_id.owner is not FactOwnerKind.STATE_LOCAL:
            raise ValueError("State facts must use the STATE_LOCAL owner")
        if fact.fact_id.provenance.origin_kind is FactOriginKind.ABSTRACT_STATE:
            raise ValueError("Abstract range facts are managed by State")
        added = self._facts.register(fact)
        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_fact_registration(fact.fact_id, duplicate=not added)
        return added

    def add_path_constraint(self, fact: Fact[SMTTerm]) -> bool:
        """Compatibility name for adding a typed state-owned fact."""
        return self.add_state_fact(fact)

    def get_branch_constraints(self) -> list[SMTTerm]:
        """Return formulas classified as relational CFG branch guards."""
        return [fact.formula for fact in self.get_branch_facts()]

    def get_branch_facts(self) -> tuple[Fact[SMTTerm], ...]:
        """Derive the branch view from the final active explicit fact set."""
        return tuple(
            fact for fact in self.get_explicit_facts() if fact.fact_id.kind is FactKind.BRANCH_GUARD
        )

    def get_branch_fact_ids(self) -> frozenset[FactId]:
        """Return active identities classified as branch guards."""
        return frozenset(fact.fact_id for fact in self.get_branch_facts())

    def add_branch_constraint(self, fact: Fact[SMTTerm]) -> bool:
        """Add a branch guard whose view is derived from its semantic kind."""
        if fact.fact_id.kind is not FactKind.BRANCH_GUARD:
            raise ValueError("Branch constraints must use BRANCH_GUARD kind")
        return self.add_state_fact(fact)

    def set_comparison(self, name: str, info: ComparisonInfo) -> None:
        """Store comparison information for a boolean SSA result."""
        self._comparisons[name] = info

    def get_comparison(self, name: str) -> ComparisonInfo | None:
        """Return comparison information for a boolean SSA result."""
        return self._comparisons.get(name)

    def add_dependency(self, variable: str, depends_on: str) -> None:
        """Record one may-dependency edge."""
        self._dependencies.setdefault(variable, set()).add(depends_on)

    def add_dependencies(self, variable: str, depends_on: set[str]) -> None:
        """Record several may-dependency edges."""
        self._dependencies.setdefault(variable, set()).update(depends_on)

    def get_dependencies(self, variable: str) -> set[str]:
        """Return a copy of the direct may-dependencies for one variable."""
        return set(self._dependencies.get(variable, set()))

    def has_transitive_dependency(self, source: str, target: str) -> bool:
        """Return whether ``source`` may transitively depend on ``target``."""
        visited: set[str] = set()
        stack = [source]
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            visited.add(current)
            dependencies = self._dependencies.get(current, set())
            if target in dependencies:
                return True
            stack.extend(dependencies)
        return False

    def add_storage_write(self, slot_key: str, variable_name: str) -> None:
        """Record one definite write while retaining prior may-write values."""
        summary = self._storage_slots.get(slot_key, StorageSlotSummary(frozenset()))
        self._storage_slots[slot_key] = StorageSlotSummary(
            summary.writes | {variable_name},
            may_be_unwritten=False,
        )

    def get_storage_writes(self, slot_key: str) -> list[str]:
        """Return deterministic may-write variable names for one slot."""
        summary = self._storage_slots.get(slot_key)
        return sorted(summary.writes) if summary is not None else []

    def storage_may_be_unwritten(self, slot_key: str) -> bool:
        """Return whether some incoming path has no modeled write to the slot."""
        summary = self._storage_slots.get(slot_key)
        return summary is None or summary.may_be_unwritten

    def deep_copy(self) -> State:
        """Copy every mutable semantic container without copying immutable values."""
        return State(
            variables=self._variables,
            comparisons=self._comparisons,
            facts=self._facts.values(),
            dependencies=self._dependencies,
            storage_slots=self._storage_slots,
            context_id=self._context_id,
        )

    def joined(self, other: State) -> State:
        """Return the complete conservative join without mutating either predecessor."""
        if self._context_id != other._context_id:
            raise ValueError("Cannot join states from incompatible analysis contexts")
        return State(
            variables=self._join_variables(other),
            comparisons=self._join_comparisons(other),
            facts=self._common_facts(other),
            dependencies=self._join_dependencies(other),
            storage_slots=self._join_storage(other),
            context_id=self._context_id,
        )

    def _common_facts(self, other: State) -> tuple[Fact[SMTTerm], ...]:
        common_ids = self._facts.ids() & other._facts.ids()
        facts = []
        for fact in self._facts.values():
            if fact.fact_id not in common_ids:
                continue
            other_fact = other._facts.get(fact.fact_id)
            if other_fact is None or not fact.formula.eq(other_fact.formula):
                raise ValueError("One semantic FactId maps to incompatible formulas")
            facts.append(fact)
        return self._sorted_facts(tuple(facts))

    def _join_variables(self, other: State) -> dict[str, TrackedSMTVariable]:
        result = {}
        for name in sorted(self.variable_names() | other.variable_names()):
            left = self._variables.get(name)
            right = other._variables.get(name)
            if left is None:
                if right is None:
                    raise RuntimeError(f"Joined variable {name!r} is absent from both states")
                result[name] = right.as_path_optional()
            elif right is None:
                result[name] = left.as_path_optional()
            else:
                result[name] = self._join_variable(name, left, right)
        return result

    @staticmethod
    def _join_variable(
        name: str,
        left: TrackedSMTVariable,
        right: TrackedSMTVariable,
    ) -> TrackedSMTVariable:
        compatible = (
            left.name == right.name
            and left.sort == right.sort
            and left.type_interval == right.type_interval
        )
        if not compatible:
            raise ValueError(f"Incompatible abstract values for SSA name {name!r}")
        joined = left.with_interval(
            left.interval.hull(right.interval),
            is_total=left.is_total and right.is_total,
        )
        return joined.with_overflow_predicates(
            no_overflow=State._merge_optional_term(left.no_overflow, right.no_overflow),
            no_underflow=State._merge_optional_term(left.no_underflow, right.no_underflow),
            operation_id=State._merge_optional_id(
                left.overflow_operation_id,
                right.overflow_operation_id,
            ),
            is_unchecked=left.is_unchecked or right.is_unchecked,
        )

    @staticmethod
    def _merge_optional_term(left: SMTTerm | None, right: SMTTerm | None) -> SMTTerm | None:
        if left is None:
            return right
        if right is None:
            return left
        if not left.eq(right):
            raise ValueError("One SSA value carries incompatible overflow predicates")
        return left

    @staticmethod
    def _merge_optional_id(
        left: StaticOperationId | None,
        right: StaticOperationId | None,
    ) -> StaticOperationId | None:
        if left is None:
            return right
        if right is None:
            return left
        if left != right:
            raise ValueError("One SSA value carries incompatible overflow identities")
        return left

    def _join_comparisons(self, other: State) -> dict[str, ComparisonInfo]:
        result = {}
        for name in sorted(self._comparisons.keys() & other._comparisons.keys()):
            left = self._comparisons[name]
            if left.matches(other._comparisons[name]):
                result[name] = left
        return result

    def _join_dependencies(self, other: State) -> dict[str, set[str]]:
        result = {}
        for name in sorted(self._dependencies.keys() | other._dependencies.keys()):
            result[name] = self._dependencies.get(name, set()) | other._dependencies.get(
                name, set()
            )
        return result

    def _join_storage(self, other: State) -> dict[str, StorageSlotSummary]:
        result = {}
        for slot in sorted(self._storage_slots.keys() | other._storage_slots.keys()):
            left = self._storage_slots.get(slot)
            right = other._storage_slots.get(slot)
            if left is None:
                if right is None:
                    raise RuntimeError(f"Joined storage slot {slot!r} is absent from both states")
                result[slot] = right.join(None)
            else:
                result[slot] = left.join(right)
        return result

    def semantic_id(self, reachability: str = "state") -> SemanticStateId:
        """Return complete semantic identity without using formula text."""
        abstract_values = tuple(
            self._abstract_value_id(name, variable)
            for name, variable in sorted(self._variables.items())
        )
        storage_summary = tuple(
            (slot, tuple(sorted(summary.writes)), summary.may_be_unwritten)
            for slot, summary in sorted(self._storage_slots.items())
        )
        comparisons = tuple(
            (name, info.operation_id, self._refinement_ids(info))
            for name, info in sorted(self._comparisons.items())
        )
        dependencies = tuple(
            (name, tuple(sorted(values))) for name, values in sorted(self._dependencies.items())
        )
        return SemanticStateId(
            reachability=reachability,
            context_id=self._context_id,
            abstract_values=abstract_values,
            active_fact_ids=self.get_fact_ids(),
            storage_summary=storage_summary,
            comparisons=comparisons,
            dependencies=dependencies,
        )

    @staticmethod
    def _refinement_ids(
        info: ComparisonInfo,
    ) -> tuple[tuple[str, int, int, int, int, bool, bool], ...]:
        return tuple(
            (
                refinement.variable_name,
                refinement.true_interval.lower,
                refinement.true_interval.upper,
                refinement.false_interval.lower,
                refinement.false_interval.upper,
                refinement.true_reachable,
                refinement.false_reachable,
            )
            for refinement in info.refinements
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

    def _range_facts(self) -> tuple[Fact[SMTTerm], ...]:
        facts = []
        for name, variable in sorted(self._variables.items()):
            if not variable.is_total:
                continue
            type_interval = variable.type_interval
            if variable.interval.lower != type_interval.lower:
                facts.append(self._range_fact(name, variable, "lower"))
            if variable.interval.upper != type_interval.upper:
                facts.append(self._range_fact(name, variable, "upper"))
        return tuple(facts)

    def _range_fact(
        self,
        program_name: str,
        variable: TrackedSMTVariable,
        side: str,
    ) -> Fact[SMTTerm]:
        value = variable.interval.lower if side == "lower" else variable.interval.upper
        width = variable.sort.parameters[0]
        constant = BitVecVal(value, width)
        signed = bool(variable.base.metadata.get("is_signed", False))
        if side == "lower":
            formula = variable.term >= constant if signed else UGE(variable.term, constant)
        else:
            formula = variable.term <= constant if signed else ULE(variable.term, constant)
        return Fact(
            fact_id=FactId(
                owner=FactOwnerKind.STATE_LOCAL,
                kind=FactKind.RANGE_BOUND,
                provenance=FactProvenance(
                    context_id=self._context_id,
                    origin_kind=FactOriginKind.ABSTRACT_STATE,
                ),
                semantic_key=(program_name, variable.name, side, str(value)),
            ),
            formula=formula,
        )

    @staticmethod
    def _sorted_facts(facts: tuple[Fact[SMTTerm], ...]) -> tuple[Fact[SMTTerm], ...]:
        return tuple(sorted(facts, key=lambda fact: State._fact_sort_key(fact.fact_id)))

    @staticmethod
    def _fact_sort_key(fact_id: FactId) -> tuple[str, ...]:
        provenance = fact_id.provenance
        return (
            fact_id.owner.value,
            fact_id.kind.value,
            repr(provenance.context_id),
            provenance.origin_kind.value,
            repr(provenance.operation_id),
            repr(provenance.cfg_edge),
            repr(provenance.loop_header_id),
            repr(provenance.loop_generation),
            repr(provenance.property_id),
            *fact_id.semantic_key,
        )

    @staticmethod
    def _abstract_value_id(
        program_name: str,
        variable: TrackedSMTVariable,
    ) -> AbstractValueId:
        metadata = variable.base.metadata
        bit_width = metadata.get("bit_width")
        return AbstractValueId(
            program_name=program_name,
            symbol_name=variable.name,
            sort_kind=variable.sort.kind.value,
            sort_parameters=tuple(variable.sort.parameters),
            is_signed=bool(metadata.get("is_signed", False)),
            bit_width=bit_width if isinstance(bit_width, int) else None,
            minimum=variable.interval.lower,
            maximum=variable.interval.upper,
            is_total=variable.is_total,
            has_no_overflow=variable.no_overflow is not None,
            has_no_underflow=variable.no_underflow is not None,
            overflow_operation_id=variable.overflow_operation_id,
            is_unchecked=variable.is_unchecked,
        )
