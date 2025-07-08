from decimal import Decimal, getcontext
from typing import Callable, Dict, Union

from slither.slithir.operations.binary import BinaryType

# Set high precision for Decimal operations
getcontext().prec = 100


class IntervalRange:
    def __init__(
        self,
        upper_bound: Union[int, Decimal] = Decimal("Infinity"),
        lower_bound: Union[int, Decimal] = Decimal("-Infinity"),
    ):
        # Convert to Decimal to maintain precision
        if isinstance(upper_bound, (int, float)):
            self.upper_bound = Decimal(str(upper_bound))
        else:
            self.upper_bound = upper_bound

        if isinstance(lower_bound, (int, float)):
            self.lower_bound = Decimal(str(lower_bound))
        else:
            self.lower_bound = lower_bound

    def __eq__(self, other):
        return self.upper_bound == other.upper_bound and self.lower_bound == other.lower_bound

    def __hash__(self):
        return hash((self.upper_bound, self.lower_bound))

    def deep_copy(self) -> "IntervalRange":
        return IntervalRange(self.upper_bound, self.lower_bound)

    def join(self, other: "IntervalRange") -> None:
        self.lower_bound = min(self.lower_bound, other.lower_bound)
        self.upper_bound = max(self.upper_bound, other.upper_bound)

    def get_lower(self) -> Decimal:
        """Get the lower bound of the interval"""
        return self.lower_bound

    def get_upper(self) -> Decimal:
        """Get the upper bound of the interval"""
        return self.upper_bound

    def __str__(self):
        lower_str = (
            str(int(self.lower_bound))
            if self.lower_bound == int(self.lower_bound)
            else str(self.lower_bound)
        )
        upper_str = (
            str(int(self.upper_bound))
            if self.upper_bound == int(self.upper_bound)
            else str(self.upper_bound)
        )
        return f"[{lower_str}, {upper_str}]"

    @staticmethod
    def calculate_arithmetic_bounds(
        left_range: "IntervalRange", right_range: "IntervalRange", operation_type: "BinaryType"
    ) -> "IntervalRange":
        """Calculate min and max bounds for arithmetic operations between two intervals."""
        # Extract bounds from the intervals
        a = left_range.get_lower()  # left min
        b = left_range.get_upper()  # left max
        c = right_range.get_lower()  # right min
        d = right_range.get_upper()  # right max

        operations: Dict["BinaryType", Callable[[Decimal, Decimal], Decimal]] = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y if y != 0 else Decimal("Infinity"),
        }
        op: Callable[[Decimal, Decimal], Decimal] = operations[operation_type]
        results: list[Decimal] = [op(a, c), op(a, d), op(b, c), op(b, d)]

        min_result = min(results)
        max_result = max(results)

        return IntervalRange(upper_bound=max_result, lower_bound=min_result)
