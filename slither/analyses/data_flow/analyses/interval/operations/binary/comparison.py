"""Comparison binary operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant

from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_variable_name,
    is_signed_type,
    get_bit_width,
    constant_to_term,
    try_create_parameter_variable,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.core.state import ComparisonInfo

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )

COMPARISON_OPERATIONS = frozenset({
    BinaryType.LESS,
    BinaryType.GREATER,
    BinaryType.LESS_EQUAL,
    BinaryType.GREATER_EQUAL,
    BinaryType.EQUAL,
    BinaryType.NOT_EQUAL,
    BinaryType.ANDAND,
    BinaryType.OROR,
})


class ComparisonHandler(BaseOperationHandler):
    """Handler for comparison binary operations.

    Supports: <, >, <=, >=, ==, !=, &&, ||
    """

    def handle(
        self,
        operation: Binary,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process comparison binary operation."""
        result_name = get_variable_name(operation.lvalue)
        result_var = self._create_result_variable(result_name)

        operand_width = self._get_operand_width(operation)
        left_term = self._resolve_operand(operation.variable_left, domain, operand_width)
        right_term = self._resolve_operand(operation.variable_right, domain, operand_width)

        if left_term is None or right_term is None:
            domain.state.set_variable(result_name, result_var)
            return

        is_signed = self._operands_are_signed(operation)
        condition = self._compute_condition(operation.type, left_term, right_term, is_signed)

        if condition is not None:
            result_term = self._bool_to_bitvector(condition)
            self.solver.assert_constraint(result_var.term == result_term)
            # Store comparison info for condition narrowing
            domain.state.set_comparison(result_name, ComparisonInfo(condition))

        domain.state.set_variable(result_name, result_var)

    def _create_result_variable(self, name: str) -> TrackedSMTVariable:
        """Create a 1-bit result variable for boolean result."""
        sort = Sort(kind=SortKind.BITVEC, parameters=[1])
        return TrackedSMTVariable.create(
            self.solver, name, sort, is_signed=False, bit_width=1
        )

    def _get_operand_width(self, operation: Binary) -> int:
        """Get the bit width of operands for comparison."""
        left_type = operation.variable_left.type
        if isinstance(left_type, ElementaryType):
            return get_bit_width(left_type)
        right_type = operation.variable_right.type
        if isinstance(right_type, ElementaryType):
            return get_bit_width(right_type)
        return 256

    def _operands_are_signed(self, operation: Binary) -> bool:
        """Check if operands are signed integers."""
        left_type = operation.variable_left.type
        if isinstance(left_type, ElementaryType) and is_signed_type(left_type):
            return True
        right_type = operation.variable_right.type
        if isinstance(right_type, ElementaryType) and is_signed_type(right_type):
            return True
        return False

    def _resolve_operand(
        self,
        operand,
        domain: "IntervalDomain",
        target_width: int,
    ) -> SMTTerm | None:
        """Resolve an operand to an SMT term."""
        if isinstance(operand, Constant):
            return self._constant_to_term(operand, target_width)

        operand_name = get_variable_name(operand)
        tracked = domain.state.get_variable(operand_name)

        if tracked is not None:
            return tracked.term

        tracked = try_create_parameter_variable(self.solver, operand, operand_name, domain)
        if tracked is not None:
            return tracked.term

        return None

    def _constant_to_term(self, constant: Constant, bit_width: int) -> SMTTerm | None:
        """Convert a constant to an SMT term."""
        value = constant.value
        if isinstance(value, bool):
            return constant_to_term(self.solver, 1 if value else 0, bit_width)
        if isinstance(value, int):
            return constant_to_term(self.solver, value, bit_width)
        return None

    def _compute_condition(
        self,
        operation_type: BinaryType,
        left: SMTTerm,
        right: SMTTerm,
        is_signed: bool,
    ) -> SMTTerm | None:
        """Compute the boolean condition for the comparison."""
        dispatch: dict[BinaryType, Callable[[], SMTTerm]] = {
            BinaryType.EQUAL: lambda: left == right,
            BinaryType.NOT_EQUAL: lambda: self.solver.Not(left == right),
            BinaryType.LESS: lambda: self._less_than(left, right, is_signed),
            BinaryType.GREATER: lambda: self._greater_than(left, right, is_signed),
            BinaryType.LESS_EQUAL: lambda: self._less_equal(left, right, is_signed),
            BinaryType.GREATER_EQUAL: lambda: self._greater_equal(left, right, is_signed),
            BinaryType.ANDAND: lambda: self._logical_and(left, right),
            BinaryType.OROR: lambda: self._logical_or(left, right),
        }

        handler = dispatch.get(operation_type)
        if handler is None:
            return None
        return handler()

    def _less_than(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Compute left < right."""
        if is_signed:
            return self.solver.bv_slt(left, right)
        return self.solver.bv_ult(left, right)

    def _greater_than(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Compute left > right."""
        if is_signed:
            return self.solver.bv_sgt(left, right)
        return self.solver.bv_ugt(left, right)

    def _less_equal(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Compute left <= right."""
        if is_signed:
            return self.solver.bv_sle(left, right)
        return self.solver.bv_ule(left, right)

    def _greater_equal(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Compute left >= right."""
        if is_signed:
            return self.solver.bv_sge(left, right)
        return self.solver.bv_uge(left, right)

    def _logical_and(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Compute left && right (both nonzero)."""
        return self.solver.And(self._is_nonzero(left), self._is_nonzero(right))

    def _logical_or(self, left: SMTTerm, right: SMTTerm) -> SMTTerm:
        """Compute left || right (either nonzero)."""
        return self.solver.Or(self._is_nonzero(left), self._is_nonzero(right))

    def _is_nonzero(self, term: SMTTerm) -> SMTTerm:
        """Check if term is nonzero."""
        width = self.solver.bv_size(term)
        zero = self.solver.create_constant(0, Sort(SortKind.BITVEC, [width]))
        return self.solver.Not(term == zero)

    def _bool_to_bitvector(self, condition: SMTTerm) -> SMTTerm:
        """Convert boolean condition to 1-bit bitvector."""
        one = self.solver.create_constant(1, Sort(SortKind.BITVEC, [1]))
        zero = self.solver.create_constant(0, Sort(SortKind.BITVEC, [1]))
        return self.solver.make_ite(condition, one, zero)
