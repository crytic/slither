from enum import Enum, auto
from typing import Optional


from slither.analyses.data_flow.analyses.interval.core.state import State
from slither.analyses.data_flow.engine.domain import Domain


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
            for var_name, incoming_smt_var in other.state.get_range_variables().items():
                existing_smt_var = self.state.get_range_variable(var_name)

                if existing_smt_var is not None:
                    # Variable exists - SMTVariables are compared by name + type
                    # So if they're different objects but represent the same variable, we keep the existing one
                    # No need to "join" SMT variables - they're just symbolic references
                    # The actual interval computation happens via constraint solving
                    if existing_smt_var != incoming_smt_var:
                        # Different SMT variables - this shouldn't happen if the solver is used correctly
                        # But if it does, we keep the existing one
                        pass
                else:
                    # Add new SMT variable from other state
                    # SMTVariables are immutable, so we can just reference it directly
                    self.state.add_range_variable(var_name, incoming_smt_var)
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
        # Use hash of SMTVariables for hashing (SMTVariables implement __hash__)
        items = sorted(
            (name, hash(smt_var)) for name, smt_var in self.state.get_range_variables().items()
        )
        return hash((self.variant, tuple(items)))

    def deep_copy(self) -> "IntervalDomain":
        """Create a deep copy of the IntervalDomain"""
        return IntervalDomain(self.variant, self.state.deep_copy())
