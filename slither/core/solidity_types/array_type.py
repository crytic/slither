from typing import Optional

from slither.core.expressions import Literal
from slither.core.expressions.expression import Expression
from slither.core.solidity_types.type import Type
from slither.visitors.expression.constants_folding import ConstantFolding


class ArrayType(Type):
    def __init__(self, t, length):
        assert isinstance(t, Type)
        if length:
            if isinstance(length, int):
                length = Literal(length, "uint256")
            assert isinstance(length, Expression)
        super(ArrayType, self).__init__()
        self._type: Type = t
        self._length: Optional[Expression] = length

        if length:
            if not isinstance(length, Literal):
                cf = ConstantFolding(length, "uint256")
                length = cf.result()
            self._length_value = length
        else:
            self._length_value = None

    @property
    def type(self) -> Type:
        return self._type

    @property
    def length(self) -> Optional[Expression]:
        return self._length

    @property
    def lenght_value(self) -> Optional[Literal]:
        return self._length_value

    @property
    def storage_size(self):
        if self._length_value:
            elem_size, _ = self._type.storage_size
            return elem_size * int(self._length_value.value), True
        return 32, True

    def __str__(self):
        if self._length:
            return str(self._type) + "[{}]".format(str(self._length_value))
        return str(self._type) + "[]"

    def __eq__(self, other):
        if not isinstance(other, ArrayType):
            return False
        return self._type == other.type and self.length == other.length

    def __hash__(self):
        return hash(str(self))
