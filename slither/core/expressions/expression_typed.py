from typing import Optional, TYPE_CHECKING

from slither.core.expressions.expression import Expression

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type


class ExpressionTyped(Expression):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self._type: Optional["Type"] = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_type: "Type"):
        self._type = new_type
