from typing import Union, List

from slither.core.expressions.expression import Expression
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal


class IndexAccess(Expression):
    def __init__(
        self,
        left_expression: Union["IndexAccess", Identifier],
        right_expression: Union[Literal, Identifier],
    ) -> None:
        super().__init__()
        self._expressions = [left_expression, right_expression]

    @property
    def expressions(self) -> List["Expression"]:
        return self._expressions

    @property
    def expression_left(self) -> "Expression":
        return self._expressions[0]

    @property
    def expression_right(self) -> "Expression":
        return self._expressions[1]

    def __str__(self) -> str:
        return str(self.expression_left) + "[" + str(self.expression_right) + "]"
