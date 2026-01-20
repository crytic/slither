from typing import TYPE_CHECKING, Any

from slither.core.expressions.expression import Expression
from slither.core.solidity_types.elementary_type import Fixed, Int, Ufixed, Uint
from slither.utils.arithmetic import convert_subdenomination
from slither.utils.integer_conversion import convert_string_to_int

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type

# Frozenset of numeric type strings for O(1) lookup (avoids list concatenation on each check)
_NUMERIC_TYPES: frozenset[str] = frozenset(Int + Uint + Fixed + Ufixed + ["address"])


class Literal(Expression):
    def __init__(
        self, value: int | str, custom_type: "Type", subdenomination: str | None = None
    ) -> None:
        super().__init__()
        self._value = value
        self._type = custom_type
        self._subdenomination = subdenomination

        # Cache converted int string for numeric types (avoids expensive re-conversion in __str__)
        # Only cache when custom_type is a string to preserve original __str__ behavior:
        # ElementaryType inputs bypass conversion (self.type in list fails for objects)
        self._cached_str: str | None = None
        if not subdenomination and isinstance(custom_type, str) and custom_type in _NUMERIC_TYPES:
            self._cached_str = str(convert_string_to_int(value))

    @property
    def value(self) -> int | str:
        return self._value

    @property
    def converted_value(self) -> int | str:
        """Return the value of the literal, accounting for subdenomination e.g. ether"""
        if self.subdenomination:
            return convert_subdenomination(self._value, self.subdenomination)
        return self._value

    @property
    def type(self) -> "Type":
        return self._type

    @property
    def subdenomination(self) -> str | None:
        return self._subdenomination

    def __str__(self) -> str:
        if self.subdenomination:
            return str(self.converted_value)

        if self._cached_str is not None:
            return self._cached_str

        # Non-numeric types (e.g., string literals) - return value as-is
        return str(self._value)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Literal):
            return False
        return (self.value, self.subdenomination) == (other.value, other.subdenomination)
