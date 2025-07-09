from decimal import Decimal
from typing import Union

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.analyses.data_flow.interval_enhanced.managers.constraint_manager import (
    ConstraintManager,
)
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.cfg.node import Node
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import Binary, BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant


class ArithmeticHandler:
    def __init__(self, constraint_manager: ConstraintManager):
        self.variable_manager = VariableManager()
        self.constraint_manager = constraint_manager

    def handle_arithmetic(self, node: Node, domain: IntervalDomain, operation: Binary) -> None:
        """Handle arithmetic operations and update domain with result"""

        # Get state info for both operands
        left_var_info = self.get_variable_info(domain, operation.variable_left)
        right_var_info = self.get_variable_info(domain, operation.variable_right)

        if not isinstance(operation.lvalue, Variable):
            logger.error(f"lvalue is not a variable for operation: {operation}")
            raise ValueError(f"lvalue is not a variable for operation: {operation}")

        # Calculate the result state info
        result_state_info = self._calculate_arithmetic_result(
            left_var_info, right_var_info, operation.type, operation.lvalue
        )

        result_var_name = self.variable_manager.get_variable_name(operation.lvalue)

        domain.state.info[result_var_name] = result_state_info

        # Register temporary variable mapping for constraint propagation
        if operation.type in self.constraint_manager.ARITHMETIC_OPERATORS:
            self.constraint_manager.add_temp_var_mapping(result_var_name, operation)

    def _calculate_arithmetic_result(
        self,
        left_info: StateInfo,
        right_info: StateInfo,
        operation_type: BinaryType,
        target_var: Variable,
    ) -> StateInfo:
        """Calculate the result of an arithmetic operation between two StateInfo objects"""

        # Handle target type safely
        if (
            target_var
            and hasattr(target_var, "type")
            and isinstance(target_var.type, ElementaryType)
        ):
            target_type = target_var.type
        else:
            # Default to uint256, but we'll determine the actual type based on the result
            target_type = ElementaryType("uint256")
        result_valid_values = SingleValues()
        result_interval_ranges = []

        # Get operation function
        operations = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y if y != 0 else Decimal("Infinity"),
        }

        if operation_type not in operations:
            # Unknown operation, return TOP
            return StateInfo(
                interval_ranges=[IntervalRange()],
                valid_values=SingleValues(),
                invalid_values=SingleValues(),
                var_type=target_type,
            )

        op_func = operations[operation_type]

        # 1. Handle valid_values + valid_values (constant + constant)
        if not left_info.valid_values.is_empty() and not right_info.valid_values.is_empty():
            # For constant + constant, we need to handle each combination
            for left_val in left_info.valid_values:
                result_valid_values = result_valid_values.join(
                    right_info.valid_values.apply_operation(left_val, lambda x, y: op_func(y, x))
                )

        # 2. Handle valid_values + interval_ranges (constant + variable)
        if not left_info.valid_values.is_empty() and left_info.interval_ranges:
            for left_val in left_info.valid_values:
                for right_range in right_info.interval_ranges:
                    try:
                        left_point = IntervalRange(upper_bound=left_val, lower_bound=left_val)
                        result_range = IntervalRange.calculate_arithmetic_bounds(
                            left_point, right_range, operation_type
                        )
                        result_interval_ranges.append(result_range)
                    except Exception as e:
                        logger.warning(f"Error in mixed arithmetic: {e}")

        # 3. Handle interval_ranges + valid_values (variable + constant)
        if left_info.interval_ranges and not right_info.valid_values.is_empty():
            for left_range in left_info.interval_ranges:
                for right_val in right_info.valid_values:
                    try:
                        right_point = IntervalRange(upper_bound=right_val, lower_bound=right_val)
                        result_range = IntervalRange.calculate_arithmetic_bounds(
                            left_range, right_point, operation_type
                        )
                        result_interval_ranges.append(result_range)
                    except Exception as e:
                        logger.warning(f"Error in mixed arithmetic: {e}")

        # 4. Handle interval_ranges + interval_ranges (variable + variable)
        if left_info.interval_ranges and right_info.interval_ranges:
            for left_range in left_info.interval_ranges:
                for right_range in right_info.interval_ranges:
                    try:
                        result_range = IntervalRange.calculate_arithmetic_bounds(
                            left_range, right_range, operation_type
                        )
                        result_interval_ranges.append(result_range)
                    except Exception as e:
                        logger.warning(f"Error in interval arithmetic: {e}")

        # If no results were computed, return TOP
        if result_valid_values.is_empty() and not result_interval_ranges:
            result_interval_ranges.append(IntervalRange())

        # Determine the appropriate type based on the result
        has_negative_values = False

        # Check valid values for negative values
        for value in result_valid_values:
            if value < 0:
                has_negative_values = True
                break

        # Check interval ranges for negative values
        if not has_negative_values:
            for interval_range in result_interval_ranges:
                if interval_range.get_lower() < 0:
                    has_negative_values = True
                    break

        # Set the appropriate type
        if has_negative_values:
            result_type = ElementaryType("int256")
        else:
            result_type = ElementaryType("uint256")

        return StateInfo(
            interval_ranges=result_interval_ranges,
            valid_values=result_valid_values,
            invalid_values=SingleValues(),
            var_type=result_type,
        )

    def get_variable_info(
        self, domain: IntervalDomain, variable: Union[Variable, Constant, RVALUE, Function]
    ) -> StateInfo:
        """Retrieve state information for a variable or constant."""
        if isinstance(variable, Constant):
            value: Decimal = Decimal(str(variable.value))
            valid_values = SingleValues()
            valid_values.add(value)

            # Determine the appropriate type for the constant
            if value < 0:
                # Negative constants should use int256
                constant_type = ElementaryType("int256")
            else:
                # Non-negative constants can use uint256
                constant_type = ElementaryType("uint256")

            # For constants, use valid_values instead of interval ranges
            return StateInfo(
                interval_ranges=[],  # No interval ranges for constants
                valid_values=valid_values,
                invalid_values=SingleValues(),
                var_type=constant_type,
            )
        elif isinstance(variable, Variable):
            var_name: str = self.variable_manager.get_variable_name(variable)
            if var_name in domain.state.info:
                return domain.state.info[var_name]
            else:
                # Default state for unknown variables
                return StateInfo(
                    interval_ranges=[IntervalRange()],
                    valid_values=SingleValues(),
                    invalid_values=SingleValues(),
                    var_type=ElementaryType("uint256"),
                )
        else:
            # Default state for other types
            return StateInfo(
                interval_ranges=[IntervalRange()],
                valid_values=SingleValues(),
                invalid_values=SingleValues(),
                var_type=ElementaryType("uint256"),
            )
