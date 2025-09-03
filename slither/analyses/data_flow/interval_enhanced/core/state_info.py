from decimal import Decimal
from typing import List, Tuple, Iterator, Optional

from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues

from slither.core.solidity_types.elementary_type import ElementaryType
from loguru import logger


class StateInfo:
    """Represents state information with interval ranges, valid/invalid values, and variable type."""

    # Default bounds for uint256
    DEFAULT_MIN = Decimal("0")
    DEFAULT_MAX = Decimal(
        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
    )

    def __init__(
        self,
        interval_ranges: List[IntervalRange] = None,
        valid_values: SingleValues = None,
        invalid_values: SingleValues = None,
        var_type: ElementaryType = None,
    ):
        """Initialize StateInfo with interval ranges, valid/invalid values, and variable type"""
        self.interval_ranges = interval_ranges or []
        self.valid_values = valid_values or SingleValues()
        self.invalid_values = invalid_values or SingleValues()
        self.var_type = var_type

    def add_interval_range(self, interval_range: IntervalRange) -> None:
        """Add an interval range to the state"""
        self.interval_ranges.append(interval_range)

    def remove_interval_range(self, interval_range: IntervalRange) -> bool:
        """Remove an interval range from the state, returns True if found and removed"""
        try:
            self.interval_ranges.remove(interval_range)
            return True
        except ValueError:
            return False

    def get_interval_ranges(self) -> List[IntervalRange]:
        """Get a copy of the interval ranges list"""
        return self.interval_ranges.copy()

    def get_valid_values(self) -> SingleValues:
        """Get the valid values"""
        return self.valid_values

    def get_invalid_values(self) -> SingleValues:
        """Get the invalid values"""
        return self.invalid_values

    def get_var_type(self) -> ElementaryType:
        """Get the variable type"""
        return self.var_type

    def get_type_bounds(self) -> Tuple[Decimal, Decimal]:
        """Get the theoretical min/max bounds for this variable's type"""
        if self.var_type and hasattr(self.var_type, "max") and hasattr(self.var_type, "min"):
            return Decimal(str(self.var_type.min)), Decimal(str(self.var_type.max))
        return self.DEFAULT_MIN, self.DEFAULT_MAX

    def _check_bounds_violation(self, bound_value: Decimal, comparison_func) -> bool:
        """Helper method to check if any values violate bounds using the given comparison function"""
        # Check interval ranges
        for interval_range in self.interval_ranges:
            range_value = (
                interval_range.get_upper()
                if comparison_func.__name__ == "gt"
                else interval_range.get_lower()
            )
            if comparison_func(range_value, bound_value):
                return True

        # Check both valid and invalid values
        for values_collection in [self.valid_values, self.invalid_values]:
            for value in values_collection:
                if comparison_func(value, bound_value):
                    return True

        return False

    def has_overflow(self) -> bool:
        """Check if any values exceed the variable's type bounds"""
        _, type_max = self.get_type_bounds()
        return self._check_bounds_violation(type_max, lambda x, y: x > y)

    def has_underflow(self) -> bool:
        """Check if any values go below the variable's type bounds"""
        type_min, _ = self.get_type_bounds()
        return self._check_bounds_violation(type_min, lambda x, y: x < y)

    def clear_intervals(self) -> None:
        """Clear the intervals"""
        self.interval_ranges.clear()

    def join(self, other: "StateInfo") -> None:
        """Join this StateInfo with another StateInfo"""
        # Join valid and invalid values
        self.valid_values = self.valid_values.join(other.valid_values)
        self.invalid_values = self.invalid_values.join(other.invalid_values)

        # Remove any valid values that are also in invalid values
        for invalid_value in self.invalid_values:
            self.valid_values.delete(invalid_value)

        # Merge ranges from both states
        self.interval_ranges.extend(range_obj.deep_copy() for range_obj in other.interval_ranges)
        # Deep copy existing ranges to maintain consistency
        self.interval_ranges = [range_obj.deep_copy() for range_obj in self.interval_ranges]

    def deep_copy(self) -> "StateInfo":
        """Create a deep copy of the StateInfo"""
        return StateInfo(
            interval_ranges=[interval_range.deep_copy() for interval_range in self.interval_ranges],
            valid_values=self.valid_values.deep_copy(),
            invalid_values=self.invalid_values.deep_copy(),
            var_type=self.var_type,
        )

    def optimize(self) -> "StateInfo":
        """Optimize by consolidating ranges and converting consecutive values to ranges."""
        result = self.deep_copy()

        # Merge overlapping ranges
        if len(result.interval_ranges) > 1:
            result.interval_ranges = self._merge_ranges(result.interval_ranges)

        # Convert consecutive valid values to ranges
        if result.valid_values and len(result.valid_values) >= 2:
            result = self._convert_consecutive_to_ranges(result)

        return result

    def _merge_ranges(self, ranges: List[IntervalRange]) -> List[IntervalRange]:
        """Merge overlapping/adjacent ranges."""
        if not ranges:
            return []

        sorted_ranges = sorted(ranges, key=lambda r: r.get_lower())
        merged = [sorted_ranges[0].deep_copy()]

        for current_range in sorted_ranges[1:]:
            last_merged = merged[-1]
            if last_merged.get_upper() >= current_range.get_lower() - 1:
                last_merged.join(current_range)
            else:
                merged.append(current_range.deep_copy())

        return merged

    def _convert_consecutive_to_ranges(self, state: "StateInfo") -> "StateInfo":
        """Convert consecutive valid values to ranges."""
        values = sorted(state.valid_values.get())
        result = state.deep_copy()

        i = 0
        while i < len(values) - 1:
            start_idx = i
            # Find consecutive sequence
            while i < len(values) - 1 and values[i + 1] == values[i] + 1:
                i += 1

            # Convert sequence to range if found
            if i > start_idx:
                result.add_interval_range(
                    IntervalRange(lower_bound=values[start_idx], upper_bound=values[i])
                )
                # Remove converted values
                for val_idx in range(start_idx, i + 1):
                    result.valid_values.delete(values[val_idx])
            i += 1

        # Re-merge ranges if needed
        if len(result.interval_ranges) > 1:
            result.interval_ranges = self._merge_ranges(result.interval_ranges)

        return result

    def _format_collection(self, collection, name: str) -> str:
        """Helper method to format collections for string representation"""
        if collection:
            if hasattr(collection, "__iter__") and not isinstance(collection, str):
                items_str = ", ".join(str(item) for item in collection)
            else:
                items_str = str(collection)
            return f"{name}:[{items_str}]"
        return f"{name}:[]"

    def __str__(self) -> str:
        """String representation of StateInfo for debugging"""
        try:
            type_name = (
                self.var_type.name
                if self.var_type
                and hasattr(self.var_type, "name")
                and self.var_type.name is not None
                else "unknown"
            )
        except Exception:
            type_name = "unknown"

        parts = [
            f"type:{type_name}",
            self._format_collection(self.interval_ranges, "ranges"),
            self._format_collection(self.valid_values, "valid"),
            self._format_collection(self.invalid_values, "invalid"),
        ]

        return f"StateInfo({', '.join(parts)})"

    def __eq__(self, other) -> bool:
        """Check equality with another StateInfo"""
        if not isinstance(other, StateInfo):
            return False
        return (
            self.interval_ranges == other.interval_ranges
            and self.valid_values == other.valid_values
            and self.invalid_values == other.invalid_values
            and self.var_type == other.var_type
        )

    def __hash__(self) -> int:
        """Hash function for StateInfo"""
        return hash(
            (tuple(self.interval_ranges), self.valid_values, self.invalid_values, self.var_type)
        )
