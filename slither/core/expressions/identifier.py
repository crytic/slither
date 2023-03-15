from typing import TYPE_CHECKING

from slither.core.expressions.expression_typed import ExpressionTyped

if TYPE_CHECKING:
    from slither.core.variables.variable import Variable


class Identifier(ExpressionTyped):
    def __init__(self, value) -> None:
        super().__init__()
        self._value: "Variable" = value

    @property
    def value(self) -> "Variable":
        return self._value

    def __str__(self) -> str:
        return str(self._value)
