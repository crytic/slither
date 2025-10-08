from decimal import Decimal
from typing import Optional, Set, Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import \
    IntervalDomain
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import \
    IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import \
    RangeVariable
from slither.analyses.data_flow.analyses.interval.managers.operand_analysis_manager import \
    OperandAnalysisManager
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import \
    VariableInfoManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.variables.constant import Constant

class ConditionValidityChecker:
    """
    Validates whether a condition can be satisfied given current domain constraints.
    Prevents application of impossible constraints that would lead to empty domains.
    """

    def __init__(
        self, variable_manager: VariableInfoManager, operand_analyzer: OperandAnalysisManager
    ) -> None:
        self._variable_manager = variable_manager
        self._operand_analyzer = operand_analyzer

    def is_condition_valid(self, condition: Binary, domain: IntervalDomain) -> bool:
        """Check if a condition can be satisfied given the current domain state."""
        if not condition:
            return True

        try:
            left_operand = condition.variable_left
            right_operand = condition.variable_right
            operator_type = condition.type

            # Handle constant-constant conditions (compile-time evaluation)
            if self._are_both_operands_constants(left_operand, right_operand, domain):
                return self._evaluate_constant_constant_condition(
                    left_operand, right_operand, operator_type, domain
                )

            # Handle variable-constant conditions (most common case)
            if self._is_variable_constant_condition(left_operand, right_operand, domain):
                return self._evaluate_variable_constant_condition(
                    left_operand, right_operand, operator_type, domain
                )

            # Handle variable-variable conditions
            if self._is_variable_variable_condition(left_operand, right_operand, domain):
                return self._evaluate_variable_variable_condition(
                    left_operand, right_operand, operator_type, domain
                )

            # If we can't determine condition validity, throw an error
            logger.error(f"Cannot determine validity for condition: {condition}")
            raise ValueError(f"Cannot determine validity for condition: {condition}")

        except Exception as e:
            logger.error(f"Error validating condition {condition}: {e}")
            raise  # Re-raise the exception to stop execution

    def _are_both_operands_constants(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        domain: IntervalDomain,
    ) -> bool:
        """Check if both operands are effectively constants."""
        return self._operand_analyzer.is_operand_constant(
            left_operand, domain
        ) and self._operand_analyzer.is_operand_constant(right_operand, domain)

    def _is_variable_constant_condition(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        domain: IntervalDomain,
    ) -> bool:
        """Check if one operand is variable and other is constant."""
        left_is_variable = not self._operand_analyzer.is_operand_constant(left_operand, domain)
        right_is_variable = not self._operand_analyzer.is_operand_constant(right_operand, domain)
        return (left_is_variable and not right_is_variable) or (
            not left_is_variable and right_is_variable
        )

    def _is_variable_variable_condition(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        domain: IntervalDomain,
    ) -> bool:
        """Check if both operands are variables."""
        return not self._operand_analyzer.is_operand_constant(
            left_operand, domain
        ) and not self._operand_analyzer.is_operand_constant(right_operand, domain)

    def _evaluate_constant_constant_condition(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operator_type: BinaryType,
        domain: IntervalDomain,
    ) -> bool:
        """Evaluate a condition where both operands are constants."""
        try:
            left_value = self._extract_constant_value(left_operand, domain)
            right_value = self._extract_constant_value(right_operand, domain)

            if left_value is None or right_value is None:
                return True

            return self._evaluate_comparison(left_value, right_value, operator_type)

        except Exception as e:
            logger.error(f"Error evaluating constant-constant condition: {e}")
            raise  # Re-raise the exception to stop execution

    def _evaluate_variable_constant_condition(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operator_type: BinaryType,
        domain: IntervalDomain,
    ) -> bool:
        """Evaluate a variable-constant condition against current domain constraints."""
        try:
            # Identify which is variable and which is constant
            if self._operand_analyzer.is_operand_constant(left_operand, domain):
                variable_operand, constant_operand = right_operand, left_operand
                # Flip the operator since we're reversing operand order
                operator_type = self._flip_comparison_operator(operator_type)
            else:
                variable_operand, constant_operand = left_operand, right_operand

            if not isinstance(variable_operand, Variable):
                return True

            variable_name = self._variable_manager.get_variable_name(variable_operand)
            if variable_name not in domain.state.get_range_variables():
                logger.error(f"Variable '{variable_name}' not found in domain state")
                raise ValueError(f"Variable '{variable_name}' not found in domain state")

            variable_state = domain.state.get_range_variables()[variable_name]
            constant_value = self._extract_constant_value(constant_operand, domain)

            if constant_value is None:
                return True

            # Conservative check: only return False if we're 100% certain it's impossible
            return self._can_variable_satisfy_condition(
                variable_state, constant_value, operator_type
            )

        except Exception as e:
            logger.error(f"Error evaluating variable-constant condition: {e}")
            raise  # Re-raise the exception to stop execution

    def _can_variable_satisfy_condition(
        self, variable_state: RangeVariable, constant_value: Decimal, operator_type: BinaryType
    ) -> bool:
        """Check if a variable can satisfy a condition with a constant value."""

        # Check valid values first (more precise)
        if variable_state.valid_values:
            for value in variable_state.valid_values:
                comparison_result = self._evaluate_comparison(value, constant_value, operator_type)
                if comparison_result:
                    return True
            # If no valid values satisfy the condition, check if we have ranges
            if not variable_state.interval_ranges:
                return False  # No valid values and no ranges -> condition is impossible

        # Check interval ranges
        if variable_state.interval_ranges:
            for interval_range in variable_state.interval_ranges:
                range_result = self._can_interval_satisfy_condition(
                    interval_range, constant_value, operator_type
                )
                if range_result:
                    return True

        # If we get here, the condition is impossible
        return False

    def _evaluate_variable_variable_condition(
        self,
        left_operand: Union[Variable, Constant],
        right_operand: Union[Variable, Constant],
        operator_type: BinaryType,
        domain: IntervalDomain,
    ) -> bool:
        """Evaluate a variable-variable condition against current domain constraints."""
        try:
            if not isinstance(left_operand, Variable) or not isinstance(right_operand, Variable):
                return True

            left_variable_name = self._variable_manager.get_variable_name(left_operand)
            right_variable_name = self._variable_manager.get_variable_name(right_operand)

            if (
                left_variable_name not in domain.state.get_range_variables()
                or right_variable_name not in domain.state.get_range_variables()
            ):
                missing_vars = []
                if left_variable_name not in domain.state.get_range_variables():
                    missing_vars.append(left_variable_name)
                if right_variable_name not in domain.state.get_range_variables():
                    missing_vars.append(right_variable_name)
                logger.error(f"Variables not found in domain state: {missing_vars}")
                raise ValueError(f"Variables not found in domain state: {missing_vars}")

            left_variable_state = domain.state.get_range_variables()[left_variable_name]
            right_variable_state = domain.state.get_range_variables()[right_variable_name]

            # Get the possible value ranges for both variables
            left_value_ranges = self._get_variable_value_ranges(left_variable_state)
            right_value_ranges = self._get_variable_value_ranges(right_variable_state)

            # Check if there's any combination that satisfies the condition
            return self._can_variable_ranges_satisfy_condition(
                left_value_ranges, right_value_ranges, operator_type
            )

        except Exception as e:
            logger.error(f"Error evaluating variable-variable condition: {e}")
            raise  # Re-raise the exception to stop execution

    def _extract_constant_value(
        self, operand: Union[Variable, Constant], domain: IntervalDomain
    ) -> Optional[Decimal]:
        """Extract constant value from operand."""
        if isinstance(operand, Constant):
            return Decimal(str(operand.value))
        elif isinstance(operand, Variable):
            variable_name = self._variable_manager.get_variable_name(operand)
            if variable_name in domain.state.get_range_variables():
                variable_state = domain.state.get_range_variables()[variable_name]
                if len(variable_state.valid_values) == 1 and not variable_state.interval_ranges:
                    return list(variable_state.valid_values)[0]
        return None

    def _can_interval_satisfy_condition(
        self, interval_range: IntervalRange, constant_value: Decimal, operator_type: BinaryType
    ) -> bool:
        """Check if any value in an interval can satisfy the condition."""
        lower_bound = interval_range.lower_bound
        upper_bound = interval_range.upper_bound

        if operator_type == BinaryType.GREATER:
            return upper_bound > constant_value
        elif operator_type == BinaryType.GREATER_EQUAL:
            return upper_bound >= constant_value
        elif operator_type == BinaryType.LESS:
            return lower_bound < constant_value
        elif operator_type == BinaryType.LESS_EQUAL:
            return lower_bound <= constant_value
        elif operator_type == BinaryType.EQUAL:
            return lower_bound <= constant_value <= upper_bound
        elif operator_type == BinaryType.NOT_EQUAL:
            return not (
                lower_bound == constant_value == upper_bound
            )  # Only false if interval is single point equal to constant

        return True

    def _get_variable_value_ranges(self, variable_state: RangeVariable) -> Set[IntervalRange]:
        """Get all possible value ranges for a variable state."""
        value_ranges: Set[IntervalRange] = set()

        # If the variable type is not numeric, return empty set (no range analysis)
        if not self._variable_manager.is_type_numeric(variable_state.var_type):
            logger.debug(
                f"Skipping range analysis for non-numeric variable type: {variable_state.var_type}"
            )
            return value_ranges  # Return empty set

        # Add valid values as point ranges
        for value in variable_state.valid_values:
            value_ranges.add(IntervalRange(value, value))

        # Add existing interval ranges
        for interval_range in variable_state.interval_ranges:
            value_ranges.add(interval_range)

        # If no specific ranges, use type bounds
        if not value_ranges:
            # Get type bounds from the variable's actual type
            type_minimum, type_maximum = variable_state.get_type_bounds()
            if type_minimum is None or type_maximum is None:
                logger.error(
                    f"Cannot retrieve type bounds for numeric variable with type: {variable_state.var_type}"
                )
                raise ValueError(
                    f"Cannot retrieve type bounds for numeric variable with type: {variable_state.var_type}"
                )

            value_ranges.add(IntervalRange(type_minimum, type_maximum))

        return value_ranges

    def _can_variable_ranges_satisfy_condition(
        self,
        left_value_ranges: Set[IntervalRange],
        right_value_ranges: Set[IntervalRange],
        operator_type: BinaryType,
    ) -> bool:
        """Check if variable-variable condition can be satisfied."""
        # If either variable has no ranges (non-numeric), we can't determine validity
        if not left_value_ranges or not right_value_ranges:
            logger.debug(
                f"Cannot determine condition validity: left_ranges={len(left_value_ranges)}, right_ranges={len(right_value_ranges)}"
            )
            return True  # Assume valid when we can't determine
        
        for left_range in left_value_ranges:
            for right_range in right_value_ranges:
                if self._can_ranges_satisfy_condition(left_range, right_range, operator_type):
                    return True
        return False

    def _can_ranges_satisfy_condition(
        self,
        left_range: IntervalRange,
        right_range: IntervalRange,
        operator_type: BinaryType,
    ) -> bool:
        """Check if two ranges can satisfy a condition."""
        left_minimum = left_range.lower_bound
        left_maximum = left_range.upper_bound
        right_minimum = right_range.lower_bound
        right_maximum = right_range.upper_bound

        if operator_type == BinaryType.GREATER:
            return left_maximum > right_minimum
        elif operator_type == BinaryType.GREATER_EQUAL:
            return left_maximum >= right_minimum
        elif operator_type == BinaryType.LESS:
            return left_minimum < right_maximum
        elif operator_type == BinaryType.LESS_EQUAL:
            return left_minimum <= right_maximum
        elif operator_type == BinaryType.EQUAL:
            # Ranges overlap
            return not (left_maximum < right_minimum or right_maximum < left_minimum)
        elif operator_type == BinaryType.NOT_EQUAL:
            # Not equal if ranges don't completely overlap with same values
            return not (left_minimum == left_maximum == right_minimum == right_maximum)

        return True

    def _evaluate_comparison(
        self, left_value: Decimal, right_value: Decimal, operator_type: BinaryType
    ) -> bool:
        """Evaluate comparison for single values."""
        if operator_type == BinaryType.GREATER:
            return left_value > right_value
        elif operator_type == BinaryType.GREATER_EQUAL:
            return left_value >= right_value
        elif operator_type == BinaryType.LESS:
            return left_value < right_value
        elif operator_type == BinaryType.LESS_EQUAL:
            return left_value <= right_value
        elif operator_type == BinaryType.EQUAL:
            return left_value == right_value
        elif operator_type == BinaryType.NOT_EQUAL:
            return left_value != right_value
        return True

    def _flip_comparison_operator(self, operator_type: BinaryType) -> BinaryType:
        """Flip comparison operator when reversing operand order."""
        operator_flip_map = {
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL: BinaryType.EQUAL,
            BinaryType.NOT_EQUAL: BinaryType.NOT_EQUAL,
        }
        return operator_flip_map.get(operator_type, operator_type)
