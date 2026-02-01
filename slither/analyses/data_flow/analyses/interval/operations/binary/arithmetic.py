"""Arithmetic binary operation handler for interval analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.slithir.utils.utils import RVALUE

from slither.analyses.data_flow.logger import get_logger
from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.operations.base import (
    BaseOperationHandler,
)
from slither.analyses.data_flow.analyses.interval.operations.type_conversion import (
    match_width_to_int,
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

logger = get_logger()


@dataclass(frozen=True)
class ConstraintContext:
    """Bundles parameters for overflow constraint assertions."""

    left: SMTTerm
    right: SMTTerm
    result: SMTTerm
    is_signed: bool
    bit_width: int


ARITHMETIC_OPERATIONS = frozenset({
    BinaryType.ADDITION,
    BinaryType.SUBTRACTION,
    BinaryType.MULTIPLICATION,
    BinaryType.DIVISION,
    BinaryType.MODULO,
    BinaryType.POWER,
    BinaryType.LEFT_SHIFT,
    BinaryType.RIGHT_SHIFT,
    BinaryType.AND,
    BinaryType.OR,
    BinaryType.CARET,
})


class ArithmeticHandler(BaseOperationHandler):
    """Handler for arithmetic binary operations.

    Supports: +, -, *, /, %, **, <<, >>, &, |, ^
    """

    def handle(
        self,
        operation: Binary,
        domain: "IntervalDomain",
        node: "Node",
    ) -> None:
        """Process arithmetic binary operation."""
        result_type = self._get_result_type(operation)
        if result_type is None:
            return

        result_name = get_variable_name(operation.lvalue)
        bit_width = get_bit_width(result_type)
        signed, both_constants = self._determine_signedness(operation, result_type)

        result_var = self._create_result_variable(result_name, bit_width, signed)
        left_term = self._resolve_operand(operation.variable_left, domain, bit_width)
        right_term = self._resolve_operand(operation.variable_right, domain, bit_width)

        if left_term is None or right_term is None:
            domain.state.set_variable(result_name, result_var)
            return

        is_self_operation = self._is_same_operand(operation)
        result_term = self._compute_result(
            operation.type, left_term, right_term, result_type, is_self_operation, bit_width
        )
        if result_term is not None:
            self.solver.assert_constraint(result_var.term == result_term)

        if operation.type in (BinaryType.DIVISION, BinaryType.MODULO):
            self._assert_divisor_nonzero(right_term, bit_width)

        overflow_predicates = self._compute_overflow_predicates(
            operation.type, left_term, right_term, signed, both_constants
        )

        should_check = node.scope.is_checked and result_term is not None and not both_constants
        if should_check:
            context = ConstraintContext(left_term, right_term, result_term, signed, bit_width)
            self._assert_checked_constraints(operation.type, context)

        result_var = result_var.with_overflow_predicates(**overflow_predicates)
        domain.state.set_variable(result_name, result_var)

    def _determine_signedness(
        self,
        operation: Binary,
        result_type: ElementaryType,
    ) -> tuple[bool, bool]:
        """Determine signedness and whether both operands are constants."""
        signed = is_signed_type(result_type)
        both_constants = (
            isinstance(operation.variable_left, Constant)
            and isinstance(operation.variable_right, Constant)
        )
        if both_constants and operation.type == BinaryType.SUBTRACTION:
            signed = self._check_constant_subtraction_signed(operation, signed)
        return signed, both_constants

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

    def _compute_overflow_predicates(
        self,
        operation_type: BinaryType,
        left_term: SMTTerm,
        right_term: SMTTerm,
        is_signed: bool,
        both_constants: bool,
    ) -> dict[str, SMTTerm | None]:
        """Compute overflow predicates, returning empty dict for constants."""
        if both_constants:
            return {"no_overflow": None, "no_underflow": None}
        return self._get_overflow_predicates(operation_type, left_term, right_term, is_signed)

    def _check_constant_subtraction_signed(
        self,
        operation: Binary,
        default_signed: bool,
    ) -> bool:
        """Check if constant subtraction produces negative result, making it signed."""
        left_val = operation.variable_left.value
        right_val = operation.variable_right.value
        if not isinstance(left_val, int) or not isinstance(right_val, int):
            return default_signed
        # If left < right, result is negative, so treat as signed
        if left_val < right_val:
            return True
        return default_signed

    def _assert_checked_constraints(
        self,
        operation_type: BinaryType,
        context: ConstraintContext,
    ) -> None:
        """Assert direct overflow/underflow constraints for checked arithmetic.

        Creates direct constraints that narrow input ranges to valid values.
        """
        if operation_type == BinaryType.ADDITION:
            self._assert_add_constraints(context)
        elif operation_type == BinaryType.SUBTRACTION:
            self._assert_sub_constraints(context)
        elif operation_type == BinaryType.MULTIPLICATION:
            self._assert_mul_constraints(context)

    def _assert_add_constraints(self, context: ConstraintContext) -> None:
        """Assert addition overflow constraints.

        For unsigned: result >= left (no wraparound)
        For signed: result must maintain sign consistency
        """
        if context.is_signed:
            self._assert_signed_add_constraints(context)
        else:
            self.solver.assert_constraint(self.solver.bv_uge(context.result, context.left))

    def _assert_signed_add_constraints(self, context: ConstraintContext) -> None:
        """Assert signed addition overflow constraints."""
        # Signed overflow: pos + pos = neg, or neg + neg = pos
        # Constraint: (left > 0 ∧ right > 0) → result >= 0
        #             (left < 0 ∧ right < 0) → result <= 0
        zero = self.solver.create_constant(
            0, Sort(kind=SortKind.BITVEC, parameters=[context.bit_width])
        )
        left_positive = self.solver.bv_sgt(context.left, zero)
        right_positive = self.solver.bv_sgt(context.right, zero)
        left_negative = self.solver.bv_slt(context.left, zero)
        right_negative = self.solver.bv_slt(context.right, zero)

        # If both positive, result must be non-negative (allows edge case zero)
        no_overflow = self.solver.Or(
            self.solver.Not(self.solver.And(left_positive, right_positive)),
            self.solver.bv_sge(context.result, zero)
        )
        # If both negative, result must be non-positive (allows edge case zero)
        no_underflow = self.solver.Or(
            self.solver.Not(self.solver.And(left_negative, right_negative)),
            self.solver.bv_sle(context.result, zero)
        )
        self.solver.assert_constraint(no_overflow)
        self.solver.assert_constraint(no_underflow)

    def _assert_sub_constraints(self, context: ConstraintContext) -> None:
        """Assert subtraction underflow constraints.

        For unsigned: result <= left (no wraparound)
        For signed: result must maintain sign consistency
        """
        if context.is_signed:
            self._assert_signed_sub_constraints(context)
        else:
            self.solver.assert_constraint(self.solver.bv_ule(context.result, context.left))

    def _assert_signed_sub_constraints(self, context: ConstraintContext) -> None:
        """Assert signed subtraction overflow/underflow constraints."""
        # Signed: pos - neg can overflow, neg - pos can underflow
        zero = self.solver.create_constant(
            0, Sort(kind=SortKind.BITVEC, parameters=[context.bit_width])
        )
        left_positive = self.solver.bv_sge(context.left, zero)
        right_negative = self.solver.bv_slt(context.right, zero)
        result_positive = self.solver.bv_sge(context.result, zero)
        left_negative = self.solver.bv_slt(context.left, zero)
        right_positive = self.solver.bv_sgt(context.right, zero)
        result_negative = self.solver.bv_slt(context.result, zero)

        # pos - neg should stay non-negative
        no_overflow = self.solver.Or(
            self.solver.Not(self.solver.And(left_positive, right_negative)),
            result_positive
        )
        # neg - pos should stay negative
        no_underflow = self.solver.Or(
            self.solver.Not(self.solver.And(left_negative, right_positive)),
            result_negative
        )
        self.solver.assert_constraint(no_overflow)
        self.solver.assert_constraint(no_underflow)

    def _assert_mul_constraints(self, context: ConstraintContext) -> None:
        """Assert multiplication overflow constraints.

        Uses the Z3 built-in predicates which work correctly for multiplication.
        """
        no_overflow = self.solver.bv_mul_no_overflow(
            context.left, context.right, context.is_signed
        )
        self.solver.assert_constraint(no_overflow)
        if context.is_signed:
            no_underflow = self.solver.bv_mul_no_underflow(context.left, context.right)
            self.solver.assert_constraint(no_underflow)

    def _assert_divisor_nonzero(self, divisor: SMTTerm, bit_width: int) -> None:
        """Assert that divisor is not zero (division by zero reverts)."""
        zero = self.solver.create_constant(0, Sort(kind=SortKind.BITVEC, parameters=[bit_width]))
        self.solver.assert_constraint(self.solver.Not(divisor == zero))

    def _get_result_type(self, operation: Binary) -> ElementaryType | None:
        """Get the result type from the operation."""
        lvalue_type = operation.lvalue.type
        if isinstance(lvalue_type, ElementaryType):
            return lvalue_type
        return None

    def _resolve_operand(
        self,
        operand: RVALUE,
        domain: "IntervalDomain",
        target_width: int,
    ) -> SMTTerm | None:
        """Resolve an operand to an SMT term.

        Args:
            operand: The operand to resolve (constant or variable reference)
            domain: The interval domain containing tracked variables
            target_width: The bit width to use for the term

        Returns:
            SMT term for the operand, or None if unsupported

        Raises:
            ValueError: If operand is a variable not found in state and not a parameter
        """
        if isinstance(operand, Constant):
            return self._constant_to_term(operand, target_width)

        operand_name = get_variable_name(operand)
        tracked = domain.state.get_variable(operand_name)

        if tracked is not None:
            return match_width_to_int(self.solver, tracked.term, target_width)

        # Variable not in state - check if it's a function parameter
        tracked = try_create_parameter_variable(self.solver, operand, operand_name, domain)
        if tracked is not None:
            return match_width_to_int(self.solver, tracked.term, target_width)

        logger.error_and_raise(
            f"Variable '{operand_name}' not found in state", ValueError
        )
        return None

    def _constant_to_term(self, constant: Constant, bit_width: int) -> SMTTerm | None:
        """Convert a constant to an SMT term."""
        value = constant.value
        if not isinstance(value, (int, bool)):
            return None
        return constant_to_term(self.solver, value, bit_width)

    def _is_same_operand(self, operation: Binary) -> bool:
        """Check if both operands refer to the same variable."""
        left_name = get_variable_name(operation.variable_left)
        right_name = get_variable_name(operation.variable_right)
        return left_name == right_name

    def _compute_result(
        self,
        operation_type: BinaryType,
        left: SMTTerm,
        right: SMTTerm,
        result_type: ElementaryType,
        is_self_operation: bool = False,
        bit_width: int = 256,
    ) -> SMTTerm | None:
        """Compute the result term for the operation."""
        signed = is_signed_type(result_type)

        if is_self_operation:
            if operation_type == BinaryType.DIVISION:
                return self.solver.create_constant(1, Sort(SortKind.BITVEC, [bit_width]))
            if operation_type == BinaryType.MODULO:
                return self.solver.create_constant(0, Sort(SortKind.BITVEC, [bit_width]))
            if operation_type == BinaryType.SUBTRACTION:
                return self.solver.create_constant(0, Sort(SortKind.BITVEC, [bit_width]))

        dispatch: dict[BinaryType, Callable[[], SMTTerm]] = {
            BinaryType.ADDITION: lambda: self.solver.bv_add(left, right),
            BinaryType.SUBTRACTION: lambda: self.solver.bv_sub(left, right),
            BinaryType.MULTIPLICATION: lambda: self.solver.bv_mul(left, right),
            BinaryType.DIVISION: lambda: self._division(left, right, signed),
            BinaryType.MODULO: lambda: self._modulo(left, right, signed),
            BinaryType.LEFT_SHIFT: lambda: self.solver.bv_shl(left, right),
            BinaryType.RIGHT_SHIFT: lambda: self._right_shift(left, right, signed),
            BinaryType.AND: lambda: self.solver.bv_and(left, right),
            BinaryType.OR: lambda: self.solver.bv_or(left, right),
            BinaryType.CARET: lambda: self.solver.bv_xor(left, right),
            BinaryType.POWER: lambda: self._power(left, right),
        }

        handler = dispatch.get(operation_type)
        if handler is None:
            return None
        return handler()

    def _get_overflow_predicates(
        self,
        operation_type: BinaryType,
        left: SMTTerm,
        right: SMTTerm,
        is_signed: bool,
    ) -> dict[str, SMTTerm | None]:
        """Get overflow/underflow predicates for an operation.

        Returns dict with 'no_overflow' and 'no_underflow' keys.
        Values are predicates that are True when no overflow/underflow occurs.
        """
        no_overflow: SMTTerm | None = None
        no_underflow: SMTTerm | None = None

        if operation_type == BinaryType.ADDITION:
            no_overflow = self.solver.bv_add_no_overflow(left, right, is_signed)
            if is_signed:
                no_underflow = self.solver.bv_add_no_underflow(left, right)

        elif operation_type == BinaryType.SUBTRACTION:
            no_underflow = self.solver.bv_sub_no_underflow(left, right, is_signed)
            if is_signed:
                no_overflow = self.solver.bv_sub_no_overflow(left, right)

        elif operation_type == BinaryType.MULTIPLICATION:
            no_overflow = self.solver.bv_mul_no_overflow(left, right, is_signed)
            if is_signed:
                no_underflow = self.solver.bv_mul_no_underflow(left, right)

        elif operation_type == BinaryType.DIVISION and is_signed:
            no_overflow = self.solver.bv_sdiv_no_overflow(left, right)

        return {"no_overflow": no_overflow, "no_underflow": no_underflow}

    def _division(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Division with proper signed/unsigned semantics."""
        if is_signed:
            return self.solver.bv_sdiv(left, right)
        return self.solver.bv_udiv(left, right)

    def _modulo(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Modulo with proper signed/unsigned semantics."""
        if is_signed:
            return self.solver.bv_srem(left, right)
        return self.solver.bv_urem(left, right)

    def _right_shift(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> SMTTerm:
        """Right shift with proper signed/unsigned semantics."""
        if is_signed:
            return self.solver.bv_ashr(left, right)
        return self.solver.bv_lshr(left, right)

    def _power(self, base: SMTTerm, exponent: SMTTerm) -> SMTTerm:
        """Power operation (simplified - returns base * exponent for now).

        Full power implementation requires iterative multiplication.
        """
        # TODO: Implement proper power operation with iterative multiplication
        return self.solver.bv_mul(base, exponent)
