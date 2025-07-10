from decimal import Decimal
from typing import Dict
import math

from loguru import logger
from slither.analyses.data_flow.interval_enhanced.analysis.domain import IntervalDomain
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.managers.variable_manager import VariableManager
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import BinaryType


class ConstraintRangeManager:
    """Handles constraint range creation and manipulation for interval analysis."""

    def __init__(self, variable_manager: VariableManager):
        self.variable_manager = variable_manager

    def create_constraint_range(
        self, value: Decimal, op_type: BinaryType, type_min: Decimal, type_max: Decimal
    ) -> IntervalRange:
        """Create an interval range representing the constraint"""

        if op_type == BinaryType.LESS:
            # x < value -> [type_min, value-1] for integers, [type_min, floor(value)] for decimals
            if value % 1 == 0:
                # Integer value: subtract 1
                upper_bound = value - Decimal("1")
            else:
                # Decimal value: round down to nearest integer
                upper_bound = Decimal(str(math.floor(float(value))))
            return IntervalRange(lower_bound=type_min, upper_bound=upper_bound)
        elif op_type == BinaryType.LESS_EQUAL:
            # x <= value -> [type_min, value]
            return IntervalRange(lower_bound=type_min, upper_bound=value)
        elif op_type == BinaryType.GREATER:
            # x > value -> [value+1, type_max] for integers, [ceil(value), type_max] for decimals
            if value % 1 == 0:
                # Integer value: add 1
                lower_bound = value + Decimal("1")
            else:
                # Decimal value: round up to nearest integer
                lower_bound = Decimal(str(math.ceil(float(value))))
            return IntervalRange(lower_bound=lower_bound, upper_bound=type_max)
        elif op_type == BinaryType.GREATER_EQUAL:
            # x >= value -> [value, type_max]
            return IntervalRange(lower_bound=value, upper_bound=type_max)
        elif op_type == BinaryType.EQUAL:
            # x == value -> [value, value]
            return IntervalRange(lower_bound=value, upper_bound=value)
        elif op_type == BinaryType.NOT_EQUAL:
            # x != value -> use full range, but add value to invalid_values
            # The actual invalidation will be handled in update_variable_bounds_from_condition
            return IntervalRange(lower_bound=type_min, upper_bound=type_max)
        else:
            # Unknown operator, return full range
            logger.warning(f"Unknown comparison operator: {op_type}")
            return IntervalRange(lower_bound=type_min, upper_bound=type_max)

    def flip_comparison_operator(self, op_type: BinaryType) -> BinaryType:
        """Flip comparison operator for handling constant-variable comparisons."""
        flip_map: Dict[BinaryType, BinaryType] = {
            BinaryType.GREATER: BinaryType.LESS,
            BinaryType.LESS: BinaryType.GREATER,
            BinaryType.GREATER_EQUAL: BinaryType.LESS_EQUAL,
            BinaryType.LESS_EQUAL: BinaryType.GREATER_EQUAL,
            BinaryType.EQUAL: BinaryType.EQUAL,
            BinaryType.NOT_EQUAL: BinaryType.NOT_EQUAL,
        }
        return flip_map[op_type]

    def apply_constraint_to_variable(
        self, var_name: str, constraint_range: IntervalRange, domain: IntervalDomain
    ) -> None:
        """Apply a constraint range to a variable's existing intervals"""
        if var_name not in domain.state.info:
            return

        state_info = domain.state.info[var_name]

        # Apply constraint to all existing intervals
        constrained_ranges = []
        for existing_range in state_info.interval_ranges:
            intersection = existing_range.intersection(constraint_range)
            if intersection is not None:
                constrained_ranges.append(intersection)

        # Update the variable's interval ranges
        state_info.interval_ranges = constrained_ranges

    def apply_constraint_to_variable_with_value(
        self,
        variable: Variable,
        constraint_value: Decimal,
        op_type: BinaryType,
        domain: IntervalDomain,
    ) -> None:
        """Apply constraint to variable and update domain."""
        var_name = self.variable_manager.get_variable_name(variable)

        if var_name not in domain.state.info:
            logger.error(f"Variable '{var_name}' not found in domain state")
            return

        state_info = domain.state.info[var_name]

        if op_type == BinaryType.EQUAL:
            # Nuke the intervals and set the exact value as valid
            state_info.clear_intervals()
            state_info.valid_values.add(constraint_value)  # Add the exact value
            return

        # Get type bounds for the variable
        type_min, type_max = state_info.get_type_bounds()

        # Create constraint range based on comparison operator
        constraint_range = self.create_constraint_range(
            constraint_value, op_type, type_min, type_max
        )

        # Apply constraint to all existing intervals
        constrained_ranges = []
        for existing_range in state_info.interval_ranges:
            intersection = existing_range.intersection(constraint_range)
            if intersection is not None:
                constrained_ranges.append(intersection)

        # Update the variable's interval ranges
        state_info.interval_ranges = constrained_ranges
