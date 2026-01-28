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
        # For default wide types (uint256/int256), try to infer a narrower type from the expression
        # This handles cases like -10 (converted to 0 - 10) where the temp gets uint256 but should be int8
        is_default_wide_type = result_type is not None and result_type.type in ("uint256", "int256")
        if (result_type is None or is_default_wide_type) and expression is not None:
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

            if result_type is None or is_default_wide_type:
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
        is_shift = operation.type in (BinaryType.LEFT_SHIFT, BinaryType.RIGHT_SHIFT)

        is_result_signed = IntervalSMTUtils.is_signed_type(result_type)
        result_width = IntervalSMTUtils.type_bit_width(result_type)

        # For shift operations, we need to perform the operation at the left operand's width
        # to preserve the bits being shifted, then truncate the result to the target width.
        # Otherwise the upper bits would be lost before the shift.
        if is_shift:
            left_operand_width = self.solver.bv_size(left_term)
            operation_width = max(left_operand_width, result_width)
        else:
            operation_width = result_width

        # Extend operands to operation width for the computation
        left_term_extended = IntervalSMTUtils.extend_to_width(
            self.solver, left_term, operation_width, is_result_signed
        )
        right_term_extended = IntervalSMTUtils.extend_to_width(
            self.solver, right_term, operation_width, is_result_signed
        )

        # Check for division/modulo by zero (always reverts in Solidity)
        if operation.type in (BinaryType.DIVISION, BinaryType.MODULO):
            if self._check_division_by_zero(right_term_extended, domain, is_checked):
                return  # Path is unreachable due to division by zero

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

        # If operation was performed at a wider width, truncate result to target width
        if is_shift and operation_width > result_width:
            raw_expr = IntervalSMTUtils.truncate_to_width(self.solver, raw_expr, result_width)

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

        # Store binary operation for later retrieval (needed for bytes memory constant tracking)
        if result_name is not None:
            domain.state.set_binary_operation(result_name, operation)

        # Track pointer arithmetic for memory safety analysis
        self._track_pointer_arithmetic(
            result_name, left_name, right_name, operation, domain
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
            # For power, we need the exponent value to compute overflow
            # The exponent should be a constant for us to handle it
            exponent_value = self._resolve_constant_value(operation.variable_right)
            if exponent_value is None or exponent_value <= 0:
                return self._bool_false()

            # Compute power at extended width (double width to catch overflow)
            extended_width = result_width * 2
            if is_signed:
                base_ext = solver.bv_sign_ext(left_term, result_width)
            else:
                base_ext = solver.bv_zero_ext(left_term, result_width)

            # Compute power at extended width
            extended_sort = Sort(kind=SortKind.BITVEC, parameters=[extended_width])
            power_result = solver.create_constant(1, extended_sort)
            for _ in range(exponent_value):
                power_result = power_result * base_ext

            # Check if upper bits are non-zero (overflow occurred)
            lower = solver.bv_extract(power_result, result_width - 1, 0)
            if is_signed:
                extended_back = solver.bv_sign_ext(lower, result_width)
            else:
                extended_back = solver.bv_zero_ext(lower, result_width)
            return extended_back != power_result
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

    def _track_pointer_arithmetic(
        self,
        result_name: str,
        left_name: str,
        right_name: str,
        operation: Binary,
        domain: "IntervalDomain",
    ) -> None:
        """Track pointer arithmetic for memory safety analysis.

        This identifies when a result is computed by adding a base pointer
        to an offset, especially when the offset is attacker-controlled.
        """
        if self.analysis is None:
            return

        # Only track addition operations (pointer + offset)
        if operation.type != BinaryType.ADDITION:
            return

        safety_ctx = self.analysis.safety_context

        def matches_any(name: str, name_set: set) -> bool:
            """Check if a name matches any entry in the set (flexible matching).

            Handles variable name format differences:
            - Binary operations use short names like 'ptr_processData_asm_0'
            - Safety context uses full names like 
              'VulnerableExample.processData(bytes).ptr_processData_asm_0|ptr_processData_asm_0_1'
            """
            if name in name_set:
                return True

            # Extract the base name (strip SSA version suffix)
            name_base = name.split("|")[0] if "|" in name else name

            for entry in name_set:
                # Check exact match with entry
                if entry == name:
                    return True

                # Extract entry base name
                entry_base = entry.split("|")[0] if "|" in entry else entry

                # Check if the entry's base ends with the name (handles full qualified names)
                # e.g., 'VulnerableExample.processData(bytes).ptr_processData_asm_0' ends with 'ptr_processData_asm_0'
                if entry_base.endswith(f".{name_base}") or entry_base.endswith(f".{name}"):
                    return True

                # Check if the name's base ends with the entry (handles reverse)
                if name_base.endswith(f".{entry_base}") or name.endswith(f".{entry}"):
                    return True

                # Check if the last component matches
                entry_last = entry_base.split(".")[-1] if "." in entry_base else entry_base
                name_last = name_base.split(".")[-1] if "." in name_base else name_base
                if entry_last == name_last:
                    return True

            return False

        # Check if either operand is a free memory pointer or derived from one
        left_is_ptr = matches_any(left_name, safety_ctx.free_memory_pointers)
        right_is_ptr = matches_any(right_name, safety_ctx.free_memory_pointers)

        # Check if this is adding to an existing pointer arithmetic result
        left_is_derived = matches_any(left_name, set(safety_ctx.pointer_arithmetic.keys()))
        right_is_derived = matches_any(right_name, set(safety_ctx.pointer_arithmetic.keys()))

        # Check if operands are attacker-controlled
        left_is_calldata = matches_any(left_name, safety_ctx.calldata_variables)
        right_is_calldata = matches_any(right_name, safety_ctx.calldata_variables)

        if left_is_ptr or left_is_derived:
            # result = ptr + offset or result = derived_ptr + offset
            base_name = left_name
            if left_is_derived:
                # Get the original base
                prev_info = safety_ctx.pointer_arithmetic.get(left_name, {})
                base_name = prev_info.get("base", left_name)
                prev_offsets = list(prev_info.get("offsets", []))
            else:
                prev_offsets = []

            offsets = prev_offsets + [right_name]
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

        elif right_is_ptr or right_is_derived:
            # result = offset + ptr (less common but possible)
            base_name = right_name
            if right_is_derived:
                prev_info = safety_ctx.pointer_arithmetic.get(right_name, {})
                base_name = prev_info.get("base", right_name)
                prev_offsets = list(prev_info.get("offsets", []))
            else:
                prev_offsets = []

            offsets = prev_offsets + [left_name]
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
