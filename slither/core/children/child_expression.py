from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.slithir.operations import Operation


class ChildExpression:
    def __init__(self) -> None:
        super().__init__()
        self._expression = None

    def set_expression(self, expression: Union["Expression", "Operation"]) -> None:
        self._expression = expression

    @property
    def expression(self) -> Union["Expression", "Operation"]:
        return self._expression
