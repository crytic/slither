from typing import Mapping, Dict, Optional

from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable


class State:
    """Represents the state of variables in range analysis."""

    def __init__(self, range_variables: Mapping[str, RangeVariable]):
        self.range_variables: Dict[str, RangeVariable] = dict(range_variables)  # Make mutable copy

    def get_range_variable(self, name: str) -> Optional[RangeVariable]:
        """Get a range variable by name, returns None if not found."""
        return self.range_variables.get(name)

    def has_range_variable(self, name: str) -> bool:
        """Check if a range variable exists in the state."""
        return name in self.range_variables

    def get_range_variables(self) -> Dict[str, RangeVariable]:
        """Get all range variables in the state."""
        return self.range_variables

    def set_range_variable(self, name: str, range_variable: RangeVariable) -> None:
        """Set a range variable by name."""
        self.range_variables[name] = range_variable

    def add_range_variable(self, name: str, range_variable: RangeVariable) -> None:
        """Add a new range variable to the state."""
        self.range_variables[name] = range_variable

    def remove_range_variable(self, name: str) -> bool:
        """Remove a range variable by name, returns True if removed."""
        if name in self.range_variables:
            del self.range_variables[name]
            return True
        return False

    def clear_range_variables(self) -> None:
        """Clear all range variables from the state."""
        self.range_variables.clear()

    def __eq__(self, other) -> bool:
        if not isinstance(other, State):
            return False
        return self.range_variables == other.range_variables

    def __hash__(self) -> int:
        # Hash based on sorted items for consistent ordering
        return hash(tuple(sorted(self.range_variables.items())))

    def deep_copy(self) -> "State":
        """Create a deep copy of the state"""
        copied_vars = {name: var.deep_copy() for name, var in self.range_variables.items()}
        return State(copied_vars)
