"""Interval analysis domain."""

from __future__ import annotations

from enum import Enum

from slither.analyses.data_flow.engine.domain import Domain
from slither.analyses.data_flow.analyses.interval.core.state import State


class DomainVariant(Enum):
    """Three-valued lattice for interval domain."""

    BOTTOM = "bottom"  # Unreachable code path
    STATE = "state"    # Concrete tracked state
    TOP = "top"        # Unconstrained (no information)


class IntervalDomain(Domain):
    """Interval analysis domain with three-valued lattice.

    Lattice order: BOTTOM < STATE < TOP
    """

    def __init__(self, variant: DomainVariant, state: State | None = None):
        self._variant = variant
        self._state = state

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

    @classmethod
    def bottom(cls) -> "IntervalDomain":
        """Create bottom element (unreachable)."""
        return cls(DomainVariant.BOTTOM)

    @classmethod
    def top(cls) -> "IntervalDomain":
        """Create top element (unconstrained)."""
        return cls(DomainVariant.TOP)

    @classmethod
    def with_state(cls, state: State) -> "IntervalDomain":
        """Create domain with concrete state."""
        return cls(DomainVariant.STATE, state)

    def join(self, other: "IntervalDomain") -> bool:
        """Lattice join: self := self ⊔ other. Returns True if self changed."""
        if other.variant == DomainVariant.BOTTOM:
            return False

        if self.variant == DomainVariant.BOTTOM:
            self._variant = other.variant
            self._state = other.state.deep_copy() if other.state else None
            return True

        if other.variant == DomainVariant.TOP:
            if self.variant != DomainVariant.TOP:
                self._variant = DomainVariant.TOP
                self._state = None
                return True
            return False

        if self.variant == DomainVariant.TOP:
            return False

        # Both are STATE - merge variable dictionaries
        return self._merge_states(other)

    def _merge_states(self, other: "IntervalDomain") -> bool:
        """Merge two STATE domains."""
        changed = False
        other_names = other.state.variable_names()

        for name in other_names:
            if self.state.get_variable(name) is None:
                self.state.set_variable(name, other.state.get_variable(name))
                changed = True

        return changed

    def deep_copy(self) -> "IntervalDomain":
        """Create a deep copy of this domain."""
        if self._state is None:
            return IntervalDomain(self._variant)
        return IntervalDomain(self._variant, self._state.deep_copy())
