from typing import Optional, TYPE_CHECKING

from .expression import Expression

if TYPE_CHECKING:
    from ..solidity_types.type import Type


class ExpressionTyped(Expression):
    def __init__(self):
        super(ExpressionTyped, self).__init__()
        self._type: Optional["Type"] = None

    @property
    def type(self):
        return self._type
