from typing import Optional, Union, TYPE_CHECKING

from slither.core.expressions.expression import Expression
from slither.utils.arithmetic import convert_subdenomination

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type


class Literal(Expression):
    def __init__(self, value, type, subdenomination=None):
        super(Literal, self).__init__()
        self._value: Union[int, str] = value
        self._type = type
        self._subdenomination: Optional[str] = subdenomination

    @property
    def value(self) -> Union[int, str]:
        return self._value

    @property
    def type(self) -> "Type":
        return self._type

    @property
    def subdenomination(self) -> Optional[str]:
        return self._subdenomination

    def __str__(self):
        if self.subdenomination:
            return str(convert_subdenomination(self._value, self.subdenomination))
        # be sure to handle any character
        return str(self._value)
