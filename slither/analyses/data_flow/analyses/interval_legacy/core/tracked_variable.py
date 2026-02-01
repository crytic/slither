"""Tracked SMT variable with overflow metadata management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Set, TYPE_CHECKING

from slither.analyses.data_flow.smt_solver.types import (
    SMTVariable,
    Sort,
    SortKind,
    SMTTerm,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


# Global set to track variables that need overflow assertions
# This avoids asserting the same constraints multiple times
_asserted_overflow_vars: Set[str] = set()


def reset_overflow_tracking() -> None:
    """Reset overflow tracking state (call at start of each analysis)."""
    global _asserted_overflow_vars
    _asserted_overflow_vars = set()


def get_pending_overflow_count() -> int:
    """Get the number of variables with overflow assertions."""
    return len(_asserted_overflow_vars)


@dataclass(eq=True)
class TrackedSMTVariable:
    """Wraps an SMT variable together with overflow tracking metadata."""

    base: SMTVariable
    overflow_flag: SMTVariable
    overflow_amount: SMTVariable

    # --------------------------------------------------------------------- #
    # Properties
    # --------------------------------------------------------------------- #
    @property
    def name(self) -> str:
        return self.base.name

    @property
    def sort(self) -> Sort:
        return self.base.sort

    @property
    def term(self) -> SMTTerm:
        return self.base.term

    # --------------------------------------------------------------------- #
    # Factory helpers
    # --------------------------------------------------------------------- #
    @classmethod
    def create(cls, solver: "SMTSolver", name: str, sort: Sort) -> "TrackedSMTVariable":
        """Declare a new tracked variable in the solver (or get existing one)."""
        base = solver.get_or_declare_const(name, sort)
        flag = cls._declare_aux_variable(solver, name, Sort(kind=SortKind.BOOL), "_overflow")
        amount = cls._declare_aux_variable(
            solver, name, Sort(kind=SortKind.INT), "_overflow_amount"
        )
        return cls(base=base, overflow_flag=flag, overflow_amount=amount)

    @classmethod
    def from_base(cls, solver: "SMTSolver", base: SMTVariable) -> "TrackedSMTVariable":
        """Wrap an existing SMT variable, ensuring overflow metadata exists."""
        flag = cls._declare_aux_variable(solver, base.name, Sort(kind=SortKind.BOOL), "_overflow")
        amount = cls._declare_aux_variable(
            solver, base.name, Sort(kind=SortKind.INT), "_overflow_amount"
        )
        return cls(base=base, overflow_flag=flag, overflow_amount=amount)

    # --------------------------------------------------------------------- #
    # Overflow operations
    # --------------------------------------------------------------------- #
    def assert_no_overflow(self, solver: "SMTSolver") -> None:
        """Assert that this variable has no overflow.

        Optimization: Tracks which variables have already been constrained to avoid
        duplicate constraint assertions (2 constraints per variable). This reduces
        solver memory usage and constraint checking overhead.
        """
        global _asserted_overflow_vars
        var_name = self.base.name

        # Skip if already asserted for this variable
        if var_name in _asserted_overflow_vars:
            return

        false_const = solver.create_constant(False, Sort(kind=SortKind.BOOL))
        solver.assert_constraint(self.overflow_flag.term == false_const)
        solver.assert_constraint(self.overflow_amount.term == 0)
        _asserted_overflow_vars.add(var_name)

    def copy_overflow_from(self, solver: "SMTSolver", other: "TrackedSMTVariable") -> None:
        solver.assert_constraint(self.overflow_flag.term == other.overflow_flag.term)
        solver.assert_constraint(self.overflow_amount.term == other.overflow_amount.term)

    def mark_overflow(
        self,
        solver: "SMTSolver",
        amount_term: SMTTerm,
    ) -> None:
        self.mark_overflow_condition(solver, True, amount_term)

    def mark_overflow_condition(
        self,
        solver: "SMTSolver",
        condition: SMTTerm,
        amount_term: SMTTerm,
    ) -> None:
        solver.assert_constraint(self.overflow_flag.term == condition)
        solver.assert_constraint(self.overflow_amount.term == amount_term)

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    @staticmethod
    def _declare_aux_variable(
        solver: "SMTSolver", base_name: str, sort: Sort, suffix: str
    ) -> SMTVariable:
        """Declare an auxiliary overflow variable if not already present."""
        name = f"{base_name}{suffix}"
        existing = solver.get_variable(name)
        if existing is not None:
            return existing
        return solver.declare_const(name, sort)
