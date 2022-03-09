from typing import List, TYPE_CHECKING
from slither.core.expressions.expression_typed import ExpressionTyped


if TYPE_CHECKING:
    from slither.core.expressions.expression import Expression
    from slither.core.solidity_types.type import Type


class IndexAccess(ExpressionTyped):
    def __init__(self, left_expression, right_expression, index_type):
        super().__init__()
        self._expressions = [left_expression, right_expression]
        # TODO type of IndexAccess is not always a Type
        #        assert isinstance(index_type, Type)
        self._type: "Type" = index_type
        self._is_slice = False  # Default

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

    @property
    def is_slice(self) -> bool:
        """
        True if IndexRangeAccess, False if IndexAccess
        """
        return self._is_slice

    @is_slice.setter
    def is_slice(self, is_index_range_access: bool):
        self._is_slice = is_index_range_access

    def __str__(self):
        if self.is_slice:
            return f"{self.expression_left}[{self.expression_right} : ]"
        return f"{self.expression_left}[{self.expression_right}]"
