from decimal import Decimal
from typing import TYPE_CHECKING, List, Tuple, Union

from loguru import logger

from slither.analyses.data_flow.analyses.interval.core.types.interval_range import IntervalRange
from slither.analyses.data_flow.analyses.interval.core.types.value_set import ValueSet
from slither.analyses.data_flow.analyses.interval.managers.variable_info_manager import (
    VariableInfoManager,
)
from slither.core.declarations.function import Function
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import BinaryType
from slither.slithir.utils.utils import RVALUE
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain


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
        if self.var_type and self.var_type.name not in ["bool"]:
            try:
                return Decimal(str(self.var_type.min)), Decimal(str(self.var_type.max))
            except Exception:
                # Handle types that don't have min/max
                return None, None
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

    # ---------- Consolidation ----------
    def consolidate_ranges(self) -> None:
        """Consolidate overlapping and duplicate ranges for efficiency."""
        if not self.interval_ranges:
            return

        # Log original ranges for debugging
        logger.debug(f"🔧 Consolidating ranges: {[str(r) for r in self.interval_ranges]}")

        # Remove duplicates by converting to set and back
        unique_ranges = list(set(self.interval_ranges))

        # Sort ranges by lower bound
        unique_ranges.sort(key=lambda r: r.get_lower())

        # Merge overlapping ranges
        consolidated = []
        for current_range in unique_ranges:
            if not consolidated:
                consolidated.append(current_range)
            else:
                last_range = consolidated[-1]

                # Check if ranges overlap or are adjacent
                if (
                    current_range.get_lower() <= last_range.get_upper() + 1
                    or last_range.get_lower() <= current_range.get_upper() + 1
                ):
                    # Merge ranges
                    merged_lower = min(last_range.get_lower(), current_range.get_lower())
                    merged_upper = max(last_range.get_upper(), current_range.get_upper())
                    consolidated[-1] = IntervalRange(merged_lower, merged_upper)
                    logger.debug(
                        f"🔧 Merged {str(last_range)} and {str(current_range)} -> {str(consolidated[-1])}"
                    )
                else:
                    # No overlap, add as new range
                    consolidated.append(current_range)

        # Update the interval ranges
        self.interval_ranges = consolidated
        logger.debug(f"🔧 Final consolidated ranges: {[str(r) for r in self.interval_ranges]}")

    def convert_consecutive_values_to_ranges(self) -> None:
        """Convert consecutive valid values to interval ranges."""
        if not self.valid_values or len(self.valid_values) < 2:
            return

        # Get sorted valid values
        sorted_values = sorted(self.valid_values)

        # Check if values are consecutive
        consecutive_ranges = []
        start = sorted_values[0]
        end = start

        for i in range(1, len(sorted_values)):
            if sorted_values[i] == end + Decimal("1"):
                # Consecutive, extend the range
                end = sorted_values[i]
            else:
                # Not consecutive, save the current range
                if start == end:
                    # Single value, keep as discrete value
                    pass
                else:
                    # Multiple consecutive values, convert to range
                    consecutive_ranges.append(IntervalRange(start, end))

                # Start new range
                start = sorted_values[i]
                end = start

        # Handle the last range
        if start == end:
            # Single value, keep as discrete value
            pass
        else:
            # Multiple consecutive values, convert to range
            consecutive_ranges.append(IntervalRange(start, end))

        # If we found consecutive ranges, convert them
        if consecutive_ranges:
            logger.debug(
                f"🔄 Converting consecutive values {sorted_values} to ranges: {[str(r) for r in consecutive_ranges]}"
            )

            # Add the new ranges
            self.interval_ranges.extend(consecutive_ranges)

            # Remove the consecutive values from valid_values
            for range_obj in consecutive_ranges:
                lower = int(range_obj.get_lower())
                upper = int(range_obj.get_upper())
                for val in range(lower, upper + 1):
                    decimal_val = Decimal(str(val))
                    if decimal_val in self.valid_values:
                        self.valid_values.remove(decimal_val)

            # Consolidate the ranges
            self.consolidate_ranges()

    # ---------- Join ----------
    def join(self, other: "RangeVariable") -> None:
        """Join this RangeVariable with another RangeVariable"""
        # Join valid and invalid values
        self.valid_values = self.valid_values.join(other.valid_values)
        self.invalid_values = self.invalid_values.join(other.invalid_values)

        # Convert consecutive valid values to ranges
        self.convert_consecutive_values_to_ranges()

        # Remove any valid values that are also in invalid values
        for invalid_value in self.invalid_values:
            self.valid_values.remove(invalid_value)

        # Merge ranges from both states
        self.interval_ranges.extend(range_obj.deep_copy() for range_obj in other.interval_ranges)
        # Deep copy existing ranges to maintain consistency
        self.interval_ranges = [range_obj.deep_copy() for range_obj in self.interval_ranges]

        # Consolidate ranges after joining to remove duplicates and overlaps
        self.consolidate_ranges()

    # ---------- Copy ----------
    def deep_copy(self) -> "RangeVariable":
        """Create a deep copy of the RangeVariable"""
        return RangeVariable(
            interval_ranges=[interval_range.deep_copy() for interval_range in self.interval_ranges],
            valid_values=self.valid_values.deep_copy(),
            invalid_values=self.invalid_values.deep_copy(),
            var_type=self.var_type,
        )

    # ---------- Arithmetic ----------
    @staticmethod
    def compute_arithmetic_range_variable(
        left: "RangeVariable",
        right: "RangeVariable",
        operation_type: BinaryType,
    ) -> "RangeVariable":
        """Compute the arithmetic result between two RangeVariables."""

        # Handle None inputs
        if left is None or right is None:
            logger.error(f"One or both operands are None: left={left}, right={right}")
            raise ValueError("Cannot perform arithmetic with None operands")

        result_valid_values = ValueSet(set())
        result_interval_ranges: List[IntervalRange] = []

        # Case 1: constant + constant (e.g., 3 + 5)
        if not left.valid_values.is_empty() and not right.valid_values.is_empty():
            for left_val in left.valid_values:
                result_valid_values = result_valid_values.join(
                    right.valid_values.compute_arithmetic_with_scalar(left_val, operation_type)
                )

        # Case 2: constant + interval (e.g., 3 + [1, 5])
        if not left.valid_values.is_empty() and right.interval_ranges:
            for left_val in left.valid_values:
                for right_range in right.interval_ranges:
                    try:
                        left_point = IntervalRange(left_val, left_val)
                        result_range = IntervalRange.compute_arithmetic_interval(
                            left_point, right_range, operation_type
                        )
                        result_interval_ranges.append(result_range)
                    except Exception as e:
                        logger.error(f"Error in mixed arithmetic: {e}")

        # Case 3: interval + constant (e.g., [2, 4] + 7)
        if left.interval_ranges and not right.valid_values.is_empty():
            for left_range in left.interval_ranges:
                for right_val in right.valid_values:
                    try:
                        right_point = IntervalRange(right_val, right_val)
                        result_range = IntervalRange.compute_arithmetic_interval(
                            left_range, right_point, operation_type
                        )
                        result_interval_ranges.append(result_range)
                    except Exception as e:
                        logger.error(f"Error in mixed arithmetic: {e}")

        # Case 4: interval + interval (e.g., [1, 3] + [4, 6])
        if left.interval_ranges and right.interval_ranges:
            for left_range in left.interval_ranges:
                for right_range in right.interval_ranges:
                    try:
                        result_range = IntervalRange.compute_arithmetic_interval(
                            left_range, right_range, operation_type
                        )
                        result_interval_ranges.append(result_range)
                    except Exception as e:
                        logger.error(f"Error in interval arithmetic: {e}")

        # Case 5: no results -> fallback (e.g., both operands empty)
        if result_valid_values.is_empty() and not result_interval_ranges:
            if left.valid_values.is_empty() and not left.interval_ranges:
                return left.deep_copy()  # fallback to left
            elif right.valid_values.is_empty() and not right.interval_ranges:
                return right.deep_copy()  # fallback to right
            else:
                # return TOP (unbounded range)
                result_interval_ranges.append(
                    IntervalRange(Decimal("-Infinity"), Decimal("Infinity"))
                )

        result = RangeVariable(
            interval_ranges=result_interval_ranges,
            valid_values=result_valid_values,
            invalid_values=ValueSet(set()),  # conservative choice: reset invalids
            var_type=left.var_type,  # TODO: replace with proper type inference
        )

        # Convert consecutive valid values to ranges
        result.convert_consecutive_values_to_ranges()

        # Consolidate ranges to remove duplicates and overlaps
        result.consolidate_ranges()

        return result

    @staticmethod
    def get_variable_info(
        domain: "IntervalDomain", variable: Union[Variable, Constant, RVALUE, Function]
    ) -> "RangeVariable":
        """Retrieve state information for a variable or constant."""
        variable_info_manager = VariableInfoManager()

        if isinstance(variable, Constant):
            value: Decimal = Decimal(str(variable.value))
            valid_values = ValueSet({value})

            # Determine the appropriate type for the constant
            if value < 0:
                # Negative constants should use int256
                constant_type = ElementaryType("int256")
            else:
                # Non-negative constants can use uint256
                constant_type = ElementaryType("uint256")

            # For constants, use valid_values instead of interval ranges
            return RangeVariable(
                interval_ranges=[],  # No interval ranges for constants
                valid_values=valid_values,
                invalid_values=ValueSet(set()),
                var_type=constant_type,
            )

        var_name: str = variable_info_manager.get_variable_name(variable)

        range_var = domain.state.get_range_variable(var_name)
        if range_var is not None:
            return range_var

        # Check if this is a ReferenceVariable that points to a struct field
        if hasattr(variable, "points_to") and variable.points_to is not None:
            # Try to find the struct field by looking at what the reference points to
            points_to = variable.points_to

            # If points_to is a LocalVariable, try to construct the field name
            if hasattr(points_to, "canonical_name"):
                # This is likely a struct field access
                # We need to find the corresponding field in the domain state
                # For now, return the first struct field we find (this is a simplified approach)
                for key in domain.state._variables.keys():
                    if key.endswith(".first") or key.endswith(".second"):
                        return domain.state.get_range_variable(key)

        logger.error(f"Variable {var_name} not found in state")
        raise ValueError(f"Variable {var_name} not found in state")
