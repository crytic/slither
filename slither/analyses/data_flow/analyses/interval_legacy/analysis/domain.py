from enum import Enum, auto
from typing import Optional, TYPE_CHECKING


from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.engine.domain import Domain

if TYPE_CHECKING:
    pass


class DomainVariant(Enum):
    BOTTOM = auto()
    TOP = auto()
    STATE = auto()


class IntervalDomain(Domain):
    def __init__(self, variant: DomainVariant, state: Optional[State]):
        self.variant = variant

        if state is None:
            self.state = State({})
        else:
            self.state = state

    @classmethod
    def bottom(cls) -> "IntervalDomain":
        return cls(DomainVariant.BOTTOM, None)

    @classmethod
    def top(cls) -> "IntervalDomain":
        return cls(DomainVariant.TOP, None)

    @classmethod
    def with_state(cls, state: State) -> "IntervalDomain":
        return cls(DomainVariant.STATE, state)

    def join(self, other: "IntervalDomain") -> bool:
        """Join this domain with another domain, returns True if this domain changed."""
        if self.variant == DomainVariant.TOP:
            return False

        if other.variant in (DomainVariant.BOTTOM, DomainVariant.TOP):
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            return self._merge_states(other)

        raise AssertionError(
            f"Unexpected domain variant combination: self={self.variant}, other={other.variant}"
        )

    def _merge_states(self, other: "IntervalDomain") -> bool:
        """Merge two STATE domains. Returns True if this domain changed."""
        if self.state == other.state:
            return False

        changed = self._merge_range_variables(other)
        changed = self._merge_binary_operations(other) or changed
        changed = self._merge_used_variables(other) or changed
        changed = self._merge_path_constraints(other) or changed
        return changed

    def _merge_range_variables(self, other: "IntervalDomain") -> bool:
        """Merge range variables from other state."""
        changed = False
        for var_name, incoming_var in other.state.get_range_variables().items():
            if self.state.range_variables.get(var_name) is None:
                self.state.add_range_variable(var_name, incoming_var)
                changed = True
        return changed

    def _merge_binary_operations(self, other: "IntervalDomain") -> bool:
        """Merge binary operations from other state."""
        changed = False
        for var_name, incoming_op in other.state.get_binary_operations().items():
            if not self.state.has_binary_operation(var_name):
                self.state.set_binary_operation(var_name, incoming_op)
                changed = True
        return changed

    def _merge_used_variables(self, other: "IntervalDomain") -> bool:
        """Merge used variables from other state."""
        other_used = other.state.get_used_variables()
        if other_used:
            self.state.used_variables.update(other_used)
            return True
        return False

    def _merge_path_constraints(self, other: "IntervalDomain") -> bool:
        """Clear path constraints when branches merge."""
        if self.state.get_path_constraints() or other.state.get_path_constraints():
            self.state.path_constraints = []
            return True
        return False

    def __eq__(self, other):
        """Check equality with another IntervalDomain"""
        if not isinstance(other, IntervalDomain):
            return False
        return self.variant == other.variant and self.state == other.state

    def __hash__(self):
        """Hash function for IntervalDomain"""
        # Use hash of tracked variables for hashing
        items = sorted(
            (
                name,
                hash(
                    (
                        tracked.base,
                        tracked.overflow_flag,
                        tracked.overflow_amount,
                    )
                ),
            )
            for name, tracked in self.state.get_range_variables().items()
        )
        return hash((self.variant, tuple(items)))

    def deep_copy(self) -> "IntervalDomain":
        """Create a deep copy of the IntervalDomain"""
        return IntervalDomain(self.variant, self.state.deep_copy())
