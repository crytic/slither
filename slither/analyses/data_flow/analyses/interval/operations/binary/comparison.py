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
            comparison_bitvec = self._build_logical(operation, domain)
        else:
            comparison_bitvec = self._build_comparison(operation, domain)

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

    def _build_comparison(self, operation: Binary, domain: IntervalDomain) -> Optional[SMTTerm]:
        left_int = self._resolve_operand_int(operation.variable_left, domain)
        right_int = self._resolve_operand_int(operation.variable_right, domain)

        if left_int is None or right_int is None:
            return None

        comp_type = operation.type
        bool_expr: Optional[SMTTerm] = None
        if comp_type.value == ">=":
            bool_expr = left_int >= right_int
        elif comp_type.value == ">":
            bool_expr = left_int > right_int
        elif comp_type.value == "<=":
            bool_expr = left_int <= right_int
        elif comp_type.value == "<":
            bool_expr = left_int < right_int
        elif comp_type.value == "==":
            bool_expr = left_int == right_int
        elif comp_type.value == "!=":
            bool_expr = left_int != right_int

        if bool_expr is None:
            return None

        return self._bool_to_bitvec(bool_expr)

    def _build_logical(self, operation: Binary, domain: IntervalDomain) -> Optional[SMTTerm]:
        left_bv = self._resolve_operand_bitvec(operation.variable_left, domain)
        right_bv = self._resolve_operand_bitvec(operation.variable_right, domain)
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

    def _resolve_operand_bitvec(self, operand, domain: IntervalDomain) -> Optional[SMTTerm]:
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
            solidity_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            if solidity_type is None:
                return None
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, operand_name, solidity_type
            )
            if tracked is None:
                return None
            domain.state.set_range_variable(operand_name, tracked)
            tracked.assert_no_overflow(self.solver)
        return tracked.term

    def _resolve_operand_int(self, operand, domain: IntervalDomain) -> Optional[SMTTerm]:
        if self.solver is None:
            return None

        if isinstance(operand, Constant):
            var_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            bitvec = IntervalSMTUtils.create_constant_term(self.solver, operand.value, var_type)
            is_signed = IntervalSMTUtils.is_signed_type(var_type) if var_type else False
            return self._term_to_int(bitvec, is_signed)

        operand_name = IntervalSMTUtils.resolve_variable_name(operand)
        if operand_name is None:
            return None

        tracked = IntervalSMTUtils.get_tracked_variable(domain, operand_name)
        if tracked is None:
            solidity_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
            if solidity_type is None:
                return None
            tracked = IntervalSMTUtils.create_tracked_variable(
                self.solver, operand_name, solidity_type
            )
            if tracked is None:
                return None
            domain.state.set_range_variable(operand_name, tracked)
            tracked.assert_no_overflow(self.solver)

            # If this is an SSA version (contains "|"), check if the base variable has an initial value
            # and propagate it. For example, if base variable "value" = 0, then "value|value_0" should also = 0
            if "|" in operand_name:
                base_name = operand_name.split("|")[0]
                base_tracked = IntervalSMTUtils.get_tracked_variable(domain, base_name)
                # If base variable exists and we're creating the first SSA version (_0),
                # check if we need to propagate initial value constraint
                ssa_part = operand_name.split("|")[-1]
                if base_tracked is not None and ssa_part.endswith("_0"):
                    from slither.core.solidity_types.elementary_type import Int, Uint

                    type_str = solidity_type.type if solidity_type else None
                    if type_str and (type_str in Uint or type_str in Int or type_str == "bool"):
                        # Assert that the SSA version equals 0 (default for uninitialized variables)
                        zero_constant = self.solver.create_constant(0, tracked.sort)
                        self.solver.assert_constraint(tracked.term == zero_constant)

        is_signed = self._is_signed(operand, tracked)
        return self._term_to_int(tracked.term, is_signed)

    def _term_to_int(self, term: SMTTerm, is_signed: bool) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for term conversion")
        if is_signed:
            return self.solver.bitvector_to_signed_int(term)
        return self.solver.bitvector_to_int(term)

    def _is_signed(self, operand, tracked: TrackedSMTVariable) -> bool:
        solidity_type = IntervalSMTUtils.resolve_elementary_type(getattr(operand, "type", None))
        if solidity_type is not None:
            return IntervalSMTUtils.is_signed_type(solidity_type)
        return bool(tracked.base.metadata.get("is_signed"))

    def _bool_bitvec_sort(self) -> Sort:
        return Sort(kind=SortKind.BITVEC, parameters=[256])

    def _bool_to_bitvec(self, condition: SMTTerm) -> SMTTerm:
        if self.solver is None:
            raise RuntimeError("Solver is required for bool conversion")
        one, zero = self._bool_constants()
        return self.solver.make_ite(condition, one, zero)

    def _bitvec_to_bool(self, term: SMTTerm) -> SMTTerm:
        zero, _ = self._bool_zero_value()
        return term != zero

    def _bool_zero_value(self) -> tuple[SMTTerm, SMTTerm]:
        if not hasattr(self, "_bool_zero_cached"):
            sort = self._bool_bitvec_sort()
            self._bool_zero_cached = self.solver.create_constant(0, sort)
            self._bool_one_cached = self.solver.create_constant(1, sort)
        return self._bool_zero_cached, self._bool_one_cached

    def _bool_constants(self) -> tuple[SMTTerm, SMTTerm]:
        zero, one = self._bool_zero_value()
        return one, zero

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
        self, binary_op: Binary, domain: IntervalDomain
    ) -> Optional[SMTTerm]:
        """Build an SMT constraint from a Binary comparison operation."""
        if self.solver is None:
            return None

        left_int = self._resolve_operand_int(binary_op.variable_left, domain)
        right_int = self._resolve_operand_int(binary_op.variable_right, domain)

        if left_int is None or right_int is None:
            return None

        comp_type = binary_op.type
        if comp_type == BinaryType.GREATER_EQUAL:
            return left_int >= right_int
        if comp_type == BinaryType.GREATER:
            return left_int > right_int
        if comp_type == BinaryType.LESS_EQUAL:
            return left_int <= right_int
        if comp_type == BinaryType.LESS:
            return left_int < right_int
        if comp_type == BinaryType.EQUAL:
            return left_int == right_int
        if comp_type == BinaryType.NOT_EQUAL:
            return left_int != right_int

        return None
