from decimal import Decimal
from typing import Optional, Set, Tuple, Union
from loguru import logger

from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.analyses.data_flow.interval_enhanced.managers.operand_analysis_manager import (
    OperandAnalysisManager,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant


class ConditionValidityCheckerManager:
    """
    Validates whether a condition can be satisfied given current domain constraints.
    Prevents application of impossible constraints that would lead to empty domains.
    """

    def __init__(self, variable_manager: VariableManager, operand_analyzer: OperandAnalysisManager):
        self.variable_manager = variable_manager
        self.operand_analyzer = operand_analyzer

    def verify_condition_validity(self, operation: Binary, domain: IntervalDomain) -> bool:

        if not operation or not hasattr(operation, "variable_left"):
            return True

        try:
            # Extract operands
            left_operand = operation.variable_left
            right_operand = operation.variable_right
            op_type = operation.type

            # Check if both operands are constants (compile-time evaluation)
            if self._both_operands_constant(left_operand, right_operand, domain):
                return self._evaluate_constant_condition(
                    left_operand, right_operand, op_type, domain
                )

            # For variable conditions, be more conservative
            # Only return False if we're absolutely certain the condition is impossible
            if self._is_variable_constant_condition(left_operand, right_operand, domain):
                return self._validate_variable_constant_condition_conservative(
                    left_operand, right_operand, op_type, domain
                )

            # Check variable-variable conditions
            if self._is_variable_variable_condition(left_operand, right_operand, domain):
                return self._validate_variable_variable_condition(
                    left_operand, right_operand, op_type, domain
                )

            # Default: assume valid if we can't determine otherwise
            return True

        except Exception as e:
            logger.warning(f"Error validating condition {operation}: {e}")
            return True  # Fail-safe: assume valid

    def _both_operands_constant(
        self,
        left: Union[Variable, Constant],
        right: Union[Variable, Constant],
        domain: IntervalDomain,
    ) -> bool:
        """Check if both operands are effectively constants."""
        return self.operand_analyzer.is_operand_constant(
            left, domain
        ) and self.operand_analyzer.is_operand_constant(right, domain)

    def _is_variable_constant_condition(
        self,
        left: Union[Variable, Constant],
        right: Union[Variable, Constant],
        domain: IntervalDomain,
    ) -> bool:
        """Check if one operand is variable and other is constant."""
        left_is_var = not self.operand_analyzer.is_operand_constant(left, domain)
        right_is_var = not self.operand_analyzer.is_operand_constant(right, domain)
        return (left_is_var and not right_is_var) or (not left_is_var and right_is_var)

    def _is_variable_variable_condition(
        self,
        left: Union[Variable, Constant],
        right: Union[Variable, Constant],
        domain: IntervalDomain,
    ) -> bool:
        """Check if both operands are variables."""
        return not self.operand_analyzer.is_operand_constant(
            left, domain
        ) and not self.operand_analyzer.is_operand_constant(right, domain)

    def _evaluate_constant_condition(
        self,
        left: Union[Variable, Constant],
        right: Union[Variable, Constant],
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> bool:
        """Evaluate a condition where both operands are constants."""
        try:
            left_val = self._get_constant_value(left, domain)
            right_val = self._get_constant_value(right, domain)

            if left_val is None or right_val is None:
                return True

            # Evaluate the condition
            if op_type == BinaryType.GREATER:
                return left_val > right_val
            elif op_type == BinaryType.GREATER_EQUAL:
                return left_val >= right_val
            elif op_type == BinaryType.LESS:
                return left_val < right_val
            elif op_type == BinaryType.LESS_EQUAL:
                return left_val <= right_val
            elif op_type == BinaryType.EQUAL:
                return left_val == right_val
            elif op_type == BinaryType.NOT_EQUAL:
                return left_val != right_val
            else:
                return True

        except Exception as e:
            logger.warning(f"Error evaluating constant condition: {e}")
            return True

    def _validate_variable_constant_condition_conservative(
        self,
        left: Union[Variable, Constant],
        right: Union[Variable, Constant],
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> bool:
        """Validate a variable-constant condition against current domain constraints (conservative version)."""
        try:
            # Identify which is variable and which is constant
            if self.operand_analyzer.is_operand_constant(left, domain):
                variable, constant = right, left
                # Flip the operator since we're reversing operand order
                op_type = self._flip_operator(op_type)
            else:
                variable, constant = left, right

            if not isinstance(variable, Variable):
                return True

            var_name = self.variable_manager.get_variable_name(variable)
            if var_name not in domain.state.info:
                return True  # Unknown variable, assume valid

            var_state = domain.state.info[var_name]
            constant_value = self._get_constant_value(constant, domain)

            if constant_value is None:
                return True

            # Conservative check: only return False if we're 100% certain it's impossible
            return self._check_condition_satisfiability_conservative(
                var_state, constant_value, op_type
            )

        except Exception as e:
            logger.warning(f"Error validating variable-constant condition: {e}")
            return True

    def _check_condition_satisfiability_conservative(
        self, var_state, constant_value: Decimal, op_type: BinaryType
    ) -> bool:
        """Conservative satisfiability check - only return False if absolutely impossible."""

        # Check valid values first (more precise)
        if not var_state.valid_values.is_empty():
            for value in var_state.valid_values:
                if self._evaluate_single_condition(value, constant_value, op_type):
                    return True
            # If no valid values satisfy the condition, check if we have ranges
            if not var_state.interval_ranges:
                return False  # No valid values and no ranges -> condition is impossible

        # Check interval ranges
        if var_state.interval_ranges:
            for range_obj in var_state.interval_ranges:
                if self._interval_satisfies_condition(range_obj, constant_value, op_type):
                    return True

        # If we get here, the condition is impossible
        return False

    def _validate_variable_variable_condition(
        self,
        left: Union[Variable, Constant],
        right: Union[Variable, Constant],
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> bool:
        """Validate a variable-variable condition against current domain constraints."""
        try:
            if not isinstance(left, Variable) or not isinstance(right, Variable):
                return True

            left_name = self.variable_manager.get_variable_name(left)
            right_name = self.variable_manager.get_variable_name(right)

            if left_name not in domain.state.info or right_name not in domain.state.info:
                return True  # Unknown variables, assume valid

            left_state = domain.state.info[left_name]
            right_state = domain.state.info[right_name]

            # Get the possible value ranges for both variables
            left_ranges = self._get_possible_value_ranges(left_state)
            right_ranges = self._get_possible_value_ranges(right_state)

            # Check if there's any combination that satisfies the condition
            return self._check_variable_variable_satisfiability(left_ranges, right_ranges, op_type)

        except Exception as e:
            logger.warning(f"Error validating variable-variable condition: {e}")
            return True

    def _get_constant_value(
        self, operand: Union[Variable, Constant], domain: IntervalDomain
    ) -> Optional[Decimal]:
        """Extract constant value from operand."""
        if isinstance(operand, Constant):
            return Decimal(str(operand.value))
        elif isinstance(operand, Variable):
            var_name = self.variable_manager.get_variable_name(operand)
            if var_name in domain.state.info:
                var_state = domain.state.info[var_name]
                if len(var_state.valid_values) == 1 and not var_state.interval_ranges:
                    return list(var_state.valid_values)[0]
        return None

    def _interval_satisfies_condition(
        self, interval_range, constant_value: Decimal, op_type: BinaryType
    ) -> bool:
        """Check if any value in an interval can satisfy the condition."""
        lower = interval_range.get_lower()
        upper = interval_range.get_upper()

        if op_type == BinaryType.GREATER:
            return upper > constant_value
        elif op_type == BinaryType.GREATER_EQUAL:
            return upper >= constant_value
        elif op_type == BinaryType.LESS:
            return lower < constant_value
        elif op_type == BinaryType.LESS_EQUAL:
            return lower <= constant_value
        elif op_type == BinaryType.EQUAL:
            return lower <= constant_value <= upper
        elif op_type == BinaryType.NOT_EQUAL:
            return not (
                lower == constant_value == upper
            )  # Only false if interval is single point equal to constant

        return True

    def _get_possible_value_ranges(self, var_state) -> Set[Tuple[Decimal, Decimal]]:
        """Get all possible value ranges for a variable state."""
        ranges = set()

        # Add valid values as point ranges
        for value in var_state.valid_values:
            ranges.add((value, value))

        # Add interval ranges
        for interval_range in var_state.interval_ranges:
            ranges.add((interval_range.get_lower(), interval_range.get_upper()))

        # If no specific ranges, use type bounds
        if not ranges:
            type_min, type_max = var_state.get_type_bounds()
            ranges.add((type_min, type_max))

        return ranges

    def _check_variable_variable_satisfiability(
        self,
        left_ranges: Set[Tuple[Decimal, Decimal]],
        right_ranges: Set[Tuple[Decimal, Decimal]],
        op_type: BinaryType,
    ) -> bool:
        """Check if variable-variable condition can be satisfied."""
        for left_min, left_max in left_ranges:
            for right_min, right_max in right_ranges:
                if self._ranges_satisfy_condition(
                    left_min, left_max, right_min, right_max, op_type
                ):
                    return True
        return False

    def _ranges_satisfy_condition(
        self,
        left_min: Decimal,
        left_max: Decimal,
        right_min: Decimal,
        right_max: Decimal,
        op_type: BinaryType,
    ) -> bool:
        """Check if two ranges can satisfy a condition."""
        if op_type == BinaryType.GREATER:
            return left_max > right_min
        elif op_type == BinaryType.GREATER_EQUAL:
            return left_max >= right_min
        elif op_type == BinaryType.LESS:
            return left_min < right_max
        elif op_type == BinaryType.LESS_EQUAL:
            return left_min <= right_max
        elif op_type == BinaryType.EQUAL:
            # Ranges overlap
            return not (left_max < right_min or right_max < left_min)
        elif op_type == BinaryType.NOT_EQUAL:
            # Not equal if ranges don't completely overlap with same values
            return not (left_min == left_max == right_min == right_max)

        return True

    def _evaluate_single_condition(
        self, left_val: Decimal, right_val: Decimal, op_type: BinaryType
    ) -> bool:
        """Evaluate condition for single values."""
        if op_type == BinaryType.GREATER:
            return left_val > right_val
        elif op_type == BinaryType.GREATER_EQUAL:
            return left_val >= right_val
        elif op_type == BinaryType.LESS:
            return left_val < right_val
        elif op_type == BinaryType.LESS_EQUAL:
            return left_val <= right_val
        elif op_type == BinaryType.EQUAL:
            return left_val == right_val
        elif op_type == BinaryType.NOT_EQUAL:
            return left_val != right_val
        return True

    def _flip_operator(self, op_type: BinaryType) -> BinaryType:
        """Flip comparison operator when reversing operand order."""
        flip_map = {
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL: BinaryType.EQUAL,
            BinaryType.NOT_EQUAL: BinaryType.NOT_EQUAL,
        }
        return flip_map.get(op_type, op_type)
