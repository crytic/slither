from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.operations.call import Call
from slither.core.solidity_types.type import Type


class NewArray(Call, OperationWithLValue):
    def __init__(self, depth, array_type, lvalue):
        super().__init__()
        assert isinstance(array_type, Type)
        self._depth = depth
        self._array_type = array_type

        self._lvalue = lvalue

    @property
    def array_type(self):
        return self._array_type

    @property
    def read(self):
        return self._unroll(self.arguments)

    @property
    def depth(self):
        return self._depth

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return f"{self.lvalue} = new {self.array_type}{'[]' * self.depth}({','.join(args)})"
