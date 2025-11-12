# Add overflow detection constraint for arithmetic operations
"""Arithmetic binary operation handler."""

from typing import Optional, TYPE_CHECKING

from slither.analyses.data_flow.analyses.interval.core.tracked_variable import TrackedSMTVariable
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import Sort, SortKind
from slither.slithir.operations.binary import Binary, BinaryType


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


class ArithmeticBinaryHandler(BaseOperationHandler):
    """Arithmetic handler for binary operations."""

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

        left_var = IntervalSMTUtils.get_tracked_variable(domain, left_name)
        right_var = IntervalSMTUtils.get_tracked_variable(domain, right_name)

        if left_var is None or right_var is None:
            self.logger.error(
                "Skipping arithmetic binary operation; operands missing in SMT state."
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

        expr = self._compute_expression(operation, left_var.term, right_var.term)
        if expr is None:
            return

        self.solver.assert_constraint(result_var.term == expr)

        # Add overflow detection constraint for arithmetic operations
        self._add_overflow_constraint(operation, left_var, right_var, result_var)

    def _compute_expression(self, operation: Binary, left_term, right_term):
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

    def _add_overflow_constraint(
        self,
        operation: Binary,
        left_var: TrackedSMTVariable,
        right_var: TrackedSMTVariable,
        result_var: TrackedSMTVariable,
    ) -> None:
        """Add overflow detection constraints for arithmetic operations."""
        solver = self.solver

        if not solver.is_bitvector(result_var.term):
            result_var.assert_no_overflow(solver)
            return

        if not (solver.is_bitvector(left_var.term) and solver.is_bitvector(right_var.term)):
            result_var.assert_no_overflow(solver)
            return

        width = result_var.sort.parameters[0]
        modulus = 1 << width
        modulus_term = solver.create_constant(modulus, Sort(kind=SortKind.INT))
        zero_term = solver.create_constant(0, Sort(kind=SortKind.INT))
        op_type = operation.type

        left_int = solver.bitvector_to_int(left_var.term)
        right_int = solver.bitvector_to_int(right_var.term)

        if op_type == BinaryType.ADDITION:
            actual_sum = left_int + right_int
            overflow_cond = actual_sum >= modulus_term
            overflow_amount = actual_sum - modulus_term
        elif op_type == BinaryType.SUBTRACTION:
            overflow_cond = left_int < right_int
            overflow_amount = right_int - left_int
        elif op_type == BinaryType.MULTIPLICATION:
            actual_prod = left_int * right_int
            overflow_cond = actual_prod >= modulus_term
            overflow_amount = actual_prod - modulus_term
        else:
            result_var.assert_no_overflow(solver)
            return

        amount_term = solver.make_ite(
            overflow_cond,
            overflow_amount,
            zero_term,
        )

        result_var.mark_overflow_condition(
            solver,
            overflow_cond,
            amount_term,
        )
