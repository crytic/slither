from typing import Dict, Mapping, Optional

from slither.analyses.data_flow.smt_solver.types import SMTVariable


class State:
    """Represents the state of variables in range analysis using SMT variables."""

    def __init__(self, range_variables: Optional[Mapping[str, SMTVariable]] = None):
        if range_variables is None:
            range_variables = {}
        self.range_variables: Dict[str, SMTVariable] = dict(range_variables)  # Make mutable copy

    def get_range_variable(self, name: str) -> Optional[SMTVariable]:
        """Get an SMT variable by name, returns None if not found."""
        return self.range_variables.get(name)

    def has_range_variable(self, name: str) -> bool:
        """Check if an SMT variable exists in the state."""
        return name in self.range_variables

    def get_range_variables(self) -> Dict[str, SMTVariable]:
        """Get all SMT variables in the state."""
        return self.range_variables

    def set_range_variable(self, name: str, smt_variable: SMTVariable) -> None:
        """Set an SMT variable by name."""
        self.range_variables[name] = smt_variable

    def add_range_variable(self, name: str, smt_variable: SMTVariable) -> None:
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
            # Compare SMTVariables using their __eq__ method
            if smt_var != other.range_variables[name]:
                return False
        return True

    def __hash__(self) -> int:
        # Hash based on variable names and SMTVariable hashes
        # Sort items for consistent ordering
        items = sorted((name, hash(smt_var)) for name, smt_var in self.range_variables.items())
        return hash(tuple(items))

    def deep_copy(self) -> "State":
        """Create a deep copy of the state"""
        # SMTVariables are immutable, so we can just copy the dict reference
        # However, we create a new dict to allow independent mutation of the dict itself
        copied_vars = dict(self.range_variables)
        new_state = State(copied_vars)
        return new_state
