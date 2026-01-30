"""Arithmetic binary operation handler."""

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
        left_term, right_term = self._get_operand_terms(
            domain, operation, left_name, right_name, result_type, is_checked, node
        )
        if left_term is None or right_term is None:
            return

        # Setup result variable
        result_var = self._setup_result_variable(domain, result_name, result_type)
        if result_var is None:
            return

        # Compute and apply the result
        self._compute_and_apply_result(
            operation, domain, node, result_var, result_type,
            left_term, right_term, left_name, right_name, result_name, is_checked,
        )

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
        domain: "IntervalDomain",
        operation: Binary,
        left_name: str,
        right_name: str,
        result_type: ElementaryType,
        is_checked: bool,
        node: "Node",
    ) -> tuple[Optional[SMTTerm], Optional[SMTTerm]]:
        """Get SMT terms for both operands."""
        left_term, _ = self._get_operand_term(
            domain, operation.variable_left, left_name,
            fallback_type=result_type, is_checked=is_checked, node=node, operation=operation
        )
        right_term, _ = self._get_operand_term(
            domain, operation.variable_right, right_name,
            fallback_type=result_type, is_checked=is_checked, node=node, operation=operation
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
        operation: Binary,
        domain: "IntervalDomain",
        _node: "Node",  # Unused but kept for API consistency
        result_var: TrackedSMTVariable,
        result_type: ElementaryType,
        left_term: SMTTerm,
        right_term: SMTTerm,
        left_name: str,
        right_name: str,
        result_name: str,
        is_checked: bool,
    ) -> None:
        """Compute the operation result and apply constraints."""
        is_signed = IntervalSMTUtils.is_signed_type(result_type)
        result_width = IntervalSMTUtils.type_bit_width(result_type)
        operation_width = self._get_operation_width(operation, left_term, result_width)

        # Extend operands
        left_ext = IntervalSMTUtils.extend_to_width(
            self.solver, left_term, operation_width, is_signed
        )
        right_ext = IntervalSMTUtils.extend_to_width(
            self.solver, right_term, operation_width, is_signed
        )

        # Check division by zero
        if operation.type in (BinaryType.DIVISION, BinaryType.MODULO):
            if self._check_division_by_zero(right_ext, domain, is_checked):
                return

        # Compute expression
        raw_expr = self._compute_operation(operation, result_var, left_ext, right_ext)
        if raw_expr is None:
            return

        # Truncate if needed
        if self._is_shift(operation) and operation_width > result_width:
            raw_expr = IntervalSMTUtils.truncate_to_width(self.solver, raw_expr, result_width)

        # Apply constraints
        self.solver.assert_constraint(result_var.term == raw_expr)
        IntervalSMTUtils.enforce_type_bounds(self.solver, result_var)

        self._add_overflow_constraint(
            result_var, left_ext, right_ext, operation, result_type, is_checked, domain
        )

        domain.state.set_binary_operation(result_name, operation)
        self._track_pointer_arithmetic(result_name, left_name, right_name, operation, domain)

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
        # Skip overflow detection for constant-only expressions.
        # Expressions like "0 - 50" represent the negative literal -50, not a runtime underflow.
        # These are computed at compile time and don't cause actual overflows.
        if isinstance(operation.variable_left, Constant) and isinstance(
            operation.variable_right, Constant
        ):
            return

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
        op_type = operation.type

        if op_type == BinaryType.MULTIPLICATION:
            return self._detect_mul_overflow(left_term, right_term, result_width, is_signed)
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
    ) -> SMTTerm:
        """Detect overflow in multiplication operations."""
        solver = self.solver
        if is_signed:
            left_ext = solver.bv_sign_ext(left_term, result_width)
            right_ext = solver.bv_sign_ext(right_term, result_width)
        else:
            left_ext = solver.bv_zero_ext(left_term, result_width)
            right_ext = solver.bv_zero_ext(right_term, result_width)

        result_ext = left_ext * right_ext
        lower = solver.bv_extract(result_ext, result_width - 1, 0)
        if is_signed:
            extended_back = solver.bv_sign_ext(lower, result_width)
        else:
            extended_back = solver.bv_zero_ext(lower, result_width)
        return extended_back != result_ext

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
        """Detect overflow in addition/subtraction operations."""
        solver = self.solver
        if is_signed:
            left_ext = solver.bv_sign_ext(left_term, 1)
            right_ext = solver.bv_sign_ext(right_term, 1)
        else:
            left_ext = solver.bv_zero_ext(left_term, 1)
            right_ext = solver.bv_zero_ext(right_term, 1)

        if op_type == BinaryType.ADDITION:
            result_ext = left_ext + right_ext
        else:
            result_ext = left_ext - right_ext

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
