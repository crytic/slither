"""Arithmetic binary operation handler."""

from typing import Optional, TYPE_CHECKING, Union

from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.core.expressions.literal import Literal
from slither.core.expressions.assignment_operation import AssignmentOperation
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.variable import SlithIRVariable


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class ArithmeticBinaryHandler(BaseOperationHandler):
    """Arithmetic handler for binary operations."""

    _MAX_SUPPORTED_EXPONENT = 256

    def __init__(self, solver=None, analysis=None) -> None:
        super().__init__(solver, analysis)

    def handle(
        self,
        operation: Optional[Binary],
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        if operation is None or self.solver is None:
            return

        left_name = IntervalSMTUtils.resolve_variable_name(operation.variable_left)
        right_name = IntervalSMTUtils.resolve_variable_name(operation.variable_right)

        if left_name is None or right_name is None:
            self.logger.debug(
                "Skipping arithmetic binary operation due to unresolved operand names."
            )
            return

        result_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        result_type: Optional[ElementaryType] = None

        expression = node.expression if isinstance(node.expression, AssignmentOperation) else None
        if expression is not None:
            right_expr = expression.expression_right
            right_expr_type: Optional[ElementaryType] = None
            if right_expr is not None:
                try:
                    candidate = right_expr.type  # type: ignore[attr-defined]
                except AttributeError:
                    candidate = None
                if isinstance(candidate, ElementaryType):
                    right_expr_type = candidate
            if right_expr_type is not None:
                result_type = right_expr_type

            if result_type is None:
                return_type = expression.expression_return_type
                if isinstance(return_type, ElementaryType):
                    result_type = return_type

        if result_type is None:
            try:
                lvalue_type = operation.lvalue.type  # type: ignore[attr-defined]
            except AttributeError:
                lvalue_type = None
            if isinstance(lvalue_type, ElementaryType):
                result_type = lvalue_type

        if result_name is None or result_type is None:
            self.logger.debug(
                "Skipping arithmetic binary operation due to unsupported lvalue metadata."
            )
            return

        is_checked = node.scope.is_checked

        left_term, left_var = self._get_operand_term(
            domain,
            operation.variable_left,
            left_name,
            fallback_type=result_type,
            is_checked=is_checked,
        )
        right_term, right_var = self._get_operand_term(
            domain,
            operation.variable_right,
            right_name,
            fallback_type=result_type,
            is_checked=is_checked,
        )

        if left_term is None or right_term is None:
            self.logger.error(
                "Skipping arithmetic binary operation; operands missing in SMT state."
            )
            return

        result_var = IntervalSMTUtils.get_tracked_variable(domain, result_name)
        if result_var is None:
            result_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, result_name, result_type
            )
            if result_var is None:
                self.logger.error(
                    "Unable to create SMT variable for binary result '%s'.", result_name
                )
                return
            domain.state.set_range_variable(result_name, result_var)

        is_power = operation.type == BinaryType.POWER

        is_result_signed = IntervalSMTUtils.is_signed_type(result_type)
        result_width = IntervalSMTUtils.type_bit_width(result_type)

        if is_power:
            raw_expr = self._compute_power_expression(
                operation,
                result_var,
                left_term,
                right_term,
            )
        else:
            raw_expr = self._compute_expression(operation, left_term, right_term)

        if raw_expr is None:
            return

        wrapped_expr = self._apply_wrap(raw_expr, result_width, is_result_signed)

        # Constrain the bitvector result
        self.solver.assert_constraint(result_var.term == wrapped_expr)

        # Add overflow detection constraint for arithmetic operations
        self._add_overflow_constraint(
            result_var,
            raw_expr,
            result_type,
            is_checked,
        )

    def _compute_expression(
        self,
        operation: Binary,
        left_term: SMTTerm,
        right_term: SMTTerm,
    ) -> Optional[SMTTerm]:
        """Build the SMT expression for the arithmetic binary operation."""
        op_type = operation.type
        if op_type == BinaryType.ADDITION:
            return left_term + right_term
        if op_type == BinaryType.SUBTRACTION:
            return left_term - right_term
        if op_type == BinaryType.MULTIPLICATION:
            return left_term * right_term
        if op_type == BinaryType.DIVISION:
            return self.solver.bv_udiv(left_term, right_term)
        if op_type == BinaryType.MODULO:
            return self.solver.bv_urem(left_term, right_term)
        if op_type == BinaryType.LEFT_SHIFT:
            return left_term << right_term
        if op_type == BinaryType.RIGHT_SHIFT:
            return self.solver.bv_lshr(left_term, right_term)

        self.logger.debug("Unsupported arithmetic binary operation type: %s", op_type)
        return None

    def _compute_power_expression(
        self,
        operation: Binary,
        result_var: TrackedSMTVariable,
        left_term: SMTTerm,
        right_term: SMTTerm,
    ) -> Optional[SMTTerm]:
        """Build the modular exponentiation expression for bitvector semantics."""
        solver = self.solver
        if solver is None:
            return None

        if not solver.is_bitvector(result_var.term):
            self.logger.error(
                "Power operation requires bitvector result for '%s'.", result_var.name
            )
            return None

        exponent_value = self._resolve_constant_value(operation.variable_right)
        if exponent_value is None:
            self.logger.debug("Skipping power operation with non-constant exponent.")
            return None

        if exponent_value < 0:
            self.logger.debug("Skipping power operation with negative exponent.")
            return None

        if exponent_value > self._MAX_SUPPORTED_EXPONENT:
            self.logger.debug(
                "Skipping power operation; exponent %s exceeds supported maximum %s.",
                exponent_value,
                self._MAX_SUPPORTED_EXPONENT,
            )
            return None

        if not solver.is_bitvector(left_term):
            self.logger.debug("Skipping power operation due to non-bitvector base term.")
            return None

        result_sort = result_var.sort
        width_parameters = result_sort.parameters
        if not width_parameters:
            self.logger.debug("Skipping power operation due to missing bit-width information.")
            return None

        bitvec_result = solver.create_constant(1, result_sort)

        if exponent_value == 0:
            return bitvec_result

        width = width_parameters[0]

        for _ in range(exponent_value):
            bitvec_result = bitvec_result * left_term
        return bitvec_result

    @staticmethod
    def _resolve_constant_value(
        operand: Union[Variable, SlithIRVariable, Constant],
    ) -> Optional[int]:
        if isinstance(operand, Constant):
            value = getattr(operand, "value", None)
            return value if isinstance(value, int) else None

        expression = getattr(operand, "expression", None)
        if isinstance(expression, Literal):
            literal_value = expression.converted_value
            if isinstance(literal_value, int):
                return literal_value
            try:
                return int(literal_value)
            except (TypeError, ValueError):
                return None

        return None

    def _add_overflow_constraint(
        self,
        result_var: TrackedSMTVariable,
        raw_expr: SMTTerm,
        result_type: ElementaryType,
        is_checked: bool,
    ) -> None:
        solver = self.solver
        overflow_cond = self._detect_width_overflow(raw_expr, result_type)

        int_sort = result_var.overflow_amount.sort
        zero = solver.create_constant(0, int_sort)
        one = solver.create_constant(1, int_sort)
        overflow_amount = solver.make_ite(overflow_cond, one, zero)

        result_var.mark_overflow_condition(
            solver,
            overflow_cond,
            overflow_amount,
        )

        if is_checked:
            result_var.assert_no_overflow(solver)

    def _detect_add_overflow(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Detect addition overflow using bitvector operations."""
        solver = self.solver
        if solver is None:
            self.logger.error_and_raise("Solver is required for overflow detection", RuntimeError)

        # Extend by 1 bit and check if result fits
        if is_signed:
            left_ext = solver.bv_sign_ext(left, 1)
            right_ext = solver.bv_sign_ext(right, 1)
            result_ext = left_ext + right_ext
            # Sign-extend the truncated result back to compare with extended sum
            truncated = solver.bv_extract(result_ext, solver.bv_size(left) - 1, 0)
            truncated_ext = solver.bv_sign_ext(truncated, 1)
            return truncated_ext != result_ext
        else:
            left_ext = solver.bv_zero_ext(left, 1)
            right_ext = solver.bv_zero_ext(right, 1)
            result_ext = left_ext + right_ext
            # Check if carry bit is set
            carry_bit = solver.bv_extract(result_ext, solver.bv_size(left), solver.bv_size(left))
            from slither.analyses.data_flow.smt_solver.types import Sort, SortKind

            one_sort = Sort(kind=SortKind.BITVEC, parameters=[1])
            one = solver.create_constant(1, one_sort)
            return carry_bit == one

    def _detect_sub_overflow(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Detect subtraction overflow using bitvector operations."""
        solver = self.solver
        if solver is None:
            self.logger.error_and_raise("Solver is required for overflow detection", RuntimeError)

        if is_signed:
            left_ext = solver.bv_sign_ext(left, 1)
            right_ext = solver.bv_sign_ext(right, 1)
            result_ext = left_ext - right_ext
            truncated = solver.bv_extract(result_ext, solver.bv_size(left) - 1, 0)
            truncated_ext = solver.bv_sign_ext(truncated, 1)
            return truncated_ext != result_ext
        else:
            # For unsigned, underflow occurs if left < right
            return solver.bv_ult(left, right)

    def _detect_mul_overflow(
        self, left: SMTTerm, right: SMTTerm, is_signed: bool, width: int
    ) -> SMTTerm:
        """Detect multiplication overflow using bitvector operations."""
        solver = self.solver
        if solver is None:
            self.logger.error_and_raise("Solver is required for overflow detection", RuntimeError)

        # Extend to double width and check if upper bits are used
        if is_signed:
            left_ext = solver.bv_sign_ext(left, width)
            right_ext = solver.bv_sign_ext(right, width)
            result_ext = left_ext * right_ext
            # Check if result fits in original width
            result_truncated = solver.bv_extract(result_ext, width - 1, 0)
            # Sign extend the truncated result and compare
            result_truncated_ext = solver.bv_sign_ext(result_truncated, width)
            return result_truncated_ext != result_ext
        else:
            left_ext = solver.bv_zero_ext(left, width)
            right_ext = solver.bv_zero_ext(right, width)
            result_ext = left_ext * right_ext
            # Check if upper bits are non-zero
            upper_bits = solver.bv_extract(result_ext, width * 2 - 1, width)
            from slither.analyses.data_flow.smt_solver.types import Sort, SortKind

            zero_sort = Sort(kind=SortKind.BITVEC, parameters=[width])
            zero = solver.create_constant(0, zero_sort)
            return upper_bits != zero

    def _get_operand_term(
        self,
        domain: "IntervalDomain",
        operand: Union[Variable, SlithIRVariable, Constant],
        name: Optional[str],
        fallback_type: Optional[ElementaryType],
        is_checked: bool,
    ) -> tuple[Optional[SMTTerm], Optional[TrackedSMTVariable]]:
        if isinstance(operand, Constant):
            var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            if var_type is None:
                var_type = fallback_type
            term = IntervalSMTUtils.create_constant_term(self.solver, operand.value, var_type)
            return term, None

        operand_name = name or IntervalSMTUtils.resolve_variable_name(operand)
        if operand_name is None:
            return None, None

        var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
        if var_type is None:
            var_type = fallback_type

        tracked = IntervalSMTUtils.get_tracked_variable(domain, operand_name)
        if tracked is None and var_type is not None:
            tracked = IntervalSMTUtils.create_tracked_variable(self.solver, operand_name, var_type)
            if tracked is not None:
                domain.state.set_range_variable(operand_name, tracked)

        if tracked is None:
            return None, None

        return tracked.term, tracked

    def _apply_wrap(self, expr: SMTTerm, width: int, is_signed: bool) -> SMTTerm:
        if width >= 256:
            return expr
        lower = self.solver.bv_extract(expr, width - 1, 0)
        if is_signed:
            return self.solver.bv_sign_ext(lower, 256 - width)
        return self.solver.bv_zero_ext(lower, 256 - width)

    def _detect_width_overflow(self, expr: SMTTerm, solidity_type: ElementaryType) -> SMTTerm:
        width = IntervalSMTUtils.type_bit_width(solidity_type)
        if width >= 256:
            return self._bool_false()
        lower = self.solver.bv_extract(expr, width - 1, 0)
        if IntervalSMTUtils.is_signed_type(solidity_type):
            extended = self.solver.bv_sign_ext(lower, 256 - width)
        else:
            extended = self.solver.bv_zero_ext(lower, 256 - width)
        return extended != expr

    def _bool_false(self) -> SMTTerm:
        if not hasattr(self, "_bool_false_term"):
            self._bool_false_term = self.solver.create_constant(False, Sort(kind=SortKind.BOOL))
        return self._bool_false_term
