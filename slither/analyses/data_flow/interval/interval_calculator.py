from decimal import Decimal
from typing import Callable, Dict, Tuple, Union

from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.core.variables.variable import Variable
from slither.slithir.operations.binary import BinaryType
from slither.slithir.variables.constant import Constant


class IntervalCalculator:
    """
    Static utility class for mathematical operations on intervals.
    Provides arithmetic bounds calculation and constraint application.
    """

    @staticmethod
    def calculate_arithmetic_bounds(
        a: Decimal, b: Decimal, c: Decimal, d: Decimal, operation_type: BinaryType
    ) -> Tuple[Decimal, Decimal]:
        """Calculate min and max bounds for arithmetic operations."""
        operations: Dict[BinaryType, Callable[[Decimal, Decimal], Decimal]] = {
            BinaryType.ADDITION: lambda x, y: x + y,
            BinaryType.SUBTRACTION: lambda x, y: x - y,
            BinaryType.MULTIPLICATION: lambda x, y: x * y,
            BinaryType.DIVISION: lambda x, y: x / y if y != 0 else Decimal("Infinity"),
        }
        op: Callable[[Decimal, Decimal], Decimal] = operations[operation_type]
        results: list[Decimal] = [op(a, c), op(a, d), op(b, c), op(b, d)]
        return min(results), max(results)

    @staticmethod
    def apply_comparison_constraint_to_interval(
        interval: IntervalInfo, constraint_value: Decimal, op_type: BinaryType
    ) -> None:
        """Apply comparison constraint to interval bounds."""
        if op_type == BinaryType.GREATER_EQUAL:
            interval.lower_bound = max(interval.lower_bound, constraint_value)
        elif op_type == BinaryType.GREATER:
            interval.lower_bound = max(interval.lower_bound, constraint_value + Decimal("1"))
        elif op_type == BinaryType.LESS_EQUAL:
            interval.upper_bound = min(interval.upper_bound, constraint_value)
        elif op_type == BinaryType.LESS:
            interval.upper_bound = min(interval.upper_bound, constraint_value - Decimal("1"))
        elif op_type == BinaryType.EQUAL:
            if (
                constraint_value >= interval.lower_bound
                and constraint_value <= interval.upper_bound
            ):
                interval.lower_bound = interval.upper_bound = constraint_value
            else:
                interval.lower_bound = Decimal("1")
                interval.upper_bound = Decimal("0")
        elif op_type == BinaryType.NOT_EQUAL:
            if constraint_value == interval.lower_bound == interval.upper_bound:
                interval.lower_bound = Decimal("1")
                interval.upper_bound = Decimal("0")
            elif constraint_value == interval.lower_bound:
                interval.lower_bound = constraint_value + Decimal("1")
            elif constraint_value == interval.upper_bound:
                interval.upper_bound = constraint_value - Decimal("1")

    @staticmethod
    def apply_equality_constraints(left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply equality constraints between two intervals."""
        common_lower: Decimal = max(left.lower_bound, right.lower_bound)
        common_upper: Decimal = min(left.upper_bound, right.upper_bound)
        if common_lower <= common_upper:
            left.lower_bound = right.lower_bound = common_lower
            left.upper_bound = right.upper_bound = common_upper

    @staticmethod
    def apply_inequality_constraints(left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply inequality constraints between two intervals."""
        if (
            left.lower_bound == left.upper_bound
            and right.lower_bound == right.upper_bound
            and left.lower_bound == right.lower_bound
        ):
            left.lower_bound = Decimal("1")
            left.upper_bound = Decimal("0")
            right.lower_bound = Decimal("1")
            right.upper_bound = Decimal("0")

    @staticmethod
    def apply_less_than_constraints(left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply less than constraints between two intervals."""
        if right.lower_bound != Decimal("-Infinity"):
            left.upper_bound = min(left.upper_bound, right.upper_bound - Decimal("1"))
        if left.upper_bound != Decimal("Infinity"):
            right.lower_bound = max(right.lower_bound, left.lower_bound + Decimal("1"))

    @staticmethod
    def apply_less_equal_constraints(left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply less than or equal constraints between two intervals."""
        if right.lower_bound != Decimal("-Infinity"):
            left.upper_bound = min(left.upper_bound, right.upper_bound)
        if left.upper_bound != Decimal("Infinity"):
            right.lower_bound = max(right.lower_bound, left.lower_bound)

    @staticmethod
    def apply_greater_than_constraints(left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply greater than constraints between two intervals."""
        if left.lower_bound != Decimal("-Infinity"):
            right.upper_bound = min(right.upper_bound, left.upper_bound - Decimal("1"))
        if right.upper_bound != Decimal("Infinity"):
            left.lower_bound = max(left.lower_bound, right.lower_bound + Decimal("1"))

    @staticmethod
    def apply_greater_equal_constraints(left: IntervalInfo, right: IntervalInfo) -> None:
        """Apply greater than or equal constraints between two intervals."""
        if left.lower_bound != Decimal("-Infinity"):
            right.upper_bound = min(right.upper_bound, left.upper_bound)
        if right.upper_bound != Decimal("Infinity"):
            left.lower_bound = max(left.lower_bound, right.lower_bound)

    @staticmethod
    def is_valid_interval(interval: IntervalInfo) -> bool:
        """Check if an interval is valid (lower <= upper)."""
        return interval.lower_bound <= interval.upper_bound

    @staticmethod
    def create_interval_from_type(
        var_type, min_val: Union[int, Decimal], max_val: Union[int, Decimal]
    ) -> IntervalInfo:
        """Create interval from type with min/max bounds."""
        return IntervalInfo(
            upper_bound=Decimal(str(max_val)),
            lower_bound=Decimal(str(min_val)),
            var_type=var_type,
        )

    @staticmethod
    def retrieve_interval_info(
        var: Union[Constant, Variable], domain_state_info: dict, operation
    ) -> IntervalInfo:
        """Retrieve interval information for a variable or constant."""
        if isinstance(var, Constant):
            value: Decimal = Decimal(str(var.value))
            return IntervalInfo(upper_bound=value, lower_bound=value, var_type=None)
        elif isinstance(var, Variable):
            # This would need to be implemented with VariableManager dependency
            # For now, return a default interval
            return IntervalInfo(var_type=None)
        return IntervalInfo(var_type=None)
