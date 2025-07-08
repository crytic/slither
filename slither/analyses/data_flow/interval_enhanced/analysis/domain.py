from enum import Enum, auto
from typing import Mapping, Optional

from slither.analyses.data_flow.domain import Domain
from slither.analyses.data_flow.interval_enhanced.core.state import State
from slither.analyses.data_flow.interval_enhanced.core.state_info import \
    StateInfo


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
    def with_state(cls, info: Mapping[str, StateInfo]) -> "IntervalDomain":
        return cls(DomainVariant.STATE, State(info))

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
            for variable_name, variable_range in other.state.info.items():
                if variable_name in self.state.info:
                    old_range = self.state.info[variable_name].deep_copy()
                    self.state.info[variable_name].join(variable_range)

                    # Check if any component changed after join
                    new_range = self.state.info[variable_name]
                    if (
                        old_range.interval_ranges != new_range.interval_ranges
                        or old_range.valid_values != new_range.valid_values
                        or old_range.invalid_values != new_range.invalid_values
                    ):
                        changed = True
                else:
                    self.state.info[variable_name] = variable_range.deep_copy()
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
        return hash((self.variant, tuple(sorted(self.state.info.items()))))

    def deep_copy(self) -> "IntervalDomain":
        """Create a deep copy of the IntervalDomain"""
        return IntervalDomain(self.variant, self.state.deep_copy())
