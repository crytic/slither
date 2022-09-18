from typing import Optional, Union, TYPE_CHECKING

from slither.core.expressions.expression import Expression
from slither.core.solidity_types.elementary_type import Byte, Fixed, Int, Ufixed, Uint
from slither.utils.arithmetic import convert_subdenomination
from slither.utils.integer_conversion import convert_string_to_int

if TYPE_CHECKING:
    from slither.core.solidity_types.type import Type


class Literal(Expression):
    def __init__(self, value, custom_type, subdenomination=None):
        super().__init__()
        self._value: Union[int, str] = value
        self._type = custom_type
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
        elif self.type in Int + Uint + Fixed + Ufixed + ["address"]:
            return str(convert_string_to_int(self._value))

        # be sure to handle any character
        return str(self._value)

    def __eq__(self, other):
        if not isinstance(other, Literal):
            return False
        return (self.value, self.subdenomination) == (other.value, other.subdenomination)
