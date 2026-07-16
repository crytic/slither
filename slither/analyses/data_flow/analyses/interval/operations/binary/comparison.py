"""Comparison binary operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING
from collections.abc import Callable

from slither.analyses.data_flow.analyses.interval.core.state import (
    ComparisonInfo,
    IntervalRefinement,
)
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    NumericInterval,
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_utils import (
    get_bit_width,
    get_variable_name,
    is_signed_type,
)
from slither.analyses.data_flow.smt_solver.facts import StaticOperationId
from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )
    from slither.core.cfg.node import Node

COMPARISON_OPERATIONS = frozenset(
    {
        BinaryType.LESS,
        BinaryType.GREATER,
        BinaryType.LESS_EQUAL,
        BinaryType.GREATER_EQUAL,
        BinaryType.EQUAL,
        BinaryType.NOT_EQUAL,
        BinaryType.ANDAND,
        BinaryType.OROR,
    }
)


class ComparisonHandler(BaseOperationHandler):
    """Handler for comparison binary operations.

    Supports: <, >, <=, >=, ==, !=, &&, ||
    """

    def handle(
        self,
        operation: Binary,
        domain: IntervalDomain,
        node: Node,
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
            self._register_equation(
                operation,
                node,
                domain,
                result_var.term == result_term,
                "comparison_result",
            )
            # Store comparison info for condition narrowing
            operation_id = StaticOperationId.from_operation(operation, node)
            domain.state.set_comparison(
                result_name,
                ComparisonInfo(
                    condition,
                    operation_id,
                    self._build_interval_refinements(operation, is_signed, operand_width),
                ),
            )

        domain.state.set_variable(result_name, result_var)

    def _create_result_variable(self, name: str) -> TrackedSMTVariable:
        """Create a 1-bit result variable for boolean result."""
        sort = Sort(kind=SortKind.BITVEC, parameters=[1])
        return TrackedSMTVariable.create(self.solver, name, sort, is_signed=False, bit_width=1)

    def _build_interval_refinements(
        self,
        operation: Binary,
        is_signed: bool,
        bit_width: int,
    ) -> tuple[IntervalRefinement, ...]:
        """Derive non-relational interval restrictions for variable/constant comparisons."""
        left = operation.variable_left
        right = operation.variable_right
        operation_type = operation.type
        if isinstance(left, Constant) and not isinstance(right, Constant):
            constant = left
            variable = right
            operation_type = self._reverse_comparison(operation_type)
        elif isinstance(right, Constant) and not isinstance(left, Constant):
            constant = right
            variable = left
        else:
            return ()
        value = constant.value
        if not isinstance(value, (int, bool)):
            return ()
        type_interval = NumericInterval.type_range(bit_width, is_signed)
        intervals = self._comparison_intervals(operation_type, int(value), type_interval)
        if intervals is None:
            return ()
        true_interval, false_interval, true_reachable, false_reachable = intervals
        return (
            IntervalRefinement(
                get_variable_name(variable),
                true_interval,
                false_interval,
                true_reachable,
                false_reachable,
            ),
        )

    @staticmethod
    def _reverse_comparison(operation_type: BinaryType) -> BinaryType:
        return {
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
        }.get(operation_type, operation_type)

    def _comparison_intervals(
        self,
        operation_type: BinaryType,
        value: int,
        type_interval: NumericInterval,
    ) -> tuple[NumericInterval, NumericInterval, bool, bool] | None:
        if operation_type is BinaryType.LESS:
            return self._split_at(type_interval, value, include_left=False)
        if operation_type is BinaryType.LESS_EQUAL:
            return self._split_at(type_interval, value, include_left=True)
        if operation_type is BinaryType.GREATER:
            false_interval, true_interval, false_reachable, true_reachable = self._split_at(
                type_interval, value, include_left=True
            )
            return true_interval, false_interval, true_reachable, false_reachable
        if operation_type is BinaryType.GREATER_EQUAL:
            false_interval, true_interval, false_reachable, true_reachable = self._split_at(
                type_interval, value, include_left=False
            )
            return true_interval, false_interval, true_reachable, false_reachable
        if operation_type in (BinaryType.EQUAL, BinaryType.NOT_EQUAL):
            return self._equality_intervals(operation_type, value, type_interval)
        return None

    @staticmethod
    def _split_at(
        interval: NumericInterval,
        value: int,
        *,
        include_left: bool,
    ) -> tuple[NumericInterval, NumericInterval, bool, bool]:
        left_upper = value if include_left else value - 1
        right_lower = value + 1 if include_left else value
        left_reachable = interval.lower <= min(interval.upper, left_upper)
        right_reachable = max(interval.lower, right_lower) <= interval.upper
        left = (
            NumericInterval(interval.lower, min(interval.upper, left_upper))
            if left_reachable
            else interval
        )
        right = (
            NumericInterval(max(interval.lower, right_lower), interval.upper)
            if right_reachable
            else interval
        )
        return left, right, left_reachable, right_reachable

    @staticmethod
    def _equality_intervals(
        operation_type: BinaryType,
        value: int,
        interval: NumericInterval,
    ) -> tuple[NumericInterval, NumericInterval, bool, bool]:
        equal_reachable = interval.lower <= value <= interval.upper
        equal = NumericInterval(value, value) if equal_reachable else interval
        not_equal = interval
        if value == interval.lower and value < interval.upper:
            not_equal = NumericInterval(value + 1, interval.upper)
        elif value == interval.upper and value > interval.lower:
            not_equal = NumericInterval(interval.lower, value - 1)
        not_equal_reachable = not (interval.lower == interval.upper == value)
        result = (equal, not_equal, equal_reachable, not_equal_reachable)
        if operation_type is BinaryType.NOT_EQUAL:
            return result[1], result[0], result[3], result[2]
        return result

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
