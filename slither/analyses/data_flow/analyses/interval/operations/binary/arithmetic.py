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
        # Prefer the lvalue type to keep the width narrow (e.g., uint8 stays uint8)
        try:
            lvalue_type = operation.lvalue.type  # type: ignore[attr-defined]
        except AttributeError:
            lvalue_type = None
        if isinstance(lvalue_type, ElementaryType):
            result_type = lvalue_type

        expression = node.expression if isinstance(node.expression, AssignmentOperation) else None
        if result_type is None and expression is not None:
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
            node=node,
            operation=operation,
        )
        right_term, right_var = self._get_operand_term(
            domain,
            operation.variable_right,
            right_name,
            fallback_type=result_type,
            is_checked=is_checked,
            node=node,
            operation=operation,
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

        # Extend operands to result width for the operation
        # Operations are performed at the result type's bit width
        left_term_extended = IntervalSMTUtils.extend_to_width(
            self.solver, left_term, result_width, is_result_signed
        )
        right_term_extended = IntervalSMTUtils.extend_to_width(
            self.solver, right_term, result_width, is_result_signed
        )

        if is_power:
            raw_expr = self._compute_power_expression(
                operation,
                result_var,
                left_term_extended,
                right_term_extended,
            )
        else:
            raw_expr = self._compute_expression(operation, left_term_extended, right_term_extended)

        if raw_expr is None:
            return

        # Result is already at result_width, just assign directly
        # Constrain the bitvector result
        self.solver.assert_constraint(result_var.term == raw_expr)

        # Enforce type bounds to ensure result stays within valid range
        IntervalSMTUtils.enforce_type_bounds(self.solver, result_var)

        # Add overflow detection constraint for arithmetic operations
        self._add_overflow_constraint(
            result_var,
            left_term_extended,
            right_term_extended,
            operation,
            result_type,
            is_checked,
            domain,
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
        if op_type == BinaryType.AND:
            return left_term & right_term
        if op_type == BinaryType.OR:
            return left_term | right_term
        if op_type == BinaryType.CARET:
            return left_term ^ right_term

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
        left_term: SMTTerm,
        right_term: SMTTerm,
        operation: Binary,
        result_type: ElementaryType,
        is_checked: bool,
        domain: "IntervalDomain",
    ) -> None:
        from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
        from slither.analyses.data_flow.smt_solver.types import CheckSatResult

        solver = self.solver
        result_width = IntervalSMTUtils.type_bit_width(result_type)
        is_signed = IntervalSMTUtils.is_signed_type(result_type)
        overflow_cond = self._detect_width_overflow(
            left_term, right_term, operation, result_width, is_signed
        )

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
            # In checked mode, check if overflow is possible
            # If overflow MUST occur, mark path as unreachable
            solver.push()
            # Try to find a model where no overflow occurs
            no_overflow = solver.create_constant(False, Sort(kind=SortKind.BOOL))
            solver.assert_constraint(overflow_cond == no_overflow)
            sat_result = solver.check_sat()
            solver.pop()

            if sat_result == CheckSatResult.UNSAT:
                # No model exists where overflow doesn't occur
                # This means overflow ALWAYS happens for current constraints
                self.logger.debug("Overflow detected in checked mode - marking path as unreachable")
                domain.variant = DomainVariant.TOP
                return

            # Otherwise, assert no overflow (constraining to valid paths)
            result_var.assert_no_overflow(solver)

    def _get_operand_term(
        self,
        domain: "IntervalDomain",
        operand: Union[Variable, SlithIRVariable, Constant],
        name: Optional[str],
        fallback_type: Optional[ElementaryType],
        is_checked: bool,
        node: "Node",
        operation: Binary,
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
        if tracked is None:
            self.logger.error_and_raise(
                "Variable '{var_name}' not found in domain for binary operation operand",
                ValueError,
                var_name=operand_name,
                embed_on_error=True,
                node=node,
                operation=operation,
                domain=domain,
            )

        return tracked.term, tracked

    def _detect_width_overflow(
        self,
        left_term: SMTTerm,
        right_term: SMTTerm,
        operation: Binary,
        result_width: int,
        is_signed: bool,
    ) -> SMTTerm:
        """Detect overflow by performing operation at extended width and comparing."""
        solver = self.solver
        op_type = operation.type

        # Extend operands by 1 bit to detect overflow
        if is_signed:
            left_ext = solver.bv_sign_ext(left_term, 1)
            right_ext = solver.bv_sign_ext(right_term, 1)
        else:
            left_ext = solver.bv_zero_ext(left_term, 1)
            right_ext = solver.bv_zero_ext(right_term, 1)

        # Perform operation at extended width
        if op_type == BinaryType.ADDITION:
            result_ext = left_ext + right_ext
        elif op_type == BinaryType.SUBTRACTION:
            result_ext = left_ext - right_ext
        elif op_type == BinaryType.MULTIPLICATION:
            # For multiplication, extend by full width to catch all overflow cases
            if is_signed:
                left_mul_ext = solver.bv_sign_ext(left_term, result_width)
                right_mul_ext = solver.bv_sign_ext(right_term, result_width)
            else:
                left_mul_ext = solver.bv_zero_ext(left_term, result_width)
                right_mul_ext = solver.bv_zero_ext(right_term, result_width)
            result_ext = left_mul_ext * right_mul_ext
            # Check if upper bits are non-zero (for unsigned) or don't match sign extension (for signed)
            lower = solver.bv_extract(result_ext, result_width - 1, 0)
            if is_signed:
                extended_back = solver.bv_sign_ext(lower, result_width)
            else:
                extended_back = solver.bv_zero_ext(lower, result_width)
            return extended_back != result_ext
        elif op_type == BinaryType.POWER:
            # Power overflow is complex; for now return false (handled separately)
            return self._bool_false()
        elif op_type in [BinaryType.AND, BinaryType.OR, BinaryType.CARET]:
            # Bitwise operations don't overflow
            return self._bool_false()
        else:
            # Division, modulo, shifts don't overflow in the traditional sense
            return self._bool_false()

        # For add/sub: check if truncated result differs from extended result
        lower = solver.bv_extract(result_ext, result_width - 1, 0)
        if is_signed:
            extended_back = solver.bv_sign_ext(lower, 1)
        else:
            extended_back = solver.bv_zero_ext(lower, 1)
        return extended_back != result_ext

    def _bool_false(self) -> SMTTerm:
        if not hasattr(self, "_bool_false_term"):
            self._bool_false_term = self.solver.create_constant(False, Sort(kind=SortKind.BOOL))
        return self._bool_false_term
