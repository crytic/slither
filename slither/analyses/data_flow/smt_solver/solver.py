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
