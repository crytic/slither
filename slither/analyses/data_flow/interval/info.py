from decimal import Decimal, getcontext
from typing import Optional, Union

from slither.core.solidity_types.elementary_type import ElementaryType

# Set high precision for Decimal operations
getcontext().prec = 100


class IntervalInfo:
    def __init__(
        self,
        upper_bound: Union[int, Decimal] = Decimal("Infinity"),
        lower_bound: Union[int, Decimal] = Decimal("-Infinity"),
        var_type: Optional[ElementaryType] = None,
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
        self.var_type = var_type

    def __eq__(self, other):
        return self.upper_bound == other.upper_bound and self.lower_bound == other.lower_bound

    def __hash__(self):
        return hash((self.upper_bound, self.lower_bound))

    def deep_copy(self) -> "IntervalInfo":
        return IntervalInfo(self.upper_bound, self.lower_bound, self.var_type)

    def join(self, other: "IntervalInfo") -> None:
        self.lower_bound = min(self.lower_bound, other.lower_bound)
        self.upper_bound = max(self.upper_bound, other.upper_bound)

    def get_type_bounds(self) -> tuple[Decimal, Decimal]:
        """Get the theoretical min/max bounds for this variable's type"""
        if self.var_type and hasattr(self.var_type, "max") and hasattr(self.var_type, "min"):
            return Decimal(str(self.var_type.min)), Decimal(str(self.var_type.max))
        else:
            # Default to uint256 bounds for temporary variables or unknown types
            return Decimal("0"), Decimal(
                "115792089237316195423570985008687907853269984665640564039457584007913129639935"
            )

    def has_overflow(self) -> bool:
        """Check if current bounds exceed the variable's type bounds"""
        type_min, type_max = self.get_type_bounds()
        return self.upper_bound > type_max

    def has_underflow(self) -> bool:
        """Check if current bounds go below the variable's type bounds"""
        type_min, type_max = self.get_type_bounds()
        return self.lower_bound < type_min

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
