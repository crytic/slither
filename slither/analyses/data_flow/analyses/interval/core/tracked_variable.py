"""Tracked SMT variable wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from slither.analyses.data_flow.smt_solver.types import SMTVariable, Sort, SMTTerm

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


@dataclass(eq=True)
class TrackedSMTVariable:
    """SMT variable wrapper for interval analysis.

    Currently holds just the base variable. Overflow tracking fields
    will be added when Binary operations are implemented.
    """

    base: SMTVariable

    @property
    def name(self) -> str:
        return self.base.name

    @property
    def sort(self) -> Sort:
        return self.base.sort

    @property
    def term(self) -> SMTTerm:
        return self.base.term

    @classmethod
    def create(
        cls,
        solver: "SMTSolver",
        name: str,
        sort: Sort,
    ) -> "TrackedSMTVariable":
        """Create a new tracked variable."""
        base = solver.get_or_declare_const(name, sort)
        return cls(base=base)
