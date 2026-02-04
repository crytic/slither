from enum import Enum, auto
from typing import Optional

from slither.analyses.data_flow.analyses.rounding.core.state import (
    RoundingState,
    RoundingTag,
)
from slither.analyses.data_flow.engine.domain import Domain


class DomainVariant(Enum):
    """Variant type for rounding domain lattice (BOTTOM or STATE)."""

    BOTTOM = auto()  # Initial state (no information)
    STATE = auto()  # Normal state with rounding information


class RoundingDomain(Domain):
    """Domain for rounding direction analysis."""

    def __init__(self, variant: DomainVariant, state: Optional[RoundingState] = None):
        self.variant = variant
        self.state = state or RoundingState()

    @classmethod
    def top(cls) -> "RoundingDomain":
        """Top element (all variables NEUTRAL)."""
        domain = cls(DomainVariant.STATE)
        # Top means all variables are NEUTRAL, which is the default
        return domain

    @classmethod
    def bottom(cls) -> "RoundingDomain":
        """Bottom element (no information)."""
        return cls(DomainVariant.BOTTOM)

    def join(self, other: "RoundingDomain") -> bool:
        """Merge two domains, return True if changed.

        Join semantics:
        - If variable exists in only one domain → add it to self
        - If variable has same tag in both → keep that tag
        - If variable has different tags → set to UNKNOWN
        """
        self_is_bottom = self.variant == DomainVariant.BOTTOM
        other_is_bottom = other.variant == DomainVariant.BOTTOM

        if self_is_bottom and not other_is_bottom:
            self.variant = DomainVariant.STATE
            self.state = other.state.deep_copy()
            return True

        if not self_is_bottom and other_is_bottom:
            return False

        if self_is_bottom and other_is_bottom:
            return False

        if not self_is_bottom and not other_is_bottom:
            return self._merge_variable_tags(other)

        return False

    def _merge_variable_tags(self, other: "RoundingDomain") -> bool:
        """Merge variable tags from other domain into self, return True if changed."""
        changed = False
        all_variables = set(self.state._tags.keys()) | set(other.state._tags.keys())

        for variable in all_variables:
            self_tag = self.state.get_tag(variable)
            other_tag = other.state.get_tag(variable)

            if self_tag == other_tag:
                continue
            elif self_tag == RoundingTag.NEUTRAL:
                if other_tag != RoundingTag.NEUTRAL:
                    self.state.set_tag(variable, other_tag)
                    changed = True
            elif other_tag == RoundingTag.NEUTRAL:
                continue
            else:
                reason = f"Join conflict: {self_tag.name} vs {other_tag.name}"
                self.state.set_tag(variable, RoundingTag.UNKNOWN, unknown_reason=reason)
                changed = True

        return changed
