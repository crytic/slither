from typing import Dict, Mapping, Optional

from .tracked_variable import TrackedSMTVariable


class State:
    """Represents the state of variables in range analysis using SMT variables."""

    def __init__(self, range_variables: Optional[Mapping[str, TrackedSMTVariable]] = None):
        if range_variables is None:
            range_variables = {}
        self.range_variables: Dict[str, TrackedSMTVariable] = dict(
            range_variables
        )  # Make mutable copy

    def get_range_variable(self, name: str) -> Optional[TrackedSMTVariable]:
        """Get an SMT variable by name, returns None if not found."""
        return self.range_variables.get(name)

    def has_range_variable(self, name: str) -> bool:
        """Check if an SMT variable exists in the state."""
        return name in self.range_variables

    def get_range_variables(self) -> Dict[str, TrackedSMTVariable]:
        """Get all SMT variables in the state."""
        return self.range_variables

    def set_range_variable(self, name: str, smt_variable: TrackedSMTVariable) -> None:
        """Set an SMT variable by name."""
        self.range_variables[name] = smt_variable

    def add_range_variable(self, name: str, smt_variable: TrackedSMTVariable) -> None:
        """Add a new SMT variable to the state."""
        self.range_variables[name] = smt_variable

    def remove_range_variable(self, name: str) -> bool:
        """Remove a range variable by name, returns True if removed."""
        if name in self.range_variables:
            del self.range_variables[name]
            return True
        return False

    def clear_range_variables(self) -> None:
        """Clear all range variables from the state."""
        self.range_variables.clear()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, State):
            return False
        # SMTVariables are compared by their equality method (name + type)
        if len(self.range_variables) != len(other.range_variables):
            return False
        for name, smt_var in self.range_variables.items():
            if name not in other.range_variables:
                return False
            # Compare TrackedSMTVariables using their equality method
            if smt_var != other.range_variables[name]:
                return False
        return True

    def __hash__(self) -> int:
        # Hash based on variable names and SMTVariable hashes
        # Sort items for consistent ordering
        items = sorted(
            (name, hash((smt_var.base, smt_var.overflow_flag, smt_var.overflow_amount)))
            for name, smt_var in self.range_variables.items()
        )
        return hash(tuple(items))

    def deep_copy(self) -> "State":
        """Create a deep copy of the state"""
        copied_vars = {
            name: TrackedSMTVariable(
                base=value.base,
                overflow_flag=value.overflow_flag,
                overflow_amount=value.overflow_amount,
            )
            for name, value in self.range_variables.items()
        }
        return State(copied_vars)
