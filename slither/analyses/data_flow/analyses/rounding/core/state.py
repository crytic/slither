import copy
from enum import Enum, auto
from typing import Dict, Optional

from slither.core.variables.variable import Variable


class RoundingTag(Enum):
    """Rounding direction metadata for variables"""

    UP = auto()  # Value was computed rounding up (ceiling)
    DOWN = auto()  # Value was computed rounding down (floor/truncation)
    UNKNOWN = auto()  # Direction unclear or mixed


class RoundingState:
    """Track rounding metadata for variables as they flow through the program"""

    def __init__(self):
        self._tags: Dict[Variable, RoundingTag] = {}

    def set_tag(self, var: Variable, tag: RoundingTag) -> None:
        """Assign a rounding tag to a variable"""
        self._tags[var] = tag

    def get_tag(self, var: Variable) -> RoundingTag:
        """Get the tag for a variable (default UNKNOWN)"""
        return self._tags.get(var, RoundingTag.UNKNOWN)

    def deep_copy(self) -> "RoundingState":
        """Create a deep copy of the state"""
        new_state = RoundingState()
        new_state._tags = copy.copy(self._tags)
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
