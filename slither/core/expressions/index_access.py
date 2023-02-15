from typing import Union, List, TYPE_CHECKING

from slither.core.expressions.expression_typed import ExpressionTyped
from slither.core.expressions.identifier import Identifier
from slither.core.expressions.literal import Literal


if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.core.solidity_types.type import Type


class IndexAccess(ExpressionTyped):
    def __init__(
        self,
        left_expression: Union["IndexAccess", Identifier],
        right_expression: Union[Literal, Identifier],
        index_type: str,
    ) -> None:
        super().__init__()
        self._expressions = [left_expression, right_expression]
        # TODO type of undexAccess is not always a Type
        #        assert isinstance(index_type, Type)
        self._type: "Type" = index_type

    @property
    def expressions(self) -> List["Expression"]:
        return self._expressions

    @property
    def expression_left(self) -> "Expression":
        return self._expressions[0]

    @property
    def expression_right(self) -> "Expression":
        return self._expressions[1]

    @property
    def type(self) -> "Type":
        return self._type

    def __str__(self) -> str:
        return str(self.expression_left) + "[" + str(self.expression_right) + "]"
