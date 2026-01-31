"""Arithmetic binary operation handler."""

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Union

from slither.analyses.data_flow.smt_solver.types import CheckSatResult, SMTTerm, Sort, SortKind
from slither.analyses.data_flow.analyses.interval.analysis.domain import DomainVariant
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
from slither.utils.integer_conversion import convert_string_to_int


if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
    from slither.core.cfg.node import Node


@dataclass
class OperandContext:
    """Context for binary operation operands."""

    left_term: SMTTerm
    right_term: SMTTerm
    left_name: str
    right_name: str


@dataclass
class ResultContext:
    """Context for binary operation result."""

    var: TrackedSMTVariable
    type: ElementaryType
    name: str


@dataclass
class BinaryOperationContext:
    """Context for binary operation handling."""

    domain: "IntervalDomain"
    operation: Binary
    node: "Node"
    is_checked: bool


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
        """Handle arithmetic binary operations."""
        if operation is None or self.solver is None:
            return

        # Resolve operand names
        left_name = IntervalSMTUtils.resolve_variable_name(operation.variable_left)
        right_name = IntervalSMTUtils.resolve_variable_name(operation.variable_right)
        if left_name is None or right_name is None:
            self.logger.debug("Skipping: unresolved operand names.")
            return

        # Infer result type
        result_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        result_type = self._infer_result_type(operation, node)
        if result_name is None or result_type is None:
            self.logger.debug("Skipping: unsupported lvalue metadata.")
            return

        # Get operand terms
        is_checked = node.scope.is_checked
        op_ctx = BinaryOperationContext(domain, operation, node, is_checked)
        left_term, right_term = self._get_operand_terms(
            left_name, right_name, result_type, op_ctx
        )
        if left_term is None or right_term is None:
            return

        # Setup result variable
        result_var = self._setup_result_variable(domain, result_name, result_type)
        if result_var is None:
            return

        # Fix signedness for negative literal constants first
        # This updates metadata to mark negative literals as signed
        self._fix_negative_literal_signedness(operation, result_var)

        # For constant-only operations, constrain to exact value and set bounds
        # This provides a fallback when SMT optimization times out
        const_result = self._try_evaluate_constant_operation(operation)
        if const_result is not None:
            bit_width = IntervalSMTUtils.type_bit_width(result_type)
            const_term = self.solver.create_constant(
                const_result,
                Sort(kind=SortKind.BITVEC, parameters=[bit_width])
            )
            self.solver.assert_constraint(result_var.term == const_term)

            # Set metadata bounds for fallback when optimization times out
            # Check if metadata was marked as signed by _fix_negative_literal_signedness
            is_signed = result_var.base.metadata.get("is_signed", False)
            if not is_signed:
                # Fall back to type-based signedness
                is_signed = IntervalSMTUtils.is_signed_type(result_type)

            if is_signed:
                # Interpret as signed value
                if const_result >= (1 << (bit_width - 1)):
                    signed_value = const_result - (1 << bit_width)
                else:
                    signed_value = const_result
                result_var.base.metadata["min_value"] = signed_value
                result_var.base.metadata["max_value"] = signed_value
            else:
                result_var.base.metadata["min_value"] = const_result
                result_var.base.metadata["max_value"] = const_result

        # Compute and apply the result
        operand_ctx = OperandContext(left_term, right_term, left_name, right_name)
        result_ctx = ResultContext(result_var, result_type, result_name)
        self._compute_and_apply_result(operand_ctx, result_ctx, op_ctx)

    def _try_evaluate_constant_operation(self, operation: Binary) -> Optional[int]:
        """Try to evaluate a constant-only operation to its concrete value.

        Returns the wrapped bitvector value if both operands are constants,
        None otherwise.
        """
        # Only handle constant-only operations
        if not isinstance(operation.variable_left, Constant):
            return None
        if not isinstance(operation.variable_right, Constant):
            return None

        left_val = operation.variable_left.value
        right_val = operation.variable_right.value

        # Check if both are integers
        if not isinstance(left_val, int) or not isinstance(right_val, int):
            return None

        # Get bit width from operation type
        try:
            lvalue_type = operation.lvalue.type  # type: ignore[attr-defined]
        except AttributeError:
            return None

        if not isinstance(lvalue_type, ElementaryType):
            return None

        bit_width = IntervalSMTUtils.type_bit_width(lvalue_type)
        modulus = 1 << bit_width

        # Evaluate the operation with wraparound semantics
        op_type = operation.type
        if op_type == BinaryType.ADDITION:
            result = (left_val + right_val) % modulus
        elif op_type == BinaryType.SUBTRACTION:
            result = (left_val - right_val) % modulus
        elif op_type == BinaryType.MULTIPLICATION:
            result = (left_val * right_val) % modulus
        else:
            # Other operations not yet supported for constant evaluation
            return None

        return result

    def _fix_negative_literal_signedness(
        self, operation: Binary, result_var: TrackedSMTVariable
    ) -> None:
        """Fix signedness metadata for constant subtractions that produce negative literals.

        When Solidity compiles "x - (-5)", it creates IR like:
            TMP = 0 - 5  (typed as uint256)
            result = x - TMP

        The intermediate TMP is typed as uint256 but semantically represents -5.
        We detect this pattern and mark the variable as signed for correct display.
        """
        if operation.type != BinaryType.SUBTRACTION:
            return

        # Only handle constant-only operations
        if not isinstance(operation.variable_left, Constant):
            return
        if not isinstance(operation.variable_right, Constant):
            return

        left_val = operation.variable_left.value
        right_val = operation.variable_right.value

        # Check if both are integers
        if not isinstance(left_val, int) or not isinstance(right_val, int):
            return

        # If left < right, the result wraps to a negative value
        # Mark as signed so it displays correctly
        if left_val < right_val:
            result_var.base.metadata["is_signed"] = True
            # Update bounds for signed interpretation
            bit_width = result_var.base.metadata.get("bit_width", 256)
            signed_min = -(1 << (bit_width - 1))
            signed_max = (1 << (bit_width - 1)) - 1
            result_var.base.metadata["min_value"] = signed_min
            result_var.base.metadata["max_value"] = signed_max

    def _infer_result_type(
        self, operation: Binary, node: "Node"
    ) -> Optional[ElementaryType]:
        """Infer the result type for the binary operation."""
        # Prefer the lvalue type
        try:
            lvalue_type = operation.lvalue.type  # type: ignore[attr-defined]
        except AttributeError:
            lvalue_type = None

        result_type = lvalue_type if isinstance(lvalue_type, ElementaryType) else None

        # For wide types, try to infer narrower type from expression
        expression = (
            node.expression if isinstance(node.expression, AssignmentOperation) else None
        )
        is_wide = result_type is not None and result_type.type in ("uint256", "int256")

        if (result_type is None or is_wide) and expression is not None:
            result_type = self._infer_type_from_expression(expression, result_type, is_wide)

        return result_type

    def _infer_type_from_expression(
        self,
        expression: AssignmentOperation,
        current_type: Optional[ElementaryType],
        is_wide: bool,
    ) -> Optional[ElementaryType]:
        """Try to infer a narrower type from the expression."""
        right_expr = expression.expression_right
        if right_expr is not None:
            try:
                candidate = right_expr.type  # type: ignore[attr-defined]
            except AttributeError:
                candidate = None
            if isinstance(candidate, ElementaryType):
                return candidate

        if current_type is None or is_wide:
            return_type = expression.expression_return_type
            if isinstance(return_type, ElementaryType):
                return return_type

        return current_type

    def _get_operand_terms(
        self,
        left_name: str,
        right_name: str,
        result_type: ElementaryType,
        ctx: BinaryOperationContext,
    ) -> tuple[Optional[SMTTerm], Optional[SMTTerm]]:
        """Get SMT terms for both operands."""
        left_term, _ = self._get_operand_term(
            ctx.operation.variable_left, left_name, result_type, ctx
        )
        right_term, _ = self._get_operand_term(
            ctx.operation.variable_right, right_name, result_type, ctx
        )
        if left_term is None or right_term is None:
            self.logger.error("Operands missing in SMT state.")
        return left_term, right_term

    def _setup_result_variable(
        self,
        domain: "IntervalDomain",
        result_name: str,
        result_type: ElementaryType,
    ) -> Optional[TrackedSMTVariable]:
        """Get or create the result variable."""
        result_var = IntervalSMTUtils.get_tracked_variable(domain, result_name)
        if result_var is None:
            result_var = IntervalSMTUtils.create_tracked_variable(
                self.solver, result_name, result_type
            )
            if result_var is None:
                self.logger.error("Unable to create SMT variable for '%s'.", result_name)
                return None
            domain.state.set_range_variable(result_name, result_var)
        return result_var

    def _compute_and_apply_result(
        self,
        operand_ctx: OperandContext,
        result_ctx: ResultContext,
        ctx: BinaryOperationContext,
    ) -> None:
        """Compute the operation result and apply constraints."""
        is_signed = IntervalSMTUtils.is_signed_type(result_ctx.type)
        result_width = IntervalSMTUtils.type_bit_width(result_ctx.type)
        operation_width = self._get_operation_width(
            ctx.operation, operand_ctx.left_term, result_width
        )

        # Extend operands
        left_ext = IntervalSMTUtils.extend_to_width(
            self.solver, operand_ctx.left_term, operation_width, is_signed
        )
        right_ext = IntervalSMTUtils.extend_to_width(
            self.solver, operand_ctx.right_term, operation_width, is_signed
        )

        # Check division by zero
        if ctx.operation.type in (BinaryType.DIVISION, BinaryType.MODULO):
            if self._check_division_by_zero(right_ext, ctx.domain, ctx.is_checked):
                return

        # Compute expression
        raw_expr = self._compute_operation(ctx.operation, result_ctx.var, left_ext, right_ext)
        if raw_expr is None:
            return

        # Truncate if needed
        if self._is_shift(ctx.operation) and operation_width > result_width:
            raw_expr = IntervalSMTUtils.truncate_to_width(self.solver, raw_expr, result_width)

        # Apply constraints
        self.solver.assert_constraint(result_ctx.var.term == raw_expr)
        IntervalSMTUtils.enforce_type_bounds(self.solver, result_ctx.var)

        # For self-multiplication of signed values, add non-negative constraint
        if (ctx.operation.type == BinaryType.MULTIPLICATION and
            is_signed and
            self._is_same_variable(ctx.operation.variable_left, ctx.operation.variable_right)):
            zero = self.solver.create_constant(
                0, Sort(kind=SortKind.BITVEC, parameters=[result_width])
            )
            self.solver.assert_constraint(self.solver.bv_sge(result_ctx.var.term, zero))
            # Set min_value for fallback when optimization times out
            result_ctx.var.base.metadata["min_value"] = 0

        self._add_overflow_constraint(result_ctx, left_ext, right_ext, ctx)

        ctx.domain.state.set_binary_operation(result_ctx.name, ctx.operation)
        self._track_pointer_arithmetic(
            result_ctx.name, operand_ctx.left_name, operand_ctx.right_name,
            ctx.operation, ctx.domain
        )

    def _get_operation_width(
        self, operation: Binary, left_term: SMTTerm, result_width: int
    ) -> int:
        """Determine the width to use for the operation."""
        if self._is_shift(operation):
            left_width = self.solver.bv_size(left_term)
            return max(left_width, result_width)
        return result_width

    def _is_shift(self, operation: Binary) -> bool:
        """Check if operation is a shift."""
        return operation.type in (BinaryType.LEFT_SHIFT, BinaryType.RIGHT_SHIFT)

    def _compute_operation(
        self,
        operation: Binary,
        result_var: TrackedSMTVariable,
        left_term: SMTTerm,
        right_term: SMTTerm,
    ) -> Optional[SMTTerm]:
        """Compute the SMT expression for the operation."""
        if operation.type == BinaryType.POWER:
            return self._compute_power_expression(operation, result_var, left_term, right_term)
        return self._compute_expression(operation, left_term, right_term)

    def _compute_expression(
        self,
        operation: Binary,
        left_term: SMTTerm,
        right_term: SMTTerm,
    ) -> Optional[SMTTerm]:
        """Build the SMT expression for the arithmetic binary operation."""
        op_type = operation.type

        # Simple operations using Python operators
        simple_ops = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.LEFT_SHIFT: lambda x, y: x << y,
            BinaryType.AND: lambda x, y: x & y,
            BinaryType.OR: lambda x, y: x | y,
            BinaryType.CARET: lambda x, y: x ^ y,
        }

        if op_type in simple_ops:
            return simple_ops[op_type](left_term, right_term)

        # Solver-specific operations
        if op_type == BinaryType.DIVISION:
            return self.solver.bv_udiv(left_term, right_term)
        if op_type == BinaryType.MODULO:
            return self.solver.bv_urem(left_term, right_term)
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
        result_ctx: ResultContext,
        left_term: SMTTerm,
        right_term: SMTTerm,
        ctx: BinaryOperationContext,
    ) -> None:
        # Skip overflow detection for constant-only expressions.
        # Expressions like "0 - 50" represent the negative literal -50, not a runtime underflow.
        # These are computed at compile time and don't cause actual overflows.
        if isinstance(ctx.operation.variable_left, Constant) and isinstance(
            ctx.operation.variable_right, Constant
        ):
            return

        solver = self.solver
        result_width = IntervalSMTUtils.type_bit_width(result_ctx.type)
        is_signed = IntervalSMTUtils.is_signed_type(result_ctx.type)
        overflow_cond = self._detect_width_overflow(
            left_term, right_term, ctx.operation, result_width, is_signed
        )

        int_sort = result_ctx.var.overflow_amount.sort
        zero = solver.create_constant(0, int_sort)
        one = solver.create_constant(1, int_sort)
        overflow_amount = solver.make_ite(overflow_cond, one, zero)

        result_ctx.var.mark_overflow_condition(
            solver,
            overflow_cond,
            overflow_amount,
        )

        if ctx.is_checked:
            self._handle_checked_overflow(solver, overflow_cond, result_ctx.var, ctx.domain)

    def _handle_checked_overflow(
        self,
        solver,
        overflow_cond: SMTTerm,
        result_var: TrackedSMTVariable,
        domain: "IntervalDomain",
    ) -> None:
        """Handle overflow in checked mode."""
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

        # Assert no overflow - this constrains input variables to valid ranges
        # e.g., for x * x, this adds: Not(x != 0 && x > MAX / x)
        # which constrains x to [0, sqrt(MAX)]
        solver.assert_constraint(solver.Not(overflow_cond))
        result_var.assert_no_overflow(solver)

    def _check_division_by_zero(
        self,
        divisor_term: SMTTerm,
        domain: "IntervalDomain",
        is_checked: bool,
    ) -> bool:
        """Check if division by zero occurs. Returns True if path is unreachable.

        In Solidity, division/modulo by zero always reverts (even in unchecked mode).
        """
        solver = self.solver

        # Get the bit width to create a zero constant of the same width
        divisor_width = solver.bv_size(divisor_term)
        zero = solver.create_constant(0, Sort(kind=SortKind.BITVEC, parameters=[divisor_width]))

        # Check if divisor can be non-zero
        solver.push()
        solver.assert_constraint(divisor_term != zero)
        can_be_nonzero = solver.check_sat()
        solver.pop()

        if can_be_nonzero == CheckSatResult.UNSAT:
            # Divisor is ALWAYS zero - division always reverts
            self.logger.debug("Division by zero detected - marking path as unreachable")
            domain.variant = DomainVariant.TOP
            return True

        # Divisor can be non-zero, so add constraint that it must be non-zero
        # (this constrains the analysis to valid execution paths)
        solver.assert_constraint(divisor_term != zero)
        return False

    def _get_operand_term(
        self,
        operand: Union[Variable, SlithIRVariable, Constant],
        name: Optional[str],
        fallback_type: Optional[ElementaryType],
        ctx: BinaryOperationContext,
    ) -> tuple[Optional[SMTTerm], Optional[TrackedSMTVariable]]:
        if isinstance(operand, Constant):
            var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            if var_type is None:
                var_type = fallback_type
            # Convert hex string constants (e.g., bytes32) to integers
            const_value = operand.value
            if isinstance(const_value, str):
                # Handle hex strings like "0x1234..." for bytes types
                try:
                    const_value = convert_string_to_int(const_value)
                except (ValueError, TypeError):
                    self.logger.debug(
                        "Unable to convert constant string '%s' to integer; skipping.",
                        const_value,
                    )
                    return None, None
            term = IntervalSMTUtils.create_constant_term(self.solver, const_value, var_type)
            return term, None

        operand_name = name or IntervalSMTUtils.resolve_variable_name(operand)
        if operand_name is None:
            return None, None

        var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
        if var_type is None:
            var_type = fallback_type

        tracked = IntervalSMTUtils.get_tracked_variable(ctx.domain, operand_name)
        if tracked is None:
            self.logger.error_and_raise(
                "Variable '{var_name}' not found in domain for binary operation operand",
                ValueError,
                var_name=operand_name,
                embed_on_error=True,
                node=ctx.node,
                operation=ctx.operation,
                domain=ctx.domain,
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
        op_type = operation.type

        if op_type == BinaryType.MULTIPLICATION:
            return self._detect_mul_overflow(
                left_term, right_term, result_width, is_signed, operation
            )
        if op_type == BinaryType.POWER:
            return self._detect_power_overflow(
                operation, left_term, result_width, is_signed
            )
        if op_type in (BinaryType.ADDITION, BinaryType.SUBTRACTION):
            return self._detect_add_sub_overflow(
                left_term, right_term, op_type, result_width, is_signed
            )
        # Bitwise, division, modulo, shifts don't overflow
        return self._bool_false()

    def _detect_mul_overflow(
        self,
        left_term: SMTTerm,
        right_term: SMTTerm,
        result_width: int,
        is_signed: bool,
        operation: Binary,
    ) -> SMTTerm:
        """Detect overflow in multiplication using division-based check.

        Uses the arithmetic property:
        - Unsigned: overflow iff b != 0 && a > MAX / b
        - Signed: split by operand signs, compare against MAX/b or MIN/b

        Special case for self-multiplication (a * a):
        - Use sqrt(MAX) as the bound directly to avoid non-linear constraints
        """
        solver = self.solver
        bv_sort = Sort(kind=SortKind.BITVEC, parameters=[result_width])
        zero = solver.create_constant(0, bv_sort)

        # Check for self-multiplication (a * a)
        is_self_mul = self._is_same_variable(operation.variable_left, operation.variable_right)

        if is_signed:
            return self._detect_signed_mul_overflow(
                solver, left_term, right_term, result_width, zero, is_self_mul
            )
        return self._detect_unsigned_mul_overflow(
            solver, left_term, right_term, result_width, zero, is_self_mul
        )

    def _is_same_variable(self, left, right) -> bool:
        """Check if two operands refer to the same variable."""
        if left is right:
            return True
        left_name = IntervalSMTUtils.resolve_variable_name(left)
        right_name = IntervalSMTUtils.resolve_variable_name(right)
        if left_name is None or right_name is None:
            return False
        # Compare base names (strip SSA suffixes like |x_1)
        left_base = left_name.split("|")[0] if "|" in left_name else left_name
        right_base = right_name.split("|")[0] if "|" in right_name else right_name
        return left_base == right_base

    def _detect_unsigned_mul_overflow(
        self,
        solver,
        left_term: SMTTerm,
        right_term: SMTTerm,
        result_width: int,
        zero: SMTTerm,
        is_self_mul: bool = False,
    ) -> SMTTerm:
        """Detect unsigned multiplication overflow: b != 0 && a > MAX / b.

        For self-multiplication (a * a), use a > sqrt(MAX) instead to avoid
        non-linear constraints that SMT solvers can't simplify for range queries.
        """
        bv_sort = Sort(kind=SortKind.BITVEC, parameters=[result_width])
        max_val = solver.create_constant((1 << result_width) - 1, bv_sort)

        if is_self_mul:
            # For a * a, overflow when a > sqrt(MAX)
            # sqrt(2^256 - 1) = 2^128 - 1 (approximately)
            sqrt_max = solver.create_constant((1 << (result_width // 2)) - 1, bv_sort)
            return solver.bv_ugt(left_term, sqrt_max)

        # b != 0 && a > MAX / b
        right_nonzero = right_term != zero
        max_div_right = solver.bv_udiv(max_val, right_term)
        left_too_large = solver.bv_ugt(left_term, max_div_right)

        return solver.And(right_nonzero, left_too_large)

    def _detect_signed_mul_overflow(
        self,
        solver,
        left_term: SMTTerm,
        right_term: SMTTerm,
        result_width: int,
        zero: SMTTerm,
        is_self_mul: bool = False,
    ) -> SMTTerm:
        """Detect signed multiplication overflow by operand sign cases."""
        bv_sort = Sort(kind=SortKind.BITVEC, parameters=[result_width])
        max_val = solver.create_constant((1 << (result_width - 1)) - 1, bv_sort)
        min_val = solver.create_constant(1 << (result_width - 1), bv_sort)

        if is_self_mul:
            # For a * a (signed), result is always non-negative
            # Overflow when |a| > sqrt(MAX)
            # sqrt(2^255 - 1) ≈ 2^127.5, use 2^127 - 1 conservatively
            sqrt_max = solver.create_constant((1 << ((result_width - 1) // 2)) - 1, bv_sort)
            neg_sqrt_max = solver.create_constant(
                (1 << result_width) - ((1 << ((result_width - 1) // 2)) - 1), bv_sort
            )
            # Overflow if a > sqrt_max OR a < -sqrt_max
            too_positive = solver.bv_sgt(left_term, sqrt_max)
            too_negative = solver.bv_slt(left_term, neg_sqrt_max)
            return solver.Or(too_positive, too_negative)

        a_pos = solver.bv_sgt(left_term, zero)
        a_neg = solver.bv_slt(left_term, zero)
        b_pos = solver.bv_sgt(right_term, zero)
        b_neg = solver.bv_slt(right_term, zero)

        # Case 1: a > 0, b > 0 -> overflow if a > MAX / b
        max_div_b = solver.bv_sdiv(max_val, right_term)
        case1 = solver.And(
            solver.And(a_pos, b_pos),
            solver.bv_sgt(left_term, max_div_b)
        )

        # Case 2: a > 0, b < 0 -> overflow if b < MIN / a
        min_div_a = solver.bv_sdiv(min_val, left_term)
        case2 = solver.And(
            solver.And(a_pos, b_neg),
            solver.bv_slt(right_term, min_div_a)
        )

        # Case 3: a < 0, b > 0 -> overflow if a < MIN / b
        min_div_b = solver.bv_sdiv(min_val, right_term)
        case3 = solver.And(
            solver.And(a_neg, b_pos),
            solver.bv_slt(left_term, min_div_b)
        )

        # Case 4: a < 0, b < 0 -> overflow if a < MAX / b (both negative, product positive)
        max_div_b_neg = solver.bv_sdiv(max_val, right_term)
        case4 = solver.And(
            solver.And(a_neg, b_neg),
            solver.bv_slt(left_term, max_div_b_neg)
        )

        return solver.Or(
            solver.Or(case1, case2),
            solver.Or(case3, case4)
        )

    def _detect_power_overflow(
        self,
        operation: Binary,
        left_term: SMTTerm,
        result_width: int,
        is_signed: bool,
    ) -> SMTTerm:
        """Detect overflow in power operations."""
        solver = self.solver
        exponent_value = self._resolve_constant_value(operation.variable_right)
        if exponent_value is None or exponent_value <= 0:
            return self._bool_false()

        extended_width = result_width * 2
        if is_signed:
            base_ext = solver.bv_sign_ext(left_term, result_width)
        else:
            base_ext = solver.bv_zero_ext(left_term, result_width)

        extended_sort = Sort(kind=SortKind.BITVEC, parameters=[extended_width])
        power_result = solver.create_constant(1, extended_sort)
        for _ in range(exponent_value):
            power_result = power_result * base_ext

        lower = solver.bv_extract(power_result, result_width - 1, 0)
        if is_signed:
            extended_back = solver.bv_sign_ext(lower, result_width)
        else:
            extended_back = solver.bv_zero_ext(lower, result_width)
        return extended_back != power_result

    def _detect_add_sub_overflow(
        self,
        left_term: SMTTerm,
        right_term: SMTTerm,
        op_type: BinaryType,
        result_width: int,
        is_signed: bool,
    ) -> SMTTerm:
        """Detect overflow using bit-level sign properties.

        For signed arithmetic, overflow depends only on sign bits:
        - Addition overflows when both operands have same sign but result differs
        - Subtraction overflows when operands differ in sign and result differs from left

        For unsigned arithmetic, overflow is carry/borrow:
        - Addition overflows if result < operand
        - Subtraction overflows if left < right
        """
        solver = self.solver

        if op_type == BinaryType.ADDITION:
            result = left_term + right_term
        else:
            result = left_term - right_term

        if is_signed:
            # Extract sign bits (MSB)
            msb = result_width - 1
            a_neg = solver.bv_extract(left_term, msb, msb)
            b_neg = solver.bv_extract(right_term, msb, msb)
            r_neg = solver.bv_extract(result, msb, msb)

            bv1_sort = Sort(kind=SortKind.BITVEC, parameters=[1])
            one = solver.create_constant(1, bv1_sort)
            zero = solver.create_constant(0, bv1_sort)

            if op_type == BinaryType.ADDITION:
                # Overflow when: same signs in, different sign out
                # (a >= 0 && b >= 0 && r < 0) || (a < 0 && b < 0 && r >= 0)
                both_pos = solver.And(a_neg == zero, b_neg == zero)
                both_neg = solver.And(a_neg == one, b_neg == one)
                pos_overflow = solver.And(both_pos, r_neg == one)
                neg_overflow = solver.And(both_neg, r_neg == zero)
            else:
                # Subtraction overflow when: different signs and result sign != left sign
                # (a >= 0 && b < 0 && r < 0) || (a < 0 && b >= 0 && r >= 0)
                a_pos_b_neg = solver.And(a_neg == zero, b_neg == one)
                a_neg_b_pos = solver.And(a_neg == one, b_neg == zero)
                pos_overflow = solver.And(a_pos_b_neg, r_neg == one)
                neg_overflow = solver.And(a_neg_b_pos, r_neg == zero)

            return solver.Or(pos_overflow, neg_overflow)
        else:
            # Unsigned overflow
            if op_type == BinaryType.ADDITION:
                # Overflow if result < left (wrapped around)
                return solver.bv_ult(result, left_term)
            else:
                # Underflow if left < right
                return solver.bv_ult(left_term, right_term)

    def _bool_false(self) -> SMTTerm:
        if not hasattr(self, "_bool_false_term"):
            self._bool_false_term = self.solver.create_constant(False, Sort(kind=SortKind.BOOL))
        return self._bool_false_term

    def _track_pointer_arithmetic(
        self,
        result_name: str,
        left_name: str,
        right_name: str,
        operation: Binary,
        domain: "IntervalDomain",
    ) -> None:
        """Track pointer arithmetic for memory safety analysis."""
        if self.analysis is None or operation.type != BinaryType.ADDITION:
            return

        safety_ctx = self.analysis.safety_context

        # Check operand classifications
        left_is_ptr = self._matches_name_set(left_name, safety_ctx.free_memory_pointers)
        right_is_ptr = self._matches_name_set(right_name, safety_ctx.free_memory_pointers)
        left_is_derived = self._matches_name_set(
            left_name, set(safety_ctx.pointer_arithmetic.keys())
        )
        right_is_derived = self._matches_name_set(
            right_name, set(safety_ctx.pointer_arithmetic.keys())
        )

        if left_is_ptr or left_is_derived:
            self._record_pointer_arithmetic(
                safety_ctx, result_name, left_name, right_name, left_is_derived
            )
        elif right_is_ptr or right_is_derived:
            self._record_pointer_arithmetic(
                safety_ctx, result_name, right_name, left_name, right_is_derived
            )

    def _matches_name_set(self, name: str, name_set: set) -> bool:
        """Check if a name matches any entry in the set (flexible matching)."""
        if name in name_set:
            return True

        name_base = name.split("|")[0] if "|" in name else name

        for entry in name_set:
            if entry == name:
                return True

            entry_base = entry.split("|")[0] if "|" in entry else entry

            # Check suffix matches for fully qualified names
            if entry_base.endswith(f".{name_base}") or entry_base.endswith(f".{name}"):
                return True
            if name_base.endswith(f".{entry_base}") or name.endswith(f".{entry}"):
                return True

            # Check if the last component matches
            entry_last = entry_base.split(".")[-1] if "." in entry_base else entry_base
            name_last = name_base.split(".")[-1] if "." in name_base else name_base
            if entry_last == name_last:
                return True

        return False

    def _record_pointer_arithmetic(
        self,
        safety_ctx,
        result_name: str,
        ptr_name: str,
        offset_name: str,
        is_derived: bool,
    ) -> None:
        """Record pointer arithmetic in the safety context."""
        if is_derived:
            prev_info = safety_ctx.pointer_arithmetic.get(ptr_name, {})
            base_name = prev_info.get("base", ptr_name)
            prev_offsets = list(prev_info.get("offsets", []))
        else:
            base_name = ptr_name
            prev_offsets = []

        offsets = prev_offsets + [offset_name]
        safety_ctx.pointer_arithmetic[result_name] = {
            "base": base_name,
            "offsets": offsets,
        }
        self.logger.debug(
            "Tracking pointer arithmetic: {result} = {base} + {offsets}",
            result=result_name,
            base=base_name,
            offsets=offsets,
        )
