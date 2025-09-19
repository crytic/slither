from enum import Enum, auto
from typing import Optional

from slither.analyses.data_flow.analyses.reentrancy.core.state import State
from slither.analyses.data_flow.engine.domain import Domain


class DomainVariant(Enum):
    BOTTOM = auto()
    TOP = auto()
    STATE = auto()


class ReentrancyDomain(Domain):
    def __init__(self, variant: DomainVariant, state: Optional[State] = None):
        self.variant = variant
        self.state = state or State()

    @classmethod
    def bottom(cls) -> "ReentrancyDomain":
        return cls(DomainVariant.BOTTOM)

    @classmethod
    def top(cls) -> "ReentrancyDomain":
        return cls(DomainVariant.TOP)

    @classmethod
    def with_state(cls, info: State) -> "ReentrancyDomain":
        return cls(DomainVariant.STATE, info)

    def join(self, other: "ReentrancyDomain") -> bool:
        if self.variant == DomainVariant.TOP or other.variant == DomainVariant.BOTTOM:
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            self.state.written.clear()
            self.state.events.clear()
            self.state.writes_after_calls.clear()
            self.state.cross_function.clear()
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            if self.state == other.state:
                return False

            self.state.send_eth.update(other.state.send_eth)
            self.state.calls.update(other.state.calls)
            self.state.reads.update(other.state.reads)
            self.state.reads_prior_calls.update(other.state.reads_prior_calls)
            self.state.safe_send_eth.update(other.state.safe_send_eth)
            self.state.writes_after_calls.update(other.state.writes_after_calls)
            self.state.cross_function.update(other.state.cross_function)
            return True

        else:
            self.variant = DomainVariant.TOP

        return True
