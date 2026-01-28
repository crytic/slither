from typing import Dict, List, Mapping, Optional, TYPE_CHECKING

from .tracked_variable import TrackedSMTVariable

if TYPE_CHECKING:
    from slither.slithir.operations.binary import Binary
    from slither.analyses.data_flow.smt_solver.types import SMTTerm


class State:
    """Represents the state of variables in range analysis using SMT variables."""

    def __init__(
        self,
        range_variables: Optional[Mapping[str, TrackedSMTVariable]] = None,
        binary_operations: Optional[Mapping[str, "Binary"]] = None,
        path_constraints: Optional[List["SMTTerm"]] = None,
        bytes_memory_constants: Optional[Dict[str, bytes]] = None,
        var_by_prefix: Optional[Dict[str, set[str]]] = None,
    ):
        if range_variables is None:
            range_variables = {}
        self.range_variables: Dict[str, TrackedSMTVariable] = dict(
            range_variables
        )  # Make mutable copy
        if binary_operations is None:
            binary_operations = {}
        self.binary_operations: Dict[str, "Binary"] = dict(
            binary_operations
        )  # Maps temp variable names to their source Binary operations
        self.used_variables: set[str] = set()  # Track which variables are actually used/read
        # Path constraints: branch conditions that must hold for this state
        self.path_constraints: List["SMTTerm"] = list(path_constraints) if path_constraints else []
        # Track bytes memory constants: maps variable name to its concrete byte content
        if bytes_memory_constants is None:
            bytes_memory_constants = {}
        self.bytes_memory_constants: Dict[str, bytes] = dict(bytes_memory_constants)
        # Index for fast prefix-based lookups: prefix -> set of variable names
        # e.g., "struct." -> {"struct.a", "struct.b"}, "array[" -> {"array[0]", "array[1]"}
        if var_by_prefix is None:
            self._var_by_prefix: Dict[str, set[str]] = {}
            # Build index from existing variables
            for name in self.range_variables:
                self._index_variable(name)
        else:
            self._var_by_prefix = {k: set(v) for k, v in var_by_prefix.items()}

    def _index_variable(self, name: str) -> None:
        """Add a variable name to the prefix index."""
        # Index by struct prefix (e.g., "MyStruct.member" -> prefix "MyStruct.")
        if "." in name:
            prefix = name.split(".", 1)[0] + "."
            if prefix not in self._var_by_prefix:
                self._var_by_prefix[prefix] = set()
            self._var_by_prefix[prefix].add(name)
        # Index by array prefix (e.g., "myArray[0]" -> prefix "myArray[")
        if "[" in name:
            prefix = name.split("[", 1)[0] + "["
            if prefix not in self._var_by_prefix:
                self._var_by_prefix[prefix] = set()
            self._var_by_prefix[prefix].add(name)

    def _unindex_variable(self, name: str) -> None:
        """Remove a variable name from the prefix index."""
        if "." in name:
            prefix = name.split(".", 1)[0] + "."
            if prefix in self._var_by_prefix:
                self._var_by_prefix[prefix].discard(name)
        if "[" in name:
            prefix = name.split("[", 1)[0] + "["
            if prefix in self._var_by_prefix:
                self._var_by_prefix[prefix].discard(name)

    def get_variables_by_prefix(self, prefix: str) -> set[str]:
        """Get all variable names that start with a given prefix.

        Args:
            prefix: The prefix to search for (e.g., "MyStruct." or "myArray[")

        Returns:
            Set of variable names matching the prefix (may be empty)
        """
        return self._var_by_prefix.get(prefix, set()).copy()

    def get_range_variable(self, name: str) -> Optional[TrackedSMTVariable]:
        """Get an SMT variable by name, returns None if not found."""
        var = self.range_variables.get(name)
        if var is not None:
            # Mark variable as used when it's retrieved
            self.used_variables.add(name)
        return var

    def has_range_variable(self, name: str) -> bool:
        """Check if an SMT variable exists in the state."""
        return name in self.range_variables

    def get_range_variables(self) -> Dict[str, TrackedSMTVariable]:
        """Get all SMT variables in the state."""
        return self.range_variables

    def set_range_variable(self, name: str, smt_variable: TrackedSMTVariable) -> None:
        """Set an SMT variable by name."""
        # Update prefix index if this is a new variable
        if name not in self.range_variables:
            self._index_variable(name)
        self.range_variables[name] = smt_variable
        # Mark as used when set (written to during analysis)
        self.used_variables.add(name)

    def add_range_variable(self, name: str, smt_variable: TrackedSMTVariable) -> None:
        """Add a new SMT variable to the state (without marking as used - for initialization)."""
        # Update prefix index if this is a new variable
        if name not in self.range_variables:
            self._index_variable(name)
        self.range_variables[name] = smt_variable
        # Don't mark as used - this is for initialization, not actual usage

    def set_binary_operation(self, var_name: str, operation: "Binary") -> None:
        """Store a Binary operation that produced a temporary variable."""
        self.binary_operations[var_name] = operation

    def get_binary_operation(self, var_name: str) -> Optional["Binary"]:
        """Retrieve the Binary operation that produced a temporary variable."""
        return self.binary_operations.get(var_name)

    def has_binary_operation(self, var_name: str) -> bool:
        """Check if a Binary operation exists for a variable name."""
        return var_name in self.binary_operations

    def get_binary_operations(self) -> Dict[str, "Binary"]:
        """Get all Binary operations in the state."""
        return self.binary_operations

    def add_path_constraint(self, constraint: "SMTTerm") -> None:
        """Add a path constraint that must hold for this state."""
        self.path_constraints.append(constraint)

    def get_path_constraints(self) -> List["SMTTerm"]:
        """Get all path constraints for this state."""
        return self.path_constraints

    def remove_range_variable(self, name: str) -> bool:
        """Remove a range variable by name, returns True if removed."""
        if name in self.range_variables:
            self._unindex_variable(name)
            del self.range_variables[name]
            return True
        return False

    def clear_range_variables(self) -> None:
        """Clear all range variables from the state."""
        self.range_variables.clear()
        self._var_by_prefix.clear()

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
        # Compare binary operations (by identity since operations are not directly comparable)
        if len(self.binary_operations) != len(other.binary_operations):
            return False
        for name, op in self.binary_operations.items():
            if name not in other.binary_operations:
                return False
            # Compare operations by identity (same object reference)
            if op is not other.binary_operations[name]:
                return False
        return True

    def __hash__(self) -> int:
        # Hash based on variable names and SMTVariable hashes
        # Sort items for consistent ordering
        items = sorted(
            (name, hash((smt_var.base, smt_var.overflow_flag, smt_var.overflow_amount)))
            for name, smt_var in self.range_variables.items()
        )
        # Include binary operations in hash (using id for object identity)
        op_items = sorted((name, id(op)) for name, op in self.binary_operations.items())
        return hash((tuple(items), tuple(op_items)))

    def get_used_variables(self) -> set[str]:
        """Get the set of variables that were actually used/read."""
        return self.used_variables

    def set_bytes_memory_constant(self, var_name: str, byte_content: bytes) -> None:
        """Store the concrete byte content for a bytes memory constant variable."""
        self.bytes_memory_constants[var_name] = byte_content

    def get_bytes_memory_constant(self, var_name: str) -> Optional[bytes]:
        """Get the concrete byte content for a bytes memory constant variable."""
        return self.bytes_memory_constants.get(var_name)

    def has_bytes_memory_constant(self, var_name: str) -> bool:
        """Check if a bytes memory constant exists for a variable."""
        return var_name in self.bytes_memory_constants

    def get_bytes_memory_constants(self) -> Dict[str, bytes]:
        """Get all bytes memory constants."""
        return self.bytes_memory_constants

    def deep_copy(self) -> "State":
        """Create a deep copy of the state.

        Optimization: TrackedSMTVariable objects are effectively immutable (they wrap
        immutable SMT terms), so we can share them directly instead of creating new
        wrapper instances. This avoids O(n) object allocations on every branch merge.
        """
        # Share TrackedSMTVariable references directly - they are immutable
        copied_vars = dict(self.range_variables)
        # Binary operations are copied by reference (they're immutable operation objects)
        copied_ops = dict(self.binary_operations)
        # Path constraints are SMT terms (immutable), copy the list
        copied_constraints = list(self.path_constraints)
        # Copy bytes memory constants
        copied_bytes_constants = dict(self.bytes_memory_constants)
        # Copy prefix index (shallow copy of sets)
        copied_prefix_index = {k: set(v) for k, v in self._var_by_prefix.items()}
        new_state = State(copied_vars, copied_ops, copied_constraints, copied_bytes_constants, copied_prefix_index)
        # Copy used variables set
        new_state.used_variables = set(self.used_variables)
        return new_state
