from decimal import Decimal, getcontext
from typing import Callable, Iterator, Optional, Set, Union

from loguru import logger

# Set high precision for Decimal operations
getcontext().prec = 100


class SingleValues:
    def __init__(
        self,
        values: Optional[Union[Set[Union[int, Decimal]], Union[int, Decimal]]] = None,
    ):
        """
        Initialize SingleValues with a set of values.

        Args:
            values: A set of values, a single value, or None for empty set
        """
        self._values: Set[Decimal] = set()

        if values is not None:
            if isinstance(values, (int, float, Decimal)):
                self.add(values)
            elif isinstance(values, (set, list, tuple)):
                for value in values:
                    self.add(value)
            else:
                self.add(values)

    def _convert_to_decimal(self, value: Union[int, float, Decimal]) -> Decimal:
        """Convert value to Decimal for consistent precision"""
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        return value

    def add(self, value: Union[int, float, Decimal]) -> None:
        """Add a value to the set"""
        decimal_value = self._convert_to_decimal(value)
        self._values.add(decimal_value)

    def get(self) -> Set[Decimal]:
        """Get the set of values"""
        return self._values.copy()

    def retrieve(self, value: Union[int, float, Decimal]) -> bool:
        """Check if a value exists in the set"""
        decimal_value = self._convert_to_decimal(value)
        return decimal_value in self._values

    def delete(self, value: Union[int, float, Decimal]) -> bool:
        """
        Delete a value from the set.

        Returns:
            True if value was found and deleted, False otherwise
        """
        decimal_value = self._convert_to_decimal(value)
        if decimal_value in self._values:
            self._values.remove(decimal_value)
            return True
        return False

    def clear(self) -> None:
        """Clear all values"""
        self._values.clear()

    def join(self, other: "SingleValues") -> "SingleValues":
        """Return a new SingleValues containing union of both sets"""
        result = SingleValues()
        result._values = self._values.union(other._values)
        return result

    def intersection(self, other: "SingleValues") -> "SingleValues":
        """Return a new SingleValues containing intersection of both sets"""
        result = SingleValues()
        result._values = self._values.intersection(other._values)
        return result

    def difference(self, other: "SingleValues") -> "SingleValues":
        """Return a new SingleValues containing values in self but not in other"""
        result = SingleValues()
        result._values = self._values.difference(other._values)
        return result

    def is_empty(self) -> bool:
        """Check if the set is empty"""
        return len(self._values) == 0

    def size(self) -> int:
        """Get the number of values"""
        return len(self._values)

    def contains_value(self, value: Union[int, float, Decimal]) -> bool:
        """Alias for retrieve method"""
        return self.retrieve(value)

    def deep_copy(self) -> "SingleValues":
        """Create a deep copy of the SingleValues"""
        result = SingleValues()
        result._values = self._values.copy()
        return result

    def __eq__(self, other):
        """Check equality with another SingleValues"""
        if not isinstance(other, SingleValues):
            return False
        return self._values == other._values

    def __hash__(self):
        """Hash function for SingleValues"""
        return hash(frozenset(self._values))

    def __len__(self):
        """Return the number of values"""
        return len(self._values)

    def __iter__(self) -> Iterator[Decimal]:
        """Allow iteration over values"""
        return iter(self._values)

    def __contains__(self, value: Union[int, float, Decimal]) -> bool:
        """Support 'in' operator"""
        return self.retrieve(value)

    def __str__(self):
        """String representation of SingleValues"""
        if self.is_empty():
            return "{}"

        # Sort values for consistent output
        sorted_values = sorted(self._values)

        # Format values (show as int if they're whole numbers)
        formatted_values = []
        for value in sorted_values:
            if value == int(value):
                formatted_values.append(str(int(value)))
            else:
                formatted_values.append(str(value))

        return "{" + ", ".join(formatted_values) + "}"

    def __repr__(self):
        """Detailed representation of SingleValues"""
        return f"SingleValues({self._values})"

    def apply_operation(
        self, operand: Union[int, float, Decimal], operation: Callable[[Decimal, Decimal], Decimal]
    ) -> "SingleValues":
        """Apply a binary operation to all values with a given operand"""

        result = SingleValues()
        decimal_operand = self._convert_to_decimal(operand)

        for value in self._values:
            try:
                result_value = operation(value, decimal_operand)
                result.add(result_value)
            except ZeroDivisionError:
                logger.error(f"Division by zero detected: {value} / {decimal_operand}")
                raise ValueError(f"Division by zero: {value} / {decimal_operand}")
            except Exception as e:
                logger.warning(f"Error in arithmetic operation {value} op {decimal_operand}: {e}")
                # Skip invalid operations but continue processing others

        return result
