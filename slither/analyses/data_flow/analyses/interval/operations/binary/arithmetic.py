"""Arithmetic binary operation handler."""

from typing import Optional, TYPE_CHECKING

from z3 import LShR, UDiv, URem

from slither.slithir.operations.binary import Binary, BinaryType

from ..base import BaseOperationHandler
from ...utils import IntervalSMTUtils

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

        left_smt = IntervalSMTUtils.get_smt_variable(domain, left_name)
        right_smt = IntervalSMTUtils.get_smt_variable(domain, right_name)

        if left_smt is None or right_smt is None:
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

        result_smt = IntervalSMTUtils.get_smt_variable(domain, result_name)
        if result_smt is None:
            result_smt = IntervalSMTUtils.create_smt_variable(self.solver, result_name, result_type)
            if result_smt is None:
                self.logger.error(
                    "Unable to create SMT variable for binary result '%s'.", result_name
                )
                return
            domain.state.set_range_variable(result_name, result_smt)

        expr = self._compute_expression(operation, left_smt.term, right_smt.term)
        if expr is None:
            return

        self.solver.assert_constraint(result_smt.term == expr)

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
            return UDiv(left_term, right_term)
        if op_type == BinaryType.MODULO:
            return URem(left_term, right_term)
        if op_type == BinaryType.LEFT_SHIFT:
            return left_term << right_term
        if op_type == BinaryType.RIGHT_SHIFT:
            return LShR(left_term, right_term)

        self.logger.debug("Unsupported arithmetic binary operation type: %s", op_type)
        return None
