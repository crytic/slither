"""Arithmetic binary operation handler."""

from typing import Optional, TYPE_CHECKING, Union

from slither.analyses.data_flow.smt_solver.types import SMTTerm
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.core.expressions.literal import Literal
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.variable import SlithIRVariable


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class ArithmeticBinaryHandler(BaseOperationHandler):
    """Arithmetic handler for binary operations."""

    _MAX_SUPPORTED_EXPONENT = 256

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
        result_type = IntervalSMTUtils.resolve_elementary_type(
            getattr(operation.lvalue, "type", None)
        )

        if result_name is None or result_type is None:
            self.logger.debug(
                "Skipping arithmetic binary operation due to unsupported lvalue metadata."
            )
            return

        is_checked = bool(getattr(getattr(node, "scope", None), "is_checked", False))

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

        if is_checked:
            self._ensure_within_bounds(result_var, result_type)

        is_power = operation.type == BinaryType.POWER

        if is_power:
            power_terms = self._compute_power_expression(
                operation, result_var, left_term, right_term
            )
            if power_terms is None:
                return
            expr, power_int = power_terms
        else:
            expr = self._compute_expression(operation, left_term, right_term)
            power_int = None

        if expr is None:
            return

        self.solver.assert_constraint(result_var.term == expr)

        # Add overflow detection constraint for arithmetic operations
        self._add_overflow_constraint(
            operation,
            left_term,
            right_term,
            result_var,
            is_checked,
            power_actual_int=power_int,
        )

    def _compute_expression(
        self, operation: Binary, left_term: SMTTerm, right_term: SMTTerm
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
    ) -> Optional[tuple[SMTTerm, SMTTerm]]:
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

        int_sort = result_var.overflow_amount.sort

        bitvec_result = solver.create_constant(1, result_sort)
        int_result = solver.create_constant(1, int_sort)

        if exponent_value == 0:
            return bitvec_result, int_result

        if isinstance(operation.variable_left, Constant):
            base_int = solver.create_constant(operation.variable_left.value, int_sort)
        else:
            base_int = solver.bitvector_to_int(left_term)

        for _ in range(exponent_value):
            bitvec_result = bitvec_result * left_term
            int_result = int_result * base_int

        return bitvec_result, int_result

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
        operation: Binary,
        left_term: SMTTerm,
        right_term: SMTTerm,
        result_var: TrackedSMTVariable,
        is_checked: bool,
        power_actual_int: Optional[SMTTerm] = None,
    ) -> None:
        """Add overflow detection constraints for arithmetic operations."""
        solver = self.solver

        if not (
            solver.is_bitvector(result_var.term)
            and solver.is_bitvector(left_term)
            and solver.is_bitvector(right_term)
        ):
            if is_checked:
                result_var.assert_no_overflow(solver)
            return

        width = result_var.sort.parameters[0]
        int_sort = result_var.overflow_amount.sort
        max_term = solver.create_constant((1 << width) - 1, int_sort)
        zero_term = solver.create_constant(0, int_sort)
        op_type = operation.type

        left_int = solver.bitvector_to_int(left_term)
        right_int = solver.bitvector_to_int(right_term)

        if op_type == BinaryType.ADDITION:
            actual_sum = left_int + right_int
            overflow_cond = actual_sum > max_term
            overflow_amount_expr = actual_sum - max_term
        elif op_type == BinaryType.SUBTRACTION:
            actual_diff = left_int - right_int
            overflow_cond = actual_diff < zero_term
            overflow_amount_expr = right_int - left_int
        elif op_type == BinaryType.MULTIPLICATION:
            actual_prod = left_int * right_int
            overflow_cond = actual_prod > max_term
            overflow_amount_expr = actual_prod - max_term
        elif op_type == BinaryType.POWER:
            if power_actual_int is None:
                if is_checked:
                    result_var.assert_no_overflow(solver)
                return

            overflow_cond = power_actual_int > max_term
            overflow_amount_expr = power_actual_int - max_term
        else:
            result_var.assert_no_overflow(solver)
            return

        amount_term = solver.make_ite(
            overflow_cond,
            overflow_amount_expr,
            zero_term,
        )

        result_var.mark_overflow_condition(
            solver,
            overflow_cond,
            amount_term,
        )

        if is_checked:
            result_var.assert_no_overflow(solver)

    def _get_operand_term(
        self,
        domain: "IntervalDomain",
        operand: Union[Variable, SlithIRVariable, Constant],
        name: Optional[str],
        fallback_type: Optional[ElementaryType],
        is_checked: bool,
    ) -> tuple[Optional[SMTTerm], Optional[TrackedSMTVariable]]:
        if isinstance(operand, Constant):
            # For constants, prioritize fallback_type to ensure bit width matches the result
            var_type = fallback_type
            if var_type is None:
                var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            if var_type is None:
                return None, None
            sort = IntervalSMTUtils.solidity_type_to_smt_sort(var_type)
            if sort is None:
                return None, None
            term = self.solver.create_constant(operand.value, sort)
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

        if is_checked and var_type is not None:
            self._ensure_within_bounds(tracked, var_type)

        return tracked.term, tracked

    def _ensure_within_bounds(
        self, tracked_var: TrackedSMTVariable, var_type: ElementaryType
    ) -> None:
        tracked_var.assert_no_overflow(self.solver)
        bounds = IntervalSMTUtils.type_bounds(var_type)
        if bounds is None:
            return
        min_val, max_val = bounds
        int_sort = tracked_var.overflow_amount.sort
        int_term = self.solver.bitvector_to_int(tracked_var.term)
        self.solver.assert_constraint(int_term >= self.solver.create_constant(min_val, int_sort))
        self.solver.assert_constraint(int_term <= self.solver.create_constant(max_val, int_sort))
