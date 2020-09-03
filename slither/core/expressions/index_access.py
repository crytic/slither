from typing import List, TYPE_CHECKING

from slither.core.expressions.expression_typed import ExpressionTyped


if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.core.solidity_types.type import Type


class IndexAccess(ExpressionTyped):
    def __init__(self, left_expression, right_expression, index_type):
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

    def __str__(self):
        return str(self.expression_left) + "[" + str(self.expression_right) + "]"
