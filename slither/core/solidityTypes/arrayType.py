from slither.core.solidityTypes.type import Type
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
            return str(self._type)+'[{}]'.format(str(self._length))
        return str(self._type)+'[]'

