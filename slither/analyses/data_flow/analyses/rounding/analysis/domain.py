from enum import Enum, auto
from typing import Optional

from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
)
from slither.analyses.data_flow.engine.domain import Domain


class DomainVariant(Enum):
    BOTTOM = auto()  # Initial state (no information)
    STATE = auto()  # Normal state with rounding information


class RoundingDomain(Domain):
    """Domain for rounding direction analysis"""

    def __init__(self, variant: DomainVariant, state: Optional[RoundingState] = None):
        self.variant = variant
        self.state = state or RoundingState()

    @classmethod
    def top(cls) -> "RoundingDomain":
        """Top element (all variables NEUTRAL)"""
        domain = cls(DomainVariant.STATE)
        # Top means all variables are NEUTRAL, which is the default
        return domain

    @classmethod
    def bottom(cls) -> "RoundingDomain":
        """Bottom element (no information)"""
        return cls(DomainVariant.BOTTOM)

    def join(self, other: "RoundingDomain") -> bool:
        """
        Merge two domains, return True if changed.

        Join semantics:
        - If variable exists in only one domain → add it to self
        - If variable has same tag in both → keep that tag
        - If variable has different tags → set to UNKNOWN
        """
        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.STATE:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            return True

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.BOTTOM:
            # No change needed, self already has state
            return False

        if self.variant == DomainVariant.BOTTOM and other.variant == DomainVariant.BOTTOM:
            return False

        if self.variant == DomainVariant.STATE and other.variant == DomainVariant.STATE:
            changed = False
            # Get all variables from both states
            all_vars = set(self.state._tags.keys()) | set(other.state._tags.keys())

            # Merge tags from other into self
            for var in all_vars:
                self_tag = self.state.get_tag(var)
                other_tag = other.state.get_tag(var)

                if self_tag == other_tag:
                    # Same tag, no change needed
                    continue
                elif self_tag == RoundingTag.NEUTRAL:
                    # Neutral adopts a more specific tag if available.
                    if other_tag != RoundingTag.NEUTRAL:
                        self.state.set_tag(var, other_tag)
                        changed = True
                elif other_tag == RoundingTag.NEUTRAL:
                    # Other is neutral, keep self's tag (no change)
                    continue
                else:
                    # Different tags (e.g., UP vs DOWN) → set to UNKNOWN
                    reason = f"Join conflict: {self_tag.name} vs {other_tag.name}"
                    self.state.set_tag(var, RoundingTag.UNKNOWN, unknown_reason=reason)
                    changed = True

            return changed

        return False
