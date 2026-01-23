import copy
from enum import Enum, auto
from typing import Dict, Optional

from slither.core.variables.variable import Variable
from slither.slithir.operations.operation import Operation


class RoundingTag(Enum):
    """Rounding direction metadata for variables"""

    UP = auto()  # Value was computed rounding up (ceiling)
    DOWN = auto()  # Value was computed rounding down (floor/truncation)
    NEUTRAL = auto()  # No rounding information (default starting tag)
    UNKNOWN = auto()  # Direction unclear or mixed


class RoundingState:
    """Track rounding metadata for variables as they flow through the program"""

    def __init__(self):
        self._tags: Dict[Variable, RoundingTag] = {}
        # Track which operation produced each variable (for pattern detection)
        self._producers: Dict[Variable, Optional[Operation]] = {}
        # Track reasons for UNKNOWN tags
        self._unknown_reasons: Dict[Variable, str] = {}

    def set_tag(
        self, var: Variable, tag: RoundingTag, producer: Optional[Operation] = None, unknown_reason: Optional[str] = None
    ) -> None:
        """Assign a rounding tag to a variable and optionally track the operation that produced it"""
        self._tags[var] = tag
        if producer is not None:
            self._producers[var] = producer
        if tag == RoundingTag.UNKNOWN and unknown_reason:
            self._unknown_reasons[var] = unknown_reason
        elif tag != RoundingTag.UNKNOWN:
            # Remove reason if tag is no longer UNKNOWN
            self._unknown_reasons.pop(var, None)

    def get_tag(self, var: Variable) -> RoundingTag:
        """Get the tag for a variable (default NEUTRAL)"""
        return self._tags.get(var, RoundingTag.NEUTRAL)

    def get_producer(self, var: Variable) -> Optional[Operation]:
        """Get the operation that produced a variable (if tracked)"""
        return self._producers.get(var, None)

    def get_unknown_reason(self, var: Variable) -> Optional[str]:
        """Get the reason why a variable has an UNKNOWN tag, if available"""
        return self._unknown_reasons.get(var, None)

    def deep_copy(self) -> "RoundingState":
        """Create a deep copy of the state"""
        new_state = RoundingState()
        new_state._tags = copy.copy(self._tags)
        new_state._producers = copy.copy(self._producers)
        new_state._unknown_reasons = copy.copy(self._unknown_reasons)
        return new_state

    def __eq__(self, other) -> bool:
        if not isinstance(other, RoundingState):
            return False
        return self._tags == other._tags

    def __hash__(self) -> int:
        # Convert to frozenset of tuples for hashing
        return hash(frozenset(self._tags.items()))

    def __str__(self) -> str:
        tag_strs = [f"{var.name}: {tag.name}" for var, tag in self._tags.items()]
        return f"RoundingState({len(self._tags)} variables: {', '.join(tag_strs)})"
