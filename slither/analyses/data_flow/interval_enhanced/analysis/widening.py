from decimal import Decimal
from typing import Dict, List, Optional, Set

from loguru import logger

from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.state_info import StateInfo
from slither.core.solidity_types.elementary_type import ElementaryType


class Widening:
    """Manages widening operations for interval analysis."""

    def __init__(self) -> None:
        self._widened_variables: Set[str] = set()  # Track variables that have been widened

    def apply_widening(
        self, current_state: IntervalDomain, previous_state: IntervalDomain, set_b: Set[int]
    ) -> IntervalDomain:
        """Apply widening operations to the current state."""
        logger.info("🔄 Applying widening!")

        # Identify variables that have changed between iterations
        changed_variables: Dict[str, Dict[str, "StateInfo"]] = self._identify_changed_variables(
            current_state, previous_state
        )

        if changed_variables:

            # Apply widening to each changed variable
            widened_state = current_state.deep_copy()
            for var_name, var_data in changed_variables.items():
                current_var: StateInfo = var_data["current"]
                previous_var: StateInfo = var_data["previous"]

                # Apply widening to this variable
                widened_var: StateInfo = self._apply_widening_to_variable(
                    current_var, previous_var, set_b
                )
                widened_state.state.info[var_name] = widened_var

                # Clear valid values for all changed variables since we're applying widening
                widened_state.state.info[var_name].valid_values.clear()

                # Mark this variable as widened to prevent future discrete value assignments
                self._widened_variables.add(var_name)

        else:

            widened_state = current_state

        return widened_state

    def _identify_changed_variables(
        self, current_state: IntervalDomain, previous_state: IntervalDomain
    ) -> Dict[str, Dict[str, "StateInfo"]]:
        """Identify variables that have different values between current and previous states."""
        changed_vars: Dict[str, Dict[str, "StateInfo"]] = {}

        # Check if both states have state info
        if not hasattr(current_state, "state") or not hasattr(previous_state, "state"):
            return changed_vars

        current_info = current_state.state.info
        previous_info = previous_state.state.info

        # Check variables present in both states
        common_vars = set(current_info.keys()) & set(previous_info.keys())

        for var_name in common_vars:
            current_var: StateInfo = current_info[var_name]
            previous_var: StateInfo = previous_info[var_name]

            if current_var != previous_var:
                changed_vars[var_name] = {"current": current_var, "previous": previous_var}

        return changed_vars

    def _apply_widening_to_variable(
        self, current_var: StateInfo, previous_var: StateInfo, set_b: Set[int]
    ) -> StateInfo:
        """Apply widening operator ∇' to a single variable based on the widening rules."""
        # Create a copy of the current variable to modify
        widened_var: StateInfo = current_var.deep_copy()

        # Convert discrete values to ranges for widening
        current_ranges: List[IntervalRange] = self._get_ranges_for_widening(current_var)
        previous_ranges: List[IntervalRange] = self._get_ranges_for_widening(previous_var)

        # Apply widening to ranges
        if current_ranges and previous_ranges:
            # For simplicity, apply widening to the first range of each variable
            if len(current_ranges) > 0 and len(previous_ranges) > 0:
                current_range: IntervalRange = current_ranges[0]
                previous_range: IntervalRange = previous_ranges[0]

                # Apply widening rules to the interval
                widened_lower: Decimal = self._widen_lower_bound(
                    previous_range.get_lower(),
                    current_range.get_lower(),
                    set_b,
                    current_var.var_type,
                )
                widened_upper: Decimal = self._widen_upper_bound(
                    previous_range.get_upper(),
                    current_range.get_upper(),
                    set_b,
                    current_var.var_type,
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
        return widened_var

    def _get_ranges_for_widening(self, var: StateInfo) -> List[IntervalRange]:
        """Get interval ranges for widening, converting from discrete values if needed."""
        # If variable already has interval ranges, use them
        if var.interval_ranges:
            return var.interval_ranges

        # If variable has discrete values, convert them to ranges
        if var.valid_values and len(var.valid_values) > 0:
            values = sorted(var.valid_values.get())
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
        set_b: Set[int],
        var_type: Optional[ElementaryType] = None,
    ) -> Decimal:
        """Apply lower bound widening rule."""
        # If l₁ ≤ l₂ (lower bound is stable/non-decreasing): keep l₃ = l₁
        if prev_lower <= curr_lower:
            logger.info(f"🔄 Lower bound stable: {prev_lower} ≤ {curr_lower}, keeping {prev_lower}")
            return prev_lower
        # If l₁ > l₂ (lower bound is unstable/decreasing): widen to l₃ = max{i ∈ B | i ≤ l₂}
        else:
            logger.info(
                f"🔄 Lower bound unstable: {prev_lower} > {curr_lower}, looking for candidates in set B: {set_b}"
            )
            # Find the maximum value in set B that is less than or equal to curr_lower
            candidates = [i for i in set_b if i <= curr_lower]
            if candidates:
                result = max(candidates)
                return result
            else:
                # If no suitable value found, use the variable's type minimum
                if var_type and hasattr(var_type, "min"):
                    result = Decimal(str(var_type.min))
                    return result
                else:
                    result = Decimal("0")  # Default for uint types
                    return result

    def _widen_upper_bound(
        self,
        prev_upper: Decimal,
        curr_upper: Decimal,
        set_b: Set[int],
        var_type: Optional[ElementaryType] = None,
    ) -> Decimal:
        """Apply upper bound widening rule."""
        # If h₂ ≤ h₁ (upper bound is stable/non-increasing): keep h₃ = h₁
        if curr_upper <= prev_upper:
            logger.info(f"🔄 Upper bound stable: {curr_upper} ≤ {prev_upper}, keeping {prev_upper}")
            return prev_upper
        # If h₂ > h₁ (upper bound is unstable/increasing): widen to h₃ = min{i ∈ B | h₂ ≤ i}
        else:
            logger.info(
                f"🔄 Upper bound unstable: {curr_upper} > {prev_upper}, looking for candidates in set B: {set_b}"
            )
            # Find the minimum value in set B that is greater than or equal to curr_upper
            candidates = [i for i in set_b if i >= curr_upper]
            if candidates:
                result = min(candidates)
                logger.info(f"🔄 Found candidate in set B: {result}")
                return result
            else:
                # If no suitable value found, use the variable's type maximum
                if var_type and hasattr(var_type, "max"):
                    result = Decimal(str(var_type.max))
                    logger.info(f"🔄 No candidates in set B, using type max: {result}")
                    return result
                else:
                    result = Decimal(
                        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                    )  # uint256 max
                    logger.info(f"🔄 No candidates in set B, using default max: {result}")
                    return result

    def is_variable_widened(self, var_name: str) -> bool:
        """Check if a variable has been widened and should not receive discrete values."""
        return var_name in self._widened_variables

    def prevent_discrete_assignment(self, var_name: str, state_info: StateInfo) -> None:
        """Prevent discrete value assignments to widened variables."""
        if self.is_variable_widened(var_name):
            # Clear any discrete values that might have been added
            state_info.valid_values.clear()
            logger.debug(f"🔄 Prevented discrete assignment to widened variable: {var_name}")
