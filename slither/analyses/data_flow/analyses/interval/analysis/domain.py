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
        """Join this domain with another domain, returns True if this domain changed.
        
        Lattice semantics:
        - BOTTOM: no information (unreached)
        - TOP: unreachable path (e.g., after revert/assert failure)
        - STATE: concrete state with tracked variables
        
        Join rules:
        - self is TOP: already unreachable, no change possible
        - other is BOTTOM or TOP: contributes nothing to join (no change)
        - self is BOTTOM, other is STATE: copy other's state
        - both STATE: merge variables and constraints
        """
        # If self is already TOP (unreachable), nothing can change it
        if self.variant == DomainVariant.TOP:
            return False
        
        # If other is BOTTOM (unreached) or TOP (unreachable path), it contributes nothing
        if other.variant == DomainVariant.BOTTOM or other.variant == DomainVariant.TOP:
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            if self.state == other.state:
                return False

            changed = False
            for var_name, incoming_var in other.state.get_range_variables().items():
                # Use has_range_variable instead of get_range_variable to avoid marking as used
                existing_var = self.state.range_variables.get(var_name)

                if existing_var is None:
                    self.state.add_range_variable(var_name, incoming_var)
                    changed = True

            # Merge binary operations from other state
            for var_name, incoming_op in other.state.get_binary_operations().items():
                if not self.state.has_binary_operation(var_name):
                    self.state.set_binary_operation(var_name, incoming_op)
                    changed = True

            # Merge used variables sets - if used in either state, mark as used
            other_used = other.state.get_used_variables()
            if other_used:
                self.state.used_variables.update(other_used)
                changed = True

            # Merge path constraints: when branches merge, constraints should be disjointed
            # (either path's constraints can lead to this point)
            self_constraints = self.state.get_path_constraints()
            other_constraints = other.state.get_path_constraints()
            if self_constraints or other_constraints:
                # Clear existing constraints and mark as changed
                self.state.path_constraints = []
                changed = True

            return changed

        # This should be unreachable given the enum has only BOTTOM, TOP, STATE
        # and we've covered all valid combinations above
        raise AssertionError(
            f"Unexpected domain variant combination: self={self.variant}, other={other.variant}"
        )

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
