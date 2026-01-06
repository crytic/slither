"""Abstract SMT solver interface following SMT-LIB 2.0 standard."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .types import SMTVariable, Sort, CheckSatResult, SMTTerm


class SMTSolver(ABC):
    """
    Abstract SMT solver following SMT-LIB 2.0 standard.

    Reference: https://smt-lib.org/

    Core SMT-LIB commands implemented:
    - (declare-const name sort)
    - (assert constraint)
    - (check-sat)
    - (get-model)
    - (get-value (term1 term2 ...))
    - (push n)
    - (pop n)
    - (reset)

    Extensions for optimization:
    - (maximize term)
    - (minimize term)
    """

    def __init__(self) -> None:
        self.variables: Dict[str, SMTVariable] = {}
        self.assertions: List[SMTTerm] = []

    # ========================================================================
    # Core SMT-LIB 2.0 Commands
    # ========================================================================

    @abstractmethod
    def declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """
        (declare-const name sort)

        Declare a constant with given name and sort.
        Returns an SMTVariable object containing the solver-specific term.
        Raises ValueError if the variable is already declared.
        """
        pass

    @abstractmethod
    def get_or_declare_const(self, name: str, sort: Sort) -> SMTVariable:
        """
        Get an existing constant or declare a new one if it doesn't exist.

        This is useful for worklist algorithms where the same variable
        may be encountered multiple times.
        """
        pass

    @abstractmethod
    def create_constant(self, value: int, sort: Sort) -> SMTTerm:
        """
        Create a constant value term.

        Args:
            value: The integer value
            sort: The sort (type) of the constant

        Returns:
            An SMTTerm representing the constant value
        """
        pass

    @abstractmethod
    def is_bitvector(self, term: SMTTerm) -> bool:
        """Return True if the solver term is a bitvector."""
        pass

    @abstractmethod
    def bitvector_to_int(self, term: SMTTerm) -> SMTTerm:
        """Convert a bitvector term into the solver's integer domain."""
        pass

    @abstractmethod
    def bitvector_to_signed_int(self, term: SMTTerm) -> SMTTerm:
        """Convert a bitvector term into a signed integer representation."""
        pass

    @abstractmethod
    def make_ite(self, condition: SMTTerm, then_term: SMTTerm, else_term: SMTTerm) -> SMTTerm:
        """Create an if-then-else expression."""
        pass

    @abstractmethod
    def Or(self, *terms: SMTTerm) -> SMTTerm:
        """Create a disjunction (OR) of multiple boolean terms."""
        pass

    @abstractmethod
    def Not(self, term: SMTTerm) -> SMTTerm:
        """Create a negation (NOT) of a boolean term."""
        pass

    @abstractmethod
    def bv_udiv(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned division for bitvectors."""
        pass

    @abstractmethod
    def bv_urem(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned remainder for bitvectors."""
        pass

    @abstractmethod
    def bv_lshr(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Logical right shift for bitvectors."""
        pass

    @abstractmethod
    def bv_sign_ext(self, term: SMTTerm, extra_bits: int) -> SMTTerm:
        """Sign-extend a bitvector by extra_bits."""
        pass

    @abstractmethod
    def bv_zero_ext(self, term: SMTTerm, extra_bits: int) -> SMTTerm:
        """Zero-extend a bitvector by extra_bits."""
        pass

    @abstractmethod
    def bv_extract(self, term: SMTTerm, high: int, low: int) -> SMTTerm:
        """Extract bits [high:low] from a bitvector."""
        pass

    @abstractmethod
    def bv_ult(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Unsigned less-than comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_slt(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Signed less-than comparison for bitvectors."""
        pass

    @abstractmethod
    def bv_size(self, term: SMTTerm) -> int:
        """Get the bit-width of a bitvector term."""
        pass

    @abstractmethod
    def bv_concat(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Concatenate two bitvectors."""
        pass

    @abstractmethod
    def bv_not(self, term: SMTTerm) -> SMTTerm:
        """Bitwise NOT for bitvectors."""
        pass

    @abstractmethod
    def assert_constraint(self, constraint: SMTTerm) -> None:
        """
        (assert constraint)

        Assert a constraint (boolean formula) to the solver.
        """
        pass

    @abstractmethod
    def check_sat(self) -> CheckSatResult:
        """
        (check-sat)

        Check satisfiability of current assertions.
        Returns: SAT, UNSAT, or UNKNOWN
        """
        pass

    @abstractmethod
    def get_model(self) -> Optional[Dict[str, SMTTerm]]:
        """
        (get-model)

        Get model (variable assignments) if last check-sat was SAT.
        Returns: Dictionary mapping variable names to their values
        """
        pass

    @abstractmethod
    def get_value(self, terms: List[SMTTerm]) -> Optional[Dict[SMTTerm, SMTTerm]]:
        """
        (get-value (term1 term2 ...))

        Get values of specific terms in the current model.
        Returns: Dictionary mapping terms to their values
        """
        pass

    @abstractmethod
    def push(self, levels: int = 1) -> None:
        """
        (push n)

        Push n levels onto the assertion stack.
        Creates a backtracking point.
        """
        pass

    @abstractmethod
    def pop(self, levels: int = 1) -> None:
        """
        (pop n)

        Pop n levels from the assertion stack.
        Backtracks to previous state.
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        (reset)

        Reset the solver to initial state.
        Clears all declarations and assertions.
        """
        pass

    # ========================================================================
    # Optimization Extensions (not in core SMT-LIB but common)
    # ========================================================================

    @abstractmethod
    def maximize(self, term: SMTTerm) -> None:
        """
        (maximize term)

        Add objective to maximize the given term.
        Requires optimization-capable solver.
        """
        pass

    @abstractmethod
    def minimize(self, term: SMTTerm) -> None:
        """
        (minimize term)

        Add objective to minimize the given term.
        Requires optimization-capable solver.
        """
        pass

    # ========================================================================
    # Helper Methods (not SMT-LIB commands)
    # ========================================================================

    def get_variable(self, name: str) -> Optional[SMTVariable]:
        """Get a declared variable by name"""
        return self.variables.get(name)

    def list_variables(self) -> List[str]:
        """List all declared variable names"""
        return list(self.variables.keys())

    def get_assertions(self) -> List[SMTTerm]:
        """Get all current assertions"""
        return self.assertions.copy()

    @abstractmethod
    def to_smtlib(self) -> str:
        """
        Export current state as SMT-LIB 2.0 format string.
        Useful for debugging or using with other solvers.
        """
        pass
