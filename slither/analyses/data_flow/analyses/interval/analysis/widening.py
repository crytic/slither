from decimal import Decimal
from typing import Dict, List, Optional, Set

from loguru import logger

from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.range_variable import RangeVariable
from slither.core.solidity_types.elementary_type import ElementaryType


class Widening:
    """Manages widening operations for interval analysis."""

    def __init__(self) -> None:
        self._widened_variables: Set[str] = set()  # Track variables that have been widened

    def apply_widening(
        self,
        current_state: IntervalDomain,
        previous_state: IntervalDomain,
        widening_literals: Set[int],
    ) -> IntervalDomain:
        """Apply widening operations to the current state."""

        # Identify variables that have changed between iterations
        changed_variables: Dict[str, Dict[str, RangeVariable]] = self._identify_changed_variables(
            current_state, previous_state
        )

        if changed_variables:

            # Apply widening to each changed variable
            widened_state = current_state.deep_copy()
            for var_name, variable_data in changed_variables.items():
                current_var: RangeVariable = variable_data["current"]
                previous_var: RangeVariable = variable_data["previous"]

                # Apply widening to this variable
                widened_var: RangeVariable = self._apply_widening_to_variable(
                    current_var, previous_var, widening_literals
                )
                widened_state.state.set_range_variable(var_name, widened_var)

                # Clear valid values for all changed variables since we're applying widening
                widened_var.valid_values.clear()

                # Mark this variable as widened to prevent future discrete value assignments
                self._widened_variables.add(var_name)

        else:

            widened_state = current_state

        return widened_state

    def _identify_changed_variables(
        self, current_state: IntervalDomain, previous_state: IntervalDomain
    ) -> Dict[str, Dict[str, RangeVariable]]:
        """Identify variables that have different values between current and previous states."""
        changed_variables: Dict[str, Dict[str, RangeVariable]] = {}

        # Check if both states have state info
        if not hasattr(current_state, "state") or not hasattr(previous_state, "state"):
            return changed_variables

        current_variables = current_state.state.get_range_variables()
        previous_variables = previous_state.state.get_range_variables()

        # Check variables present in both states
        common_variables = set(current_variables.keys()) & set(previous_variables.keys())

        for var_name in common_variables:
            current_var: RangeVariable = current_variables[var_name]
            previous_var: RangeVariable = previous_variables[var_name]

            if current_var != previous_var:
                changed_variables[var_name] = {"current": current_var, "previous": previous_var}

        return changed_variables

    def _apply_widening_to_variable(
        self, current_var: RangeVariable, previous_var: RangeVariable, widening_literals: Set[int]
    ) -> RangeVariable:
        """Apply widening operator ∇' to a single variable based on the widening rules."""
        # Create a copy of the current variable to modify
        widened_var: RangeVariable = current_var.deep_copy()

        # Convert discrete values to ranges for widening
        current_ranges: List[IntervalRange] = self._extract_ranges_for_widening(current_var)
        previous_ranges: List[IntervalRange] = self._extract_ranges_for_widening(previous_var)

        # Apply widening to ranges
        if current_ranges and previous_ranges:
            # For simplicity, apply widening to the first range of each variable
            if len(current_ranges) > 0 and len(previous_ranges) > 0:
                current_range: IntervalRange = current_ranges[0]
                previous_range: IntervalRange = previous_ranges[0]

                # Apply widening rules to the interval
                prev_lower = previous_range.get_lower()
                curr_lower = current_range.get_lower()
                prev_upper = previous_range.get_upper()
                curr_upper = current_range.get_upper()

                # Ensure we have valid Decimal values
                if prev_lower is None or curr_lower is None:
                    logger.error(
                        f"Invalid lower bound values: prev={prev_lower}, curr={curr_lower}"
                    )
                    raise ValueError(
                        f"Invalid lower bound values: prev={prev_lower}, curr={curr_lower}"
                    )
                if prev_upper is None or curr_upper is None:
                    logger.error(
                        f"Invalid upper bound values: prev={prev_upper}, curr={curr_upper}"
                    )
                    raise ValueError(
                        f"Invalid upper bound values: prev={prev_upper}, curr={curr_upper}"
                    )

                widened_lower: Decimal = self._widen_lower_bound(
                    prev_lower,
                    curr_lower,
                    widening_literals,
                )
                widened_upper: Decimal = self._widen_upper_bound(
                    prev_upper,
                    curr_upper,
                    widening_literals,
                )

                # Create the widened interval range
                widened_range: IntervalRange = IntervalRange(
                    lower_bound=widened_lower, upper_bound=widened_upper
                )

                # Replace the interval ranges with the widened one
                widened_var.interval_ranges = [widened_range]
                # Clear valid values since we now have a range
                widened_var.valid_values.clear()

        # Always clear valid values when widening is applied (even if no ranges were created)
        widened_var.valid_values.clear()

        # Consolidate ranges to remove duplicates and overlaps FIRST
        widened_var.consolidate_ranges()

        # Apply widening to the consolidated ranges by comparing with previous state
        if widened_var.interval_ranges and previous_var.interval_ranges:
            # Get the previous consolidated range (should be single range after consolidation)
            if len(previous_var.interval_ranges) > 0:
                prev_range = previous_var.interval_ranges[
                    0
                ]  # Take first (should be only one after consolidation)

                # Apply widening to each current consolidated range
                widened_ranges = []
                for range_obj in widened_var.interval_ranges:
                    widened_range = self._apply_widening_between_ranges(
                        range_obj, prev_range, widening_literals
                    )
                    widened_ranges.append(widened_range)
                widened_var.interval_ranges = widened_ranges

        return widened_var

    def _apply_widening_between_ranges(
        self,
        current_range: IntervalRange,
        previous_range: IntervalRange,
        widening_literals: Set[int],
    ) -> IntervalRange:
        """Apply widening to a range by comparing with the previous range."""
        # Get bounds
        current_lower = current_range.get_lower()
        current_upper = current_range.get_upper()
        previous_lower = previous_range.get_lower()
        previous_upper = previous_range.get_upper()

        # Apply widening to bounds
        widened_lower = self._widen_lower_bound(previous_lower, current_lower, widening_literals)
        widened_upper = self._widen_upper_bound(previous_upper, current_upper, widening_literals)

        # Create new widened range
        widened_range = IntervalRange(widened_lower, widened_upper)

        return widened_range

    def _extract_ranges_for_widening(self, var: RangeVariable) -> List[IntervalRange]:
        """Get interval ranges for widening, converting from discrete values if needed."""
        # If variable already has interval ranges, use them
        if var.interval_ranges:
            return var.interval_ranges

        # If variable has discrete values, convert them to ranges
        if var.valid_values and len(var.valid_values) > 0:
            values = sorted(var.valid_values)
            if values:
                # Create a range from min to max of the discrete values
                min_val = min(values)
                max_val = max(values)
                return [IntervalRange(lower_bound=min_val, upper_bound=max_val)]

        # If no ranges or values, return empty list
        return []

    def _widen_lower_bound(
        self,
        prev_lower: Decimal,
        curr_lower: Decimal,
        widening_literals: Set[int],
    ) -> Decimal:
        """Apply lower bound widening rule."""
        # If l₁ ≤ l₂ (lower bound is stable/non-decreasing): keep l₃ = l₁
        if prev_lower <= curr_lower:
            # logger.info(f"🔄 Lower bound stable: {prev_lower} ≤ {curr_lower}, keeping {prev_lower}")
            return prev_lower
        # If l₁ > l₂ (lower bound is unstable/decreasing): widen to l₃ = max{i ∈ B | i ≤ l₂}
        else:

            # Find the maximum value in widening literals that is less than or equal to curr_lower
            valid_candidates = [i for i in widening_literals if i <= curr_lower]
            if valid_candidates:
                result = max(valid_candidates)
                # Ensure result is converted to Decimal safely
                try:
                    if isinstance(result, Decimal):
                        return result
                    elif isinstance(result, int):
                        # For large ints, use string conversion
                        return Decimal(str(result))
                    elif isinstance(result, float):
                        return Decimal(result)
                    else:
                        logger.warning(
                            f"Unexpected result type in _widen_lower_bound: {type(result)}, value: {result}"
                        )
                        return Decimal(str(result))
                except Exception as e:
                    logger.error(
                        f"Error converting result to Decimal: {result} (type: {type(result)}), error: {e}"
                    )
                    # Fallback to default minimum
                    return Decimal("0")
            else:
                # If no suitable value found, use default minimum
                result = Decimal("0")  # Default for uint types
                return result

    def _widen_upper_bound(
        self,
        prev_upper: Decimal,
        curr_upper: Decimal,
        widening_literals: Set[int],
    ) -> Decimal:
        """Apply upper bound widening rule."""
        # If h₂ ≤ h₁ (upper bound is stable/non-increasing): keep h₃ = h₁
        if curr_upper <= prev_upper:
            # logger.info(f"🔄 Upper bound stable: {curr_upper} ≤ {prev_upper}, keeping {prev_upper}")
            return prev_upper
        # If h₂ > h₁ (upper bound is unstable/increasing): widen to h₃ = min{i ∈ B | h₂ ≤ i}
        else:
            # logger.info(
            #     f"🔄 Upper bound unstable: {curr_upper} > {prev_upper}, looking for candidates in widening literals: {widening_literals}"
            # )
            # Find the minimum value in widening literals that is greater than or equal to curr_upper
            valid_candidates = [i for i in widening_literals if i >= curr_upper]
            if valid_candidates:
                result = min(valid_candidates)
                # logger.info(f"🔄 Found candidate in widening literals: {result}")
                # Ensure result is converted to Decimal safely
                try:
                    if isinstance(result, Decimal):
                        return result
                    elif isinstance(result, int):
                        # For large ints, use string conversion
                        return Decimal(str(result))
                    elif isinstance(result, float):
                        return Decimal(result)
                    else:
                        logger.warning(
                            f"Unexpected result type in _widen_upper_bound: {type(result)}, value: {result}"
                        )
                        return Decimal(str(result))
                except Exception as e:
                    logger.error(
                        f"Error converting result to Decimal: {result} (type: {type(result)}), error: {e}"
                    )
                    # Fallback: try to convert curr_upper or use a safe default
                    if isinstance(curr_upper, Decimal):
                        return curr_upper
                    else:
                        return Decimal("0")
            else:
                # If no suitable value found, use the maximum value in widening literals
                # This ensures widening is capped by the program's literals
                if widening_literals:
                    result = max(widening_literals)

                    # Ensure result is converted to Decimal safely
                    try:
                        if isinstance(result, Decimal):
                            return result
                        elif isinstance(result, int):
                            # For large ints, use string conversion
                            return Decimal(str(result))
                        elif isinstance(result, float):
                            return Decimal(result)
                        else:
                            logger.warning(
                                f"Unexpected result type in _widen_upper_bound: {type(result)}, value: {result}"
                            )
                            return Decimal(str(result))
                    except Exception as e:
                        logger.error(
                            f"Error converting result to Decimal: {result} (type: {type(result)}), error: {e}"
                        )
                        # Fallback: try to convert curr_upper or use a safe default
                        if isinstance(curr_upper, Decimal):
                            return curr_upper
                        else:
                            return Decimal("0")
                else:
                    # Fallback to uint256 maximum if widening literals is empty
                    result = Decimal(
                        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                    )  # uint256 max
                    # logger.info(f"🔄 Empty widening literals, using default max: {result}")
                    return result

    def is_variable_widened(self, var_name: str) -> bool:
        """Check if a variable has been widened and should not receive discrete values."""
        return var_name in self._widened_variables

    def prevent_discrete_assignment(self, var_name: str, range_variable: RangeVariable) -> None:
        """Prevent discrete value assignments to widened variables."""
        if self.is_variable_widened(var_name):
            # Clear any discrete values that might have been added
            range_variable.valid_values.clear()
