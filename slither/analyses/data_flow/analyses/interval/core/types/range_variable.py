from decimal import Decimal
from typing import Callable, List, Tuple

from loguru import logger

from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.core.solidity_types.elementary_type import ElementaryType


class RangeVariable:
    """Represents a variable for range analysis with intervals, discrete values, and type."""

    def __init__(
        self,
        interval_ranges: List[IntervalRange] = None,
        valid_values: ValueSet = None,
        invalid_values: ValueSet = None,
        var_type: ElementaryType = None,
    ):
        self.interval_ranges = interval_ranges or []
        self.valid_values = valid_values or ValueSet(set())
        self.invalid_values = invalid_values or ValueSet(set())
        self.var_type = var_type

    # ---------- Getters ----------
    def get_interval_ranges(self) -> List[IntervalRange]:
        return self.interval_ranges.copy()

    def get_valid_values(self) -> ValueSet:
        return self.valid_values

    def get_invalid_values(self) -> ValueSet:
        return self.invalid_values

    def get_var_type(self) -> ElementaryType:
        return self.var_type

    def get_type_bounds(self) -> Tuple[Decimal, Decimal]:
        if self.var_type and hasattr(self.var_type, "min") and hasattr(self.var_type, "max"):
            return Decimal(str(self.var_type.min)), Decimal(str(self.var_type.max))
        return None, None

    # ---------- Adders ----------
    def add_interval_range(self, interval_range: IntervalRange) -> None:
        self.interval_ranges.append(interval_range)

    def add_valid_value(self, value: Decimal) -> None:
        self.valid_values.add(value)

    def add_invalid_value(self, value: Decimal) -> None:
        self.invalid_values.add(value)

    # ---------- Overflow/Underflow checkers ----------
    def _check_bounds_violation(self, bound_value: Decimal, check_upper: bool) -> bool:
        """Check if any interval or value violates the bound."""
        # Check interval ranges
        for interval_range in self.interval_ranges:
            if check_upper:
                value = interval_range.get_upper()
                if value > bound_value:
                    return True
            else:
                value = interval_range.get_lower()
                if value < bound_value:
                    return True

        # Check discrete values
        for values_collection in [self.valid_values, self.invalid_values]:
            for value in values_collection:
                if check_upper:
                    if value > bound_value:
                        return True
                else:
                    if value < bound_value:
                        return True

        return False

    def has_overflow(self) -> bool:
        """Check if any value exceeds the maximum type bound."""
        _, type_max = self.get_type_bounds()
        if type_max is None:
            return False
        return self._check_bounds_violation(type_max, check_upper=True)

    def has_underflow(self) -> bool:
        """Check if any value is below the minimum type bound."""
        type_min, _ = self.get_type_bounds()
        if type_min is None:
            return False
        return self._check_bounds_violation(type_min, check_upper=False)

    # ---------- Clear ----------
    def clear_intervals(self) -> None:
        self.interval_ranges.clear()

    def clear_valid_values(self) -> None:
        self.valid_values = ValueSet(set())

    def clear_invalid_values(self) -> None:
        self.invalid_values = ValueSet(set())

    # ---------- Join ----------
    def join(self, other: "RangeVariable") -> None:
        """Join this RangeVariable with another RangeVariable"""
        # Join valid and invalid values
        self.valid_values = self.valid_values.join(other.valid_values)
        self.invalid_values = self.invalid_values.join(other.invalid_values)

        # Remove any valid values that are also in invalid values
        for invalid_value in self.invalid_values:
            self.valid_values.remove(invalid_value)

        # Merge ranges from both states
        self.interval_ranges.extend(range_obj.copy() for range_obj in other.interval_ranges)
        # Deep copy existing ranges to maintain consistency
        self.interval_ranges = [range_obj.copy() for range_obj in self.interval_ranges]

    # ---------- Copy ----------
    def deep_copy(self) -> "RangeVariable":
        """Create a deep copy of the RangeVariable"""
        return RangeVariable(
            interval_ranges=[interval_range.deep_copy() for interval_range in self.interval_ranges],
            valid_values=self.valid_values.deep_copy(),
            invalid_values=self.invalid_values.deep_copy(),
            var_type=self.var_type,
        )
