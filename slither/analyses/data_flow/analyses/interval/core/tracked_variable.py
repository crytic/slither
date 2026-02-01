"""Tracked SMT variable wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from slither.analyses.data_flow.smt_solver.types import SMTVariable, Sort, SMTTerm

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


@dataclass(eq=True)
class TrackedSMTVariable:
    """SMT variable wrapper for interval analysis.

    Tracks an SMT variable along with optional overflow predicates
    from the operation that produced it.

    Attributes:
        base: The underlying SMT variable.
        no_overflow: Predicate that is True when the operation does not overflow.
        no_underflow: Predicate that is True when the operation does not underflow.
    """

    base: SMTVariable
    no_overflow: Optional[SMTTerm] = field(default=None, compare=False)
    no_underflow: Optional[SMTTerm] = field(default=None, compare=False)

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
        is_signed: bool = False,
        bit_width: int | None = None,
    ) -> "TrackedSMTVariable":
        """Create a new tracked variable without overflow predicates.

        Args:
            solver: The SMT solver instance.
            name: Variable name.
            sort: SMT sort (type).
            is_signed: Whether this is a signed integer type.
            bit_width: Bit width for bitvector types.
        """
        base = solver.get_or_declare_const(name, sort)
        # Set metadata for range solving
        base.metadata["is_signed"] = is_signed
        if bit_width is not None:
            base.metadata["bit_width"] = bit_width
        return cls(base=base)

    def with_overflow_predicates(
        self,
        no_overflow: Optional[SMTTerm] = None,
        no_underflow: Optional[SMTTerm] = None,
    ) -> "TrackedSMTVariable":
        """Return a copy with overflow predicates set."""
        return TrackedSMTVariable(
            base=self.base,
            no_overflow=no_overflow,
            no_underflow=no_underflow,
        )
