from decimal import Decimal
from typing import List

from slither.analyses.data_flow.interval_enhanced.core.interval_range import IntervalRange
from slither.analyses.data_flow.interval_enhanced.core.single_values import SingleValues
from slither.core.solidity_types.elementary_type import ElementaryType


class StateInfo:
    def __init__(
        self,
        interval_ranges: List[IntervalRange],
        valid_values: SingleValues,
        invalid_values: SingleValues,
        var_type: ElementaryType,
    ):
        """Initialize StateInfo with interval ranges, valid/invalid values, and variable type"""
        self.interval_ranges = interval_ranges if interval_ranges else []
        self.valid_values = valid_values if valid_values else SingleValues()
        self.invalid_values = invalid_values if invalid_values else SingleValues()
        self.var_type = var_type

    def add_interval_range(self, interval_range: IntervalRange) -> None:
        """Add an interval range to the state"""
        self.interval_ranges.append(interval_range)

    def remove_interval_range(self, interval_range: IntervalRange) -> bool:
        """Remove an interval range from the state, returns True if found and removed"""
        if interval_range in self.interval_ranges:
            self.interval_ranges.remove(interval_range)
            return True
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

    def get_type_bounds(self) -> tuple[Decimal, Decimal]:
        """Get the theoretical min/max bounds for this variable's type"""
        if self.var_type and hasattr(self.var_type, "max") and hasattr(self.var_type, "min"):
            return Decimal(str(self.var_type.min)), Decimal(str(self.var_type.max))
        else:
            # Default to uint256 bounds for temporary variables or unknown types
            return Decimal("0"), Decimal(
                "115792089237316195423570985008687907853269984665640564039457584007913129639935"
            )

    def join(self, other: "StateInfo") -> None:
        """Join this StateInfo with another StateInfo"""
        # Join interval ranges - merge all ranges from both states
        for other_range in other.interval_ranges:
            found_overlap = False
            for self_range in self.interval_ranges:
                # Check if ranges can be merged (overlapping or adjacent)
                if (
                    self_range.get_lower() <= other_range.get_upper()
                    and self_range.get_upper() >= other_range.get_lower()
                ):
                    self_range.join(other_range)
                    found_overlap = True
                    break
            if not found_overlap:
                self.interval_ranges.append(other_range.deep_copy())

        # Join valid values
        self.valid_values = self.valid_values.join(other.valid_values)

        # Join invalid values
        self.invalid_values = self.invalid_values.join(other.invalid_values)

    def deep_copy(self) -> "StateInfo":
        """Create a deep copy of the StateInfo"""
        copied_ranges = [interval_range.deep_copy() for interval_range in self.interval_ranges]
        copied_valid = self.valid_values.deep_copy()
        copied_invalid = self.invalid_values.deep_copy()

        return StateInfo(
            interval_ranges=copied_ranges,
            valid_values=copied_valid,
            invalid_values=copied_invalid,
            var_type=self.var_type,
        )

    def has_overflow(self) -> bool:
        """Check if any values exceed the variable's type bounds"""
        _, type_max = self.get_type_bounds()

        # Check interval ranges
        for interval_range in self.interval_ranges:
            if interval_range.get_upper() > type_max:
                return True

        # Check valid values
        for value in self.valid_values:
            if value > type_max:
                return True

        # Check invalid values
        for value in self.invalid_values:
            if value > type_max:
                return True

        return False

    def has_underflow(self) -> bool:
        """Check if any values go below the variable's type bounds"""
        type_min, _ = self.get_type_bounds()

        # Check interval ranges
        for interval_range in self.interval_ranges:
            if interval_range.get_lower() < type_min:
                return True

        # Check valid values
        for value in self.valid_values:
            if value < type_min:
                return True

        # Check invalid values
        for value in self.invalid_values:
            if value < type_min:
                return True

        return False

    def __eq__(self, other):
        """Check equality with another StateInfo"""
        if not isinstance(other, StateInfo):
            return False
        return (
            self.interval_ranges == other.interval_ranges
            and self.valid_values == other.valid_values
            and self.invalid_values == other.invalid_values
            and self.var_type == other.var_type
        )

    def __hash__(self):
        """Hash function for StateInfo"""
        return hash(
            (tuple(self.interval_ranges), self.valid_values, self.invalid_values, self.var_type)
        )
