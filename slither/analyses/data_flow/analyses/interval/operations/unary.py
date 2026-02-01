"""Unary operation handler for interval analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.unary import Unary, UnaryType
from slither.slithir.variables.constant import Constant
from slither.slithir.utils.utils import RVALUE

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

if TYPE_CHECKING:
    from slither.core.cfg.node import Node
    from slither.analyses.data_flow.analyses.interval.analysis.domain import (
        IntervalDomain,
    )


class UnaryHandler(BaseOperationHandler):
    """Handler for unary operations.

    Supports: ! (logical not), ~ (bitwise not)
    """

    def handle(
        self,
        operation: Unary,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process unary operation."""
        result_type = self._get_result_type(operation)
        if result_type is None:
            return

        result_name = get_variable_name(operation.lvalue)
        bit_width = get_bit_width(result_type)
        signed = is_signed_type(result_type)

        result_var = self._create_result_variable(result_name, bit_width, signed)
        operand_term = self._resolve_operand(operation.rvalue, domain, bit_width)

        if operand_term is None:
            domain.state.set_variable(result_name, result_var)
            return

        result_term = self._compute_result(operation.type, operand_term, bit_width)
        if result_term is not None:
            self.solver.assert_constraint(result_var.term == result_term)

        domain.state.set_variable(result_name, result_var)

    def _get_result_type(self, operation: Unary) -> ElementaryType | None:
        """Get the result type from the operation."""
        lvalue_type = operation.lvalue.type
        if isinstance(lvalue_type, ElementaryType):
            return lvalue_type
        return None

    def _create_result_variable(
        self,
        result_name: str,
        bit_width: int,
        is_signed: bool,
    ) -> TrackedSMTVariable:
        """Create a tracked variable for the operation result."""
        sort = Sort(kind=SortKind.BITVEC, parameters=[bit_width])
        return TrackedSMTVariable.create(
            self.solver, result_name, sort, is_signed=is_signed, bit_width=bit_width
        )

    def _resolve_operand(
        self,
        operand: RVALUE,
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

        # Variable not in state - check if it's a function parameter
        tracked = try_create_parameter_variable(self.solver, operand, operand_name, domain)
        if tracked is not None:
            return tracked.term

        return None

    def _constant_to_term(self, constant: Constant, bit_width: int) -> SMTTerm | None:
        """Convert a constant to an SMT term."""
        value = constant.value
        if isinstance(value, bool):
            int_value = 1 if value else 0
            return constant_to_term(self.solver, int_value, bit_width)
        if isinstance(value, int):
            return constant_to_term(self.solver, value, bit_width)
        return None

    def _compute_result(
        self,
        operation_type: UnaryType,
        operand: SMTTerm,
        bit_width: int,
    ) -> SMTTerm | None:
        """Compute the result term for the unary operation."""
        if operation_type == UnaryType.BANG:
            return self._logical_not(operand, bit_width)
        if operation_type == UnaryType.TILD:
            return self.solver.bv_not(operand)
        return None

    def _logical_not(self, operand: SMTTerm, bit_width: int) -> SMTTerm:
        """Compute logical not: !x.

        For booleans (1-bit): flips 0 to 1 and 1 to 0.
        For larger types: returns 1 if operand is 0, else 0.
        """
        zero = self.solver.create_constant(0, Sort(SortKind.BITVEC, [bit_width]))
        one = self.solver.create_constant(1, Sort(SortKind.BITVEC, [bit_width]))
        is_zero = operand == zero
        return self.solver.make_ite(is_zero, one, zero)
