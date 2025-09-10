from enum import Enum, auto
from typing import Optional

from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.engine.domain import Domain


class DomainVariant(Enum):
    BOTTOM = auto()
    TOP = auto()
    STATE = auto()


class IntervalDomain(Domain):
    def __init__(self, variant: DomainVariant, state: Optional[State] = None):
        self.variant = variant

        if state is None:
            self.state = State({})
        else:
            self.state = state

    @classmethod
    def bottom(cls) -> "IntervalDomain":
        return cls(DomainVariant.BOTTOM)

    @classmethod
    def top(cls) -> "IntervalDomain":
        return cls(DomainVariant.TOP)

    @classmethod
    def with_state(cls, state: State) -> "IntervalDomain":
        return cls(DomainVariant.STATE, state)

    def join(self, other: "IntervalDomain") -> bool:
        """Join this domain with another domain, returns True if this domain changed"""
        if self.variant == DomainVariant.TOP or other.variant == DomainVariant.BOTTOM:
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            if self.state == other.state:
                return False

            changed = False
            for var_name, incoming_range in other.state.get_range_variables().items():
                existing_range = self.state.get_range_variable(var_name)

                if existing_range is not None:
                    # Variable exists, join with the incoming range
                    range_before_join = existing_range.copy()
                    existing_range.join(incoming_range)

                    # Check if any component changed after join
                    if (
                        range_before_join.interval_ranges != existing_range.interval_ranges
                        or range_before_join.valid_values != existing_range.valid_values
                        or range_before_join.invalid_values != existing_range.invalid_values
                    ):
                        changed = True
                else:
                    # Add new variable from other state
                    self.state.add_range_variable(var_name, incoming_range.copy())
                    changed = True

            return changed

        else:
            self.variant = DomainVariant.TOP

        return True

    def __eq__(self, other):
        """Check equality with another IntervalDomain"""
        if not isinstance(other, IntervalDomain):
            return False
        return self.variant == other.variant and self.state == other.state

    def __hash__(self):
        """Hash function for IntervalDomain"""
        return hash((self.variant, tuple(sorted(self.state.get_range_variables().items()))))

    def deep_copy(self) -> "IntervalDomain":
        """Create a deep copy of the IntervalDomain"""
        return IntervalDomain(self.variant, self.state.deep_copy())
