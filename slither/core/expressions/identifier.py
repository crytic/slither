from typing import TYPE_CHECKING, Optional

from slither.core.expressions.expression import Expression

if TYPE_CHECKING:
    from slither.core.variables.variable import Variable
    from slither.core.solidity_types.type import Type


class Identifier(Expression):
    def __init__(self, value) -> None:
        super().__init__()
        self._value: "Variable" = value
        self._type: Optional["Type"] = None

    @property
    def type(self) -> Optional["Type"]:
        return self._type

    @type.setter
    def type(self, new_type: "Type") -> None:
        self._type = new_type

    @property
    def value(self) -> "Variable":
        return self._value

    def __str__(self) -> str:
        return str(self._value)
