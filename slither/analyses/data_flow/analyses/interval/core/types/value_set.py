from decimal import Decimal, getcontext
from typing import Callable, Iterator, Set, Union

from loguru import logger

from slither.slithir.operations.binary import BinaryType

getcontext().prec = 100  # Set high precision for Decimal operations


class ValueSet:
    """Represents a set of discrete high-precision decimal values."""

    def __init__(self, values: Union[Set[Union[int, Decimal]], int, Decimal]):
        self._values: Set[Decimal] = set()
        if isinstance(values, (int, Decimal)):
            self.add(values)
        elif isinstance(values, (set, list, tuple)):
            for value in values:
                if not isinstance(value, (int, Decimal)):
                    raise TypeError(f"Unsupported type in ValueSet: {type(value)}")
                self.add(value)
        else:
            raise TypeError(f"Unsupported type for ValueSet initialization: {type(values)}")

    # Internal helper
    def _to_decimal(self, value: Union[int, Decimal]) -> Decimal:
        return Decimal(value) if isinstance(value, int) else value

    # Core operations
    def add(self, value: Union[int, Decimal]) -> None:
        self._values.add(self._to_decimal(value))

    def remove(self, value: Union[int, Decimal]) -> bool:
        decimal_value = self._to_decimal(value)
        if decimal_value in self._values:
            self._values.remove(decimal_value)
            return True
        return False

    def clear(self) -> None:
        self._values.clear()

    # Set operations
    def union(self, other: "ValueSet") -> "ValueSet":
        return ValueSet(self._values.union(other._values))

    def intersection(self, other: "ValueSet") -> "ValueSet":
        return ValueSet(self._values.intersection(other._values))

    def difference(self, other: "ValueSet") -> "ValueSet":
        return ValueSet(self._values.difference(other._values))

    # Queries
    def contains(self, value: Union[int, Decimal]) -> bool:
        return self._to_decimal(value) in self._values

    def is_empty(self) -> bool:
        return len(self._values) == 0

    def size(self) -> int:
        return len(self._values)

    def deep_copy(self) -> "ValueSet":
        """Create a deep copy of this ValueSet."""
        return ValueSet(self._values.copy())

    def join(self, other: "ValueSet") -> "ValueSet":
        """Return a new ValueSet containing union of both sets."""
        result = ValueSet(set())
        result._values = self._values.union(other._values)
        return result

    # Apply operations
    def apply(
        self, operand: Union[int, Decimal], operation: Callable[[Decimal, Decimal], Decimal]
    ) -> "ValueSet":
        result = ValueSet(set())
        decimal_operand = self._to_decimal(operand)
        for value in self._values:
            try:
                result.add(operation(value, decimal_operand))
            except ZeroDivisionError:
                logger.error(f"Division by zero detected: {value} / {decimal_operand}")
                raise ValueError(f"Division by zero: {value} / {decimal_operand}")
            except Exception as e:
                logger.warning(f"Error applying operation {value} op {decimal_operand}: {e}")
        return result

    def compute_arithmetic_with_scalar(
        self, scalar: Union[int, Decimal], operation_type: BinaryType
    ) -> "ValueSet":
        """Compute the result of applying a scalar operation to all values in this ValueSet."""
        result_values = ValueSet(set())
        decimal_scalar = self._to_decimal(scalar)

        # Apply operation to each value in the set
        for value in self._values:
            try:
                result_val = ValueSet._apply_scalar_op(value, decimal_scalar, operation_type)
                result_values.add(result_val)
            except Exception as e:
                logger.warning(f"Error in scalar arithmetic: {e}")

        return result_values

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

    # Magic methods
    def __eq__(self, other):
        return isinstance(other, ValueSet) and self._values == other._values

    def __hash__(self):
        return hash(frozenset(self._values))

    def __len__(self):
        return len(self._values)

    def __iter__(self) -> Iterator[Decimal]:
        return iter(self._values)

    def __contains__(self, value: Union[int, Decimal]) -> bool:
        return self.contains(value)

    def __str__(self):
        """Return string representation of the value set."""
        if self.is_empty():
            return "{}"

        # Sort values for consistent output
        sorted_values = sorted(self._values)

        # Format each value (show integers without decimal places)
        formatted_values = []
        for value in sorted_values:
            if value == int(value):
                formatted_values.append(str(int(value)))
            else:
                formatted_values.append(str(value))

        return "{" + ", ".join(formatted_values) + "}"
