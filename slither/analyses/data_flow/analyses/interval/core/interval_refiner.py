from decimal import Decimal
from typing import List, Optional, Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.core.types.interval_range import \
    IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import \
    RangeVariable
from slither.slithir.operations.binary import BinaryType


class IntervalRefiner:
    """Pure interval refinement logic for constraint application."""

    @staticmethod
    def refine_variable_range(
        range_var: RangeVariable,
        constant_value: Union[int, float, str],
        operation_type: BinaryType,
    ) -> None:
        """Refine a variable's range based on a constant comparison."""
        try:
            constant_decimal = Decimal(str(constant_value))

            # Get the current intervals using the getter method
            current_intervals = range_var.get_interval_ranges()

            if not current_intervals:
                logger.debug("No current intervals to refine")
                return

            # Handle equality constraint specially - use valid_values instead of intervals
            if operation_type == BinaryType.EQUAL:
                # Check if the constant is within any of the current intervals
                constant_in_range = any(
                    interval.get_lower() <= constant_decimal <= interval.get_upper()
                    for interval in current_intervals
                )

                if constant_in_range:
                    # Clear all intervals and add the exact value to valid_values
                    range_var.clear_intervals()
                    range_var.add_valid_value(constant_decimal)
                    logger.debug(
                        f"Set exact value {constant_decimal} in valid_values for equality constraint"
                    )
                else:
                    # Constant is not in any valid range, clear everything
                    range_var.clear_intervals()
                    logger.debug("Constant not in valid range for equality constraint")
                return

            # Handle NOT_EQUAL constraint specially - add constant to invalid_values
            if operation_type == BinaryType.NOT_EQUAL:
                # Add the constant to invalid_values since it's explicitly excluded
                range_var.add_invalid_value(constant_decimal)

            # Create new refined intervals based on the comparison
            new_intervals = []

            for interval in current_intervals:
                refined_interval = IntervalRefiner._refine_interval_with_constraint(
                    interval, constant_decimal, operation_type
                )
                if refined_interval is not None:
                    if isinstance(refined_interval, list):
                        # Handle case where interval was split (e.g., for != operator)
                        new_intervals.extend(refined_interval)
                    else:
                        new_intervals.append(refined_interval)

            # Update the range variable with refined intervals using proper methods
            if new_intervals:
                # Clear existing intervals and add new ones
                range_var.clear_intervals()
                for interval in new_intervals:
                    range_var.add_interval_range(interval)

            else:
                # Clear all intervals if no valid ones remain
                range_var.clear_intervals()
                logger.debug("No valid intervals remain after constraint application")

        except Exception as e:
            logger.error(f"Error refining variable range: {e}")
            raise

    @staticmethod
    def _refine_interval_with_constraint(
        interval: IntervalRange, constant_value: Decimal, operation_type: BinaryType
    ) -> Optional[Union[IntervalRange, List[IntervalRange]]]:
        """Refine a single interval based on a constant constraint."""
        try:
            lower = interval.get_lower()
            upper = interval.get_upper()

            if operation_type == BinaryType.LESS:
                # x < constant: refine upper bound
                if upper > constant_value:
                    new_upper = constant_value - 1  # One less than constant (integer)
                    if new_upper >= lower:
                        return IntervalRange(lower, new_upper)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.LESS_EQUAL:
                # x <= constant: refine upper bound
                if upper > constant_value:
                    if constant_value >= lower:
                        return IntervalRange(lower, constant_value)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.GREATER:
                # x > constant: refine lower bound
                if lower < constant_value:
                    new_lower = constant_value + 1  # One more than constant (integer)
                    if new_lower <= upper:
                        return IntervalRange(new_lower, upper)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.GREATER_EQUAL:
                # x >= constant: refine lower bound
                if lower < constant_value:
                    if constant_value <= upper:
                        return IntervalRange(constant_value, upper)
                    else:
                        return None  # No valid interval

            elif operation_type == BinaryType.EQUAL:
                # x == constant: this should be handled in the main flow, not here
                # Return None to indicate no interval processing needed
                return None

            elif operation_type == BinaryType.NOT_EQUAL:
                # x != constant: split interval if constant is inside
                if lower < constant_value < upper:
                    # Split into two intervals
                    return [
                        IntervalRange(lower, constant_value - 1),
                        IntervalRange(constant_value + 1, upper),
                    ]
                elif constant_value == lower:
                    # Remove lower bound
                    return IntervalRange(constant_value + 1, upper)
                elif constant_value == upper:
                    # Remove upper bound
                    return IntervalRange(lower, constant_value - 1)
                else:
                    # Constant outside interval, no change needed
                    return interval

            # If no constraint applied, return original interval
            return interval

        except Exception as e:
            logger.error(f"Error refining interval: {e}")
            raise
