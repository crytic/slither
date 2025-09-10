from decimal import Decimal, getcontext
from typing import Optional, Union

from loguru import logger

from slither.slithir.operations.binary import BinaryType

# Set high precision for Decimal operations
getcontext().prec = 100


class IntervalRange:
    """Represents a closed interval [lower_bound, upper_bound] with high-precision decimal arithmetic."""

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
        else:
            raise ValueError(f"Unsupported operation: {operation}")
