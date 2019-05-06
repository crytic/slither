from slither.core.variables.variable import Variable
from slither.core.solidity_types.type import Type
from slither.core.expressions.expression import Expression
from slither.core.expressions import Literal
from slither.visitors.expression.constants_folding import ConstantFolding

class ArrayType(Type):

    def __init__(self, t, length):
        assert isinstance(t, Type)
        if length:
            if isinstance(length, int):
                length = Literal(length, 'uint256')
            assert isinstance(length, Expression)
        super(ArrayType, self).__init__()
        self._type = t
        self._length = length

        if length:
            if not isinstance(length, Literal):
                cf = ConstantFolding(length, "uint256")
                length = cf.result()
            self._length_value = length
        else:
            self._length_value = None

    @property
    def type(self):
        return self._type

    @property
    def length(self):
        return self._length

    def __str__(self):
        if self._length:
            return str(self._type)+'[{}]'.format(str(self._length_value))
        return str(self._type)+'[]'


    def __eq__(self, other):
        if not isinstance(other, ArrayType):
            return False
        return self._type == other.type and self.length == other.length

    def __hash__(self):
        return hash(str(self))
