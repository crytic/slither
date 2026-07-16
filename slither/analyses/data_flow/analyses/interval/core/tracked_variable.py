"""Tracked SMT variable wrapper."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from slither.analyses.data_flow.smt_solver.facts import StaticOperationId
from slither.analyses.data_flow.smt_solver.types import SMTVariable, Sort, SMTTerm

if TYPE_CHECKING:
    from slither.analyses.data_flow.smt_solver.solver import SMTSolver


@dataclass(frozen=True, order=True)
class NumericInterval:
    """Closed integer interval used as the numeric abstract value."""

    lower: int
    upper: int

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise ValueError("Interval lower bound cannot exceed its upper bound")

    @classmethod
    def type_range(cls, bit_width: int, is_signed: bool) -> NumericInterval:
        """Return the full representable range for one bit-vector type."""
        if bit_width <= 0:
            raise ValueError("Bit width must be positive")
        if is_signed:
            return cls(-(1 << (bit_width - 1)), (1 << (bit_width - 1)) - 1)
        return cls(0, (1 << bit_width) - 1)

    def hull(self, other: NumericInterval) -> NumericInterval:
        """Return the least interval containing both operands."""
        return NumericInterval(min(self.lower, other.lower), max(self.upper, other.upper))

    def intersection(self, other: NumericInterval) -> NumericInterval | None:
        """Return the common interval, or ``None`` when it is empty."""
        lower = max(self.lower, other.lower)
        upper = min(self.upper, other.upper)
        if lower > upper:
            return None
        return NumericInterval(lower, upper)


@dataclass(frozen=True, eq=False)
class TrackedSMTVariable:
    """SMT variable wrapper for interval analysis.

    Tracks an SMT variable along with optional overflow predicates
    from the operation that produced it.

    Attributes:
        base: The underlying SMT variable.
        no_overflow: Predicate that is True when the operation does not overflow.
        no_underflow: Predicate that is True when the operation does not underflow.
        is_unchecked: True if from unchecked context (assembly/unchecked block).
    """

    base: SMTVariable
    interval: NumericInterval
    is_total: bool = True
    no_overflow: SMTTerm | None = field(default=None, compare=False)
    no_underflow: SMTTerm | None = field(default=None, compare=False)
    overflow_operation_id: StaticOperationId | None = None
    is_unchecked: bool = field(default=False, compare=False)

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
        solver: SMTSolver,
        name: str,
        sort: Sort,
        is_signed: bool = False,
        bit_width: int | None = None,
    ) -> TrackedSMTVariable:
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
        return cls(
            base=base,
            interval=NumericInterval.type_range(bit_width or sort.parameters[0], is_signed),
        )

    @property
    def type_interval(self) -> NumericInterval:
        """Return the full representable range for this variable's type."""
        bit_width = self.base.metadata.get("bit_width")
        if not isinstance(bit_width, int):
            if not self.sort.parameters:
                raise ValueError(f"Variable {self.name!r} has no bit width")
            bit_width = self.sort.parameters[0]
        is_signed = bool(self.base.metadata.get("is_signed", False))
        return NumericInterval.type_range(bit_width, is_signed)

    def with_interval(
        self,
        interval: NumericInterval,
        *,
        is_total: bool | None = None,
    ) -> TrackedSMTVariable:
        """Return a copy carrying a new abstract interval and path totality."""
        if interval.intersection(self.type_interval) != interval:
            raise ValueError(f"Interval {interval!r} is outside the type range for {self.name!r}")
        return TrackedSMTVariable(
            base=self.base,
            interval=interval,
            is_total=self.is_total if is_total is None else is_total,
            no_overflow=self.no_overflow,
            no_underflow=self.no_underflow,
            overflow_operation_id=self.overflow_operation_id,
            is_unchecked=self.is_unchecked,
        )

    def as_path_optional(self) -> TrackedSMTVariable:
        """Retain definition bounds while marking the SSA value path-optional."""
        return self.with_interval(self.interval, is_total=False)

    def with_overflow_predicates(
        self,
        no_overflow: SMTTerm | None = None,
        no_underflow: SMTTerm | None = None,
        operation_id: StaticOperationId | None = None,
        is_unchecked: bool = False,
    ) -> TrackedSMTVariable:
        """Return a copy with overflow predicates set."""
        if (no_overflow is not None or no_underflow is not None) and operation_id is None:
            raise ValueError("Overflow predicates require a stable operation identity")
        return TrackedSMTVariable(
            base=self.base,
            interval=self.interval,
            is_total=self.is_total,
            no_overflow=no_overflow,
            no_underflow=no_underflow,
            overflow_operation_id=operation_id,
            is_unchecked=is_unchecked,
        )
