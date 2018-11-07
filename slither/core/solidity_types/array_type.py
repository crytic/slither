from slither.core.variables.variable import Variable
from slither.core.solidity_types.type import Type
from slither.core.expressions.expression import Expression

class ArrayType(Type):

    def __init__(self, t, length):
        assert isinstance(t, Type)
        if length:
            assert isinstance(length, Expression)
        super(ArrayType, self).__init__()
        self._type = t
        self._length = length

    @property
    def type(self):
        return self._type

    @property
    def length(self):
        return self._length

    def __str__(self):
        if self._length:
            if isinstance(self._length.value, Variable) and self._length.value.is_constant:
                return str(self._type)+'[{}]'.format(str(self._length.value.expression))
            return str(self._type)+'[{}]'.format(str(self._length))
        return str(self._type)+'[]'


    def __eq__(self, other):
        if not isinstance(other, ArrayType):
            return False
        return self._type == other.type and self.length == other.length

    def __hash__(self):
        return hash(str(self))
