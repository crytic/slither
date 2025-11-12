"""Tracked SMT variable with overflow metadata management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.smt_solver.types import (
    SMTVariable,
    Sort,
    SortKind,
    SMTTerm,
)

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


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
        """Declare a new tracked variable in the solver."""
        base = solver.declare_const(name, sort)
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
        solver.assert_constraint(self.overflow_flag.term == False)
        solver.assert_constraint(self.overflow_amount.term == 0)

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
