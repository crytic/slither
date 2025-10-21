from decimal import Decimal, getcontext
from typing import Optional, Union, List

from loguru import logger

from slither.slithir.operations.binary import BinaryType

# Set high precision for Decimal operations
getcontext().prec = 100


class IntervalRange:
    """Represents a closed interval [lower_bound, upper_bound] with high-precision decimal arithmetic."""

    # Class-level configuration for power operation limits
    MAX_POWER_VALUE = Decimal(2) ** 256 - 1  # Default to 256-bit max

    def __init__(self, lower_bound: Union[int, Decimal], upper_bound: Union[int, Decimal]):
        self.lower_bound = Decimal(str(lower_bound))
        self.upper_bound = Decimal(str(upper_bound))

    def __eq__(self, other):
        return self.upper_bound == other.upper_bound and self.lower_bound == other.lower_bound

    def __hash__(self):
        return hash((self.upper_bound, self.lower_bound))

    def __str__(self):
        return f"[{self.lower_bound}, {self.upper_bound}]"

    def get_lower(self) -> Decimal:
        return self.lower_bound

    def get_upper(self) -> Decimal:
        return self.upper_bound

    def set_lower(self, value: Union[int, Decimal]) -> None:
        self.lower_bound = Decimal(str(value))

    def set_upper(self, value: Union[int, Decimal]) -> None:
        self.upper_bound = Decimal(str(value))

    def copy(self) -> "IntervalRange":
        return IntervalRange(self.lower_bound, self.upper_bound)

    def deep_copy(self) -> "IntervalRange":
        """Create a deep copy of this IntervalRange."""
        return IntervalRange(self.lower_bound, self.upper_bound)

    def join(self, other: "IntervalRange") -> None:
        self.lower_bound = min(self.lower_bound, other.lower_bound)
        self.upper_bound = max(self.upper_bound, other.upper_bound)

    def union(self, other: "IntervalRange") -> "IntervalRange":
        return IntervalRange(
            min(self.lower_bound, other.lower_bound), max(self.upper_bound, other.upper_bound)
        )

    def intersection(self, other: "IntervalRange") -> Optional["IntervalRange"]:
        new_lower = max(self.lower_bound, other.lower_bound)
        new_upper = min(self.upper_bound, other.upper_bound)

        if new_lower <= new_upper:
            return IntervalRange(new_lower, new_upper)
        return None

    def contains(self, value: Union[int, Decimal]) -> bool:
        value = Decimal(str(value))
        return self.lower_bound <= value <= self.upper_bound

    @classmethod
    def set_max_power_value(cls, max_value: Union[int, Decimal]) -> None:
        """Set the maximum value for power operations."""
        cls.MAX_POWER_VALUE = Decimal(str(max_value))

    @staticmethod
    def _safe_power(base: Decimal, exponent: int) -> Decimal:
        """
        Compute base^exponent with early termination if result exceeds MAX_POWER_VALUE.
        Returns the first value that goes over the threshold.
        Uses binary exponentiation for O(log n) performance.
        """
        max_value = IntervalRange.MAX_POWER_VALUE

        if exponent < 0:
            if base == 0:
                raise ZeroDivisionError(f"Cannot compute 0^{exponent}")
            # Negative exponents result in fractions, will be 0 after to_integral_value
            return Decimal(0) if abs(base) > 1 else max_value

        if exponent == 0:
            return Decimal(1)

        if base == 0:
            return Decimal(0)

        if base == 1:
            return Decimal(1)

        if base == -1:
            return Decimal(1) if exponent % 2 == 0 else Decimal(-1)

        # Binary exponentiation with overflow check
        result = Decimal(1)
        current_base = Decimal(int(base))
        current_exp = exponent

        while current_exp > 0:
            if current_exp % 2 == 1:
                result *= current_base
                if abs(result) > max_value:
                    # Return the actual value that exceeded threshold
                    return result

            current_exp //= 2
            if current_exp > 0:
                current_base *= current_base
                if abs(current_base) > max_value:
                    # Base squared exceeded threshold, compute what the result would be
                    # We need to continue with the overflowed base to get the final result
                    return result * current_base

        return result

    @staticmethod
    def compute_arithmetic_interval(
        left: "IntervalRange", right: "IntervalRange", operation: BinaryType
    ) -> "IntervalRange":
        """Compute the resulting interval from applying an arithmetic operation between two IntervalRanges."""

        left_lower, left_upper = left.lower_bound, left.upper_bound
        right_lower, right_upper = right.lower_bound, right.upper_bound

        # Calculate all 4 combinations of interval bounds
        try:
            result_ll = IntervalRange._apply_scalar_op(left_lower, right_lower, operation)
            result_lu = IntervalRange._apply_scalar_op(left_lower, right_upper, operation)
            result_ul = IntervalRange._apply_scalar_op(left_upper, right_lower, operation)
            result_uu = IntervalRange._apply_scalar_op(left_upper, right_upper, operation)
        except ZeroDivisionError as e:
            logger.error(f"Division by zero in interval arithmetic: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in interval arithmetic: {e}")
            raise

        return IntervalRange(
            lower_bound=min(result_ll, result_lu, result_ul, result_uu),
            upper_bound=max(result_ll, result_lu, result_ul, result_uu),
        )

    @staticmethod
    def _apply_scalar_op(left: Decimal, right: Decimal, operation: BinaryType) -> Decimal:
        """Apply a binary arithmetic operation to two scalar Decimal values."""
        if operation == BinaryType.ADDITION:
            return (left + right).to_integral_value()
        elif operation == BinaryType.SUBTRACTION:
            return (left - right).to_integral_value()
        elif operation == BinaryType.MULTIPLICATION:
            return (left * right).to_integral_value()
        elif operation == BinaryType.DIVISION:
            # Check for division by zero before performing operation
            if right == 0:
                raise ZeroDivisionError(f"Division by zero: {left} / {right}")
            return (left / right).to_integral_value()
        elif operation == BinaryType.LEFT_SHIFT:
            # x << y is equivalent to x * 2**y
            return (left * (Decimal(2) ** right)).to_integral_value()
        elif operation == BinaryType.RIGHT_SHIFT:
            # x >> y is equivalent to x / 2**y, rounded towards negative infinity
            if right < 0:
                raise ValueError(f"Right shift by negative amount: {right}")
            return (left / (Decimal(2) ** right)).to_integral_value()
        elif operation == BinaryType.AND:
            # Bitwise AND: x & y
            return Decimal(int(left) & int(right))
        elif operation == BinaryType.OR:
            # Bitwise OR: x | y
            return Decimal(int(left) | int(right))
        elif operation == BinaryType.CARET:
            # Bitwise XOR: x ^ y
            return Decimal(int(left) ^ int(right))
        elif operation == BinaryType.MODULO:
            # Modulo: x % y
            if right == 0:
                raise ZeroDivisionError(f"Modulo by zero: {left} % {right}")
            return Decimal(int(left) % int(right))
        elif operation == BinaryType.POWER:
            # Exponentiation: x ** y with overflow protection
            return IntervalRange._safe_power(left, int(right))
        else:
            raise ValueError(f"Unsupported operation: {operation}")

    @staticmethod
    def compute_list_intersection(
        target_ranges: List["IntervalRange"], ref_ranges: List["IntervalRange"]
    ) -> List["IntervalRange"]:
        """Compute the intersection of two lists of interval ranges."""
        intersected_ranges: List["IntervalRange"] = []

        for target_range in target_ranges:
            for ref_range in ref_ranges:
                # Calculate intersection of two ranges
                lower_bound = max(target_range.get_lower(), ref_range.get_lower())
                upper_bound = min(target_range.get_upper(), ref_range.get_upper())

                # Only add if intersection is valid (lower <= upper)
                if lower_bound <= upper_bound:
                    intersected_range = IntervalRange(lower_bound, upper_bound)
                    intersected_ranges.append(intersected_range)

        return intersected_ranges
