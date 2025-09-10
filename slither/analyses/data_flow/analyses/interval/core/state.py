from typing import Mapping, Dict

from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable


class State:
    """Represents the state of variables in range analysis."""

    def __init__(self, variables: Mapping[str, RangeVariable]):
        self.variables: Dict[str, RangeVariable] = dict(variables)  # Make mutable copy

    def __eq__(self, other) -> bool:
        if not isinstance(other, State):
            return False
        return self.variables == other.variables

    def __hash__(self) -> int:
        # Hash based on sorted items for consistent ordering
        return hash(tuple(sorted(self.variables.items())))

    def deep_copy(self) -> "State":
        """Create a deep copy of the state"""
        copied_vars = {name: var.deep_copy() for name, var in self.variables.items()}
        return State(copied_vars)
