"""Interval analysis domain."""

from __future__ import annotations

from enum import Enum

from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.smt_solver.facts import AnalysisContextId, SemanticStateId
from slither.analyses.data_flow.smt_solver.telemetry import get_telemetry


class DomainVariant(Enum):
    """Three-valued lattice for interval domain."""

    BOTTOM = "bottom"  # Unreachable code path
    STATE = "state"  # Concrete tracked state
    TOP = "top"  # Unconstrained (no information)


class IntervalDomain(Domain):
    """Interval analysis domain with three-valued lattice.

    Lattice order: BOTTOM < STATE < TOP
    """

    def __init__(
        self,
        variant: DomainVariant,
        state: State | None = None,
        context_id: AnalysisContextId | None = None,
    ) -> None:
        self._variant = variant
        self._state = state
        self._context_id = state.context_id if state else context_id or AnalysisContextId.unbound()

    @property
    def variant(self) -> DomainVariant:
        return self._variant

    @variant.setter
    def variant(self, value: DomainVariant) -> None:
        self._variant = value

    @property
    def state(self) -> State | None:
        return self._state

    @state.setter
    def state(self, value: State | None) -> None:
        self._state = value
        if value is not None:
            self._context_id = value.context_id

    @property
    def context_id(self) -> AnalysisContextId:
        """Return the structured context carried by this domain."""
        return self._context_id

    @classmethod
    def bottom(
        cls,
        context_id: AnalysisContextId | None = None,
    ) -> IntervalDomain:
        """Create bottom element (unreachable)."""
        return cls(DomainVariant.BOTTOM, context_id=context_id)

    @classmethod
    def top(
        cls,
        context_id: AnalysisContextId | None = None,
    ) -> IntervalDomain:
        """Create top element (unconstrained)."""
        return cls(DomainVariant.TOP, context_id=context_id)

    @classmethod
    def with_state(cls, state: State) -> IntervalDomain:
        """Create domain with concrete state."""
        return cls(DomainVariant.STATE, state)

    def join(self, other: Domain) -> bool:
        """Apply the complete lattice join without mutating ``other``."""
        if not isinstance(other, IntervalDomain):
            raise TypeError("IntervalDomain can only join another IntervalDomain")
        before = self.semantic_id()

        if other.variant == DomainVariant.BOTTOM:
            self._context_id = self._compatible_context(other)
            return self._record_join(before)

        if self.variant == DomainVariant.BOTTOM:
            context_id = self._compatible_context(other)
            self._variant = other.variant
            self._state = other.state.deep_copy() if other.state else None
            self._context_id = context_id
            return self._record_join(before)

        context_id = self._compatible_context(other)

        if other.variant == DomainVariant.TOP:
            self._variant = DomainVariant.TOP
            self._state = None
            self._context_id = context_id
            return self._record_join(before)

        if self.variant == DomainVariant.TOP:
            self._context_id = context_id
            return self._record_join(before)

        self._merge_states(other)
        return self._record_join(before)

    def _record_join(self, before: SemanticStateId) -> bool:
        """Compare the complete state identity and emit opt-in telemetry."""
        changed = self.semantic_id() != before
        telemetry = get_telemetry()
        if telemetry is not None and telemetry.enabled:
            telemetry.record_state_join(changed)
        return changed

    def _merge_states(self, other: IntervalDomain) -> None:
        """Replace two reachable states with their complete conservative join."""
        if self._state is None or other.state is None:
            raise ValueError("STATE domains must carry a State")
        joined = self._state.joined(other.state)
        if joined.semantic_id() != self._state.semantic_id():
            self._state = joined
            self._context_id = joined.context_id

    def _compatible_context(self, other: IntervalDomain) -> AnalysisContextId:
        """Return the shared context, treating an unbound bottom/top as neutral."""
        if self._context_id == other.context_id:
            return self._context_id
        unbound = AnalysisContextId.unbound()
        if self._context_id == unbound:
            return other.context_id
        if other.context_id == unbound:
            return self._context_id
        raise ValueError("Cannot join domains from incompatible analysis contexts")

    def deep_copy(self) -> IntervalDomain:
        """Create a deep copy of this domain."""
        if self._state is None:
            return IntervalDomain(self._variant, context_id=self._context_id)
        return IntervalDomain(self._variant, self._state.deep_copy())

    def semantic_id(self) -> SemanticStateId:
        """Return complete identity including reachability."""
        if self._variant is DomainVariant.STATE:
            if self._state is None:
                raise ValueError("STATE domain has no semantic State")
            return self._state.semantic_id(self._variant.value)
        return State(context_id=self._context_id).semantic_id(self._variant.value)
