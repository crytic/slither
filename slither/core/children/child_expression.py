from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression


class ChildExpression:
    def __init__(self):
        super().__init__()
        self._expression = None

    def set_expression(self, expression: "Expression"):
        self._expression = expression

    @property
    def expression(self) -> "Expression":
        return self._expression
