import copy
from enum import Enum, auto
from typing import Dict, FrozenSet, Optional, Union

from slither.core.variables.variable import Variable
from slither.slithir.operations.operation import Operation


class RoundingTag(Enum):
    """Rounding direction metadata for variables."""

    UP = auto()  # Value was computed rounding up (ceiling)
    DOWN = auto()  # Value was computed rounding down (floor/truncation)
    NEUTRAL = auto()  # No rounding information (default starting tag)
    UNKNOWN = auto()  # Direction unclear or mixed


TagSet = FrozenSet[RoundingTag]


class RoundingState:
    """Track rounding metadata for variables as they flow through the program."""

    def __init__(self):
        self._tags: Dict[Variable, TagSet] = {}
        # Track which operation produced each variable (for pattern detection)
        self._producers: Dict[Variable, Optional[Operation]] = {}
        # Track reasons for UNKNOWN tags
        self._unknown_reasons: Dict[Variable, str] = {}

    def set_tag(
        self,
        variable: Variable,
        tag: Union[RoundingTag, TagSet],
        producer: Optional[Operation] = None,
        unknown_reason: Optional[str] = None,
    ) -> None:
        """Assign a rounding tag or tag set to a variable.

        Accepts a single RoundingTag or a TagSet. Single tags are normalized
        to TagSet for internal storage. Optionally tracks the operation that
        produced it.
        """
        tag_set: TagSet
        if isinstance(tag, RoundingTag):
            tag_set = frozenset({tag})
        else:
            tag_set = tag
        self._tags[variable] = tag_set
        if producer is not None:
            self._producers[variable] = producer
        if RoundingTag.UNKNOWN in tag_set and unknown_reason:
            self._unknown_reasons[variable] = unknown_reason
        elif RoundingTag.UNKNOWN not in tag_set:
            self._unknown_reasons.pop(variable, None)

    def get_tags(self, variable: Variable) -> TagSet:
        """Get the tag set for a variable (default {NEUTRAL})."""
        return self._tags.get(variable, frozenset({RoundingTag.NEUTRAL}))

    def get_tag(self, variable: Variable) -> RoundingTag:
        """Get a single tag for a variable (backward compatibility).

        Returns the single tag if only one exists, otherwise UNKNOWN.
        """
        tags = self.get_tags(variable)
        if len(tags) == 1:
            return next(iter(tags))
        return RoundingTag.UNKNOWN

    def get_producer(self, variable: Variable) -> Optional[Operation]:
        """Get the operation that produced a variable (if tracked)."""
        return self._producers.get(variable, None)

    def get_unknown_reason(self, variable: Variable) -> Optional[str]:
        """Get the reason why a variable has an UNKNOWN tag, if available."""
        return self._unknown_reasons.get(variable, None)

    def deep_copy(self) -> "RoundingState":
        """Create a deep copy of the state."""
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
        tag_strings = []
        for variable, tags in self._tags.items():
            if len(tags) == 1:
                tag_strings.append(f"{variable.name}: {next(iter(tags)).name}")
            else:
                names = sorted(tag.name for tag in tags)
                tag_strings.append(f"{variable.name}: {{{', '.join(names)}}}")
        return f"RoundingState({len(self._tags)} variables: {', '.join(tag_strings)})"
