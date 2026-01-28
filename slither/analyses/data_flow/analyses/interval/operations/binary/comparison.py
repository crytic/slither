from typing import Optional

from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.tracked_variable import (
    TrackedSMTVariable,
)
from slither.analyses.data_flow.analyses.interval.operations.base import BaseOperationHandler
from slither.analyses.data_flow.analyses.interval.utils import IntervalSMTUtils
from slither.analyses.data_flow.smt_solver.types import SMTTerm, Sort, SortKind
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.temporary import TemporaryVariable


class ComparisonBinaryHandler(BaseOperationHandler):
    """Handler for comparison binary operations."""

    _LOGICAL_TYPES = {BinaryType.ANDAND, BinaryType.OROR}

    def handle(self, operation: Binary, domain: IntervalDomain, node: Node) -> None:
        if self.solver is None or operation is None:
            return

        result_var = self._ensure_result_variable(operation, domain)
        if result_var is None:
            return

        if operation.type in self._LOGICAL_TYPES:
            comparison_bitvec = self._build_logical(operation, domain, node)
        else:
            comparison_bitvec = self._build_comparison(operation, domain, node)

        if comparison_bitvec is None:
            return

        # Link result boolean to comparison result, no additional enforcement.
        self.solver.assert_constraint(result_var.term == comparison_bitvec)
        result_var.assert_no_overflow(self.solver)

        # Store the operation for all variables (temporaries and locals) that result from comparison/logical operations
        # This allows require() to retrieve the original constraint
        result_name = IntervalSMTUtils.resolve_variable_name(operation.lvalue)
        if result_name is not None:
            domain.state.set_binary_operation(result_name, operation)

    def _ensure_result_variable(
        self, operation: Binary, domain: IntervalDomain
    ) -> Optional[TrackedSMTVariable]:
        result = operation.lvalue
        result_name = IntervalSMTUtils.resolve_variable_name(result)
        if result_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, result_name)
        if tracked is not None:
            return tracked

        # Comparison operations always return bool.
        bool_type = ElementaryType("bool")
        tracked = IntervalSMTUtils.create_tracked_variable(self.solver, result_name, bool_type)
        if tracked is None:
            return None

        domain.state.set_range_variable(result_name, tracked)
        return tracked

    def _build_comparison(
        self, operation: Binary, domain: IntervalDomain, node: Node
    ) -> Optional[SMTTerm]:
        # Get bitvector terms directly (no BV2Int conversion)
        left_bv = self._resolve_operand_bitvec(operation.variable_left, domain, node, operation)
        right_bv = self._resolve_operand_bitvec(operation.variable_right, domain, node, operation)

        if left_bv is None or right_bv is None:
            return None

        # Determine signedness from operand types
        is_signed = self._is_comparison_signed(operation.variable_left, operation.variable_right, domain)

        # Normalize widths if they differ (extend smaller to match larger)
        left_bv, right_bv = self._normalize_widths(left_bv, right_bv, is_signed)

        comp_type = operation.type
        bool_expr: Optional[SMTTerm] = None

        # Use pure bitvector comparisons (no BV2Int conversion)
        if comp_type.value == ">=":
            bool_expr = self.solver.bv_sge(left_bv, right_bv) if is_signed else self.solver.bv_uge(left_bv, right_bv)
        elif comp_type.value == ">":
            bool_expr = self.solver.bv_sgt(left_bv, right_bv) if is_signed else self.solver.bv_ugt(left_bv, right_bv)
        elif comp_type.value == "<=":
            bool_expr = self.solver.bv_sle(left_bv, right_bv) if is_signed else self.solver.bv_ule(left_bv, right_bv)
        elif comp_type.value == "<":
            bool_expr = self.solver.bv_slt(left_bv, right_bv) if is_signed else self.solver.bv_ult(left_bv, right_bv)
        elif comp_type.value == "==":
            bool_expr = left_bv == right_bv
        elif comp_type.value == "!=":
            bool_expr = left_bv != right_bv

        if bool_expr is None:
            return None

        return self._bool_to_bitvec(bool_expr)

    def _normalize_widths(self, left: SMTTerm, right: SMTTerm, is_signed: bool) -> tuple[SMTTerm, SMTTerm]:
        """Normalize bitvector widths to match (extend smaller to match larger)."""
        left_width = self.solver.bv_size(left)
        right_width = self.solver.bv_size(right)

        if left_width == right_width:
            return left, right

        if left_width < right_width:
            # Extend left to match right
            extra_bits = right_width - left_width
            if is_signed:
                left = self.solver.bv_sign_ext(left, extra_bits)
            else:
                left = self.solver.bv_zero_ext(left, extra_bits)
        else:
            # Extend right to match left
            extra_bits = left_width - right_width
            if is_signed:
                right = self.solver.bv_sign_ext(right, extra_bits)
            else:
                right = self.solver.bv_zero_ext(right, extra_bits)

        return left, right

    def _is_comparison_signed(self, left_operand, right_operand, domain: IntervalDomain) -> bool:
        """Determine if comparison should use signed semantics based on operand types."""
        # Check left operand
        left_type = IntervalSMTUtils.resolve_elementary_type(getattr(left_operand, "type", None))
        if left_type is not None and IntervalSMTUtils.is_signed_type(left_type):
            return True

        # Check right operand
        right_type = IntervalSMTUtils.resolve_elementary_type(getattr(right_operand, "type", None))
        if right_type is not None and IntervalSMTUtils.is_signed_type(right_type):
            return True

        # Check tracked variable metadata
        left_name = IntervalSMTUtils.resolve_variable_name(left_operand)
        if left_name:
            left_tracked = IntervalSMTUtils.get_tracked_variable(domain, left_name)
            if left_tracked and left_tracked.base.metadata.get("is_signed"):
                return True

        right_name = IntervalSMTUtils.resolve_variable_name(right_operand)
        if right_name:
            right_tracked = IntervalSMTUtils.get_tracked_variable(domain, right_name)
            if right_tracked and right_tracked.base.metadata.get("is_signed"):
                return True

        return False

    def _build_logical(
        self, operation: Binary, domain: IntervalDomain, node: Node
    ) -> Optional[SMTTerm]:
        left_bv = self._resolve_operand_bitvec(operation.variable_left, domain, node, operation)
        right_bv = self._resolve_operand_bitvec(operation.variable_right, domain, node, operation)
        if left_bv is None or right_bv is None:
            return None

        left_bool = self._bitvec_to_bool(left_bv)
        right_bool = self._bitvec_to_bool(right_bv)
        if operation.type == BinaryType.ANDAND:
            bool_expr = left_bool & right_bool
        elif operation.type == BinaryType.OROR:
            bool_expr = left_bool | right_bool
        else:
            return None
        return self._bool_to_bitvec(bool_expr)

    def _resolve_operand_bitvec(
        self, operand, domain: IntervalDomain, node: Node, operation: Binary
    ) -> Optional[SMTTerm]:
        if self.solver is None:
            return None

        if isinstance(operand, Constant):
            var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            return IntervalSMTUtils.create_constant_term(self.solver, operand.value, var_type)

        operand_name = IntervalSMTUtils.resolve_variable_name(operand)
        if operand_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, operand_name)
        if tracked is None:
            self.logger.error_and_raise(
                "Variable '{var_name}' not found in domain for comparison operation operand",
                ValueError,
                var_name=operand_name,
                embed_on_error=True,
                node=node,
                operation=operation,
                domain=domain,
            )
        return tracked.term

    def _bool_bitvec_sort(self) -> Sort:
        return Sort(kind=SortKind.BITVEC, parameters=[1])

    def _bool_to_bitvec(self, condition: SMTTerm) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for bool conversion")
        one, zero = self._bool_constants()
        return self.solver.make_ite(condition, one, zero)

    def _bitvec_to_bool(self, term: SMTTerm) -> SMTTerm:
        # Create zero with the same width as the term
        term_width = self.solver.bv_size(term)
        zero = self.solver.create_constant(0, Sort(kind=SortKind.BITVEC, parameters=[term_width]))
        return term != zero

    def _bool_one_zero_cached(self) -> tuple[SMTTerm, SMTTerm]:
        """Return (one, zero) as 1-bit bitvector constants."""
        if not hasattr(self, "_bool_one_cached"):
            sort = self._bool_bitvec_sort()
            self._bool_one_cached = self.solver.create_constant(1, sort)
            self._bool_zero_cached = self.solver.create_constant(0, sort)
        return self._bool_one_cached, self._bool_zero_cached

    def _bool_constants(self) -> tuple[SMTTerm, SMTTerm]:
        """Return (one, zero) as 1-bit bitvector constants."""
        return self._bool_one_zero_cached()

    @staticmethod
    def get_binary_operation_from_temp(
        temp_var_name: str, domain: IntervalDomain
    ) -> Optional[Binary]:
        """Retrieve the original Binary operation that produced a temporary variable."""
        return domain.state.get_binary_operation(temp_var_name)

    @staticmethod
    def validate_constraint_from_temp(
        temp_var_name: str, domain: IntervalDomain
    ) -> Optional[Binary]:
        """Validate that a temporary variable represents a valid constraint from a Binary operation."""
        operation = domain.state.get_binary_operation(temp_var_name)
        if operation is None:
            return None

        # Validate that the operation is a comparison or logical operation
        if operation.type in ComparisonBinaryHandler._LOGICAL_TYPES:
            return operation

        # Check if it's a comparison operation
        comparison_types = {
            BinaryType.LESS,
            BinaryType.GREATER,
            BinaryType.LESS_EQUAL,
            BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL,
            BinaryType.NOT_EQUAL,
        }
        if operation.type in comparison_types:
            return operation

        return None

    def build_comparison_constraint(
        self, binary_op: Binary, domain: IntervalDomain, node: Node, operation: Binary
    ) -> Optional[SMTTerm]:
        """Build an SMT constraint from a Binary comparison operation using pure bitvector ops."""
        if self.solver is None:
            return None

        # Get bitvector terms directly (no BV2Int conversion)
        left_bv = self._resolve_operand_bitvec(binary_op.variable_left, domain, node, operation)
        right_bv = self._resolve_operand_bitvec(binary_op.variable_right, domain, node, operation)

        if left_bv is None or right_bv is None:
            return None

        # Determine signedness from operand types
        is_signed = self._is_comparison_signed(binary_op.variable_left, binary_op.variable_right, domain)

        # Normalize widths if they differ
        left_bv, right_bv = self._normalize_widths(left_bv, right_bv, is_signed)

        comp_type = binary_op.type
        if comp_type == BinaryType.GREATER_EQUAL:
            return self.solver.bv_sge(left_bv, right_bv) if is_signed else self.solver.bv_uge(left_bv, right_bv)
        if comp_type == BinaryType.GREATER:
            return self.solver.bv_sgt(left_bv, right_bv) if is_signed else self.solver.bv_ugt(left_bv, right_bv)
        if comp_type == BinaryType.LESS_EQUAL:
            return self.solver.bv_sle(left_bv, right_bv) if is_signed else self.solver.bv_ule(left_bv, right_bv)
        if comp_type == BinaryType.LESS:
            return self.solver.bv_slt(left_bv, right_bv) if is_signed else self.solver.bv_ult(left_bv, right_bv)
        if comp_type == BinaryType.EQUAL:
            return left_bv == right_bv
        if comp_type == BinaryType.NOT_EQUAL:
            return left_bv != right_bv

        return None
