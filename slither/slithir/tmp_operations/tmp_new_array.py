from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.solidity_types.type import Type


class TmpNewArray(OperationWithLValue):
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
        return []

    @property
    def depth(self):
        return self._depth

    def __str__(self):
        return "{} = new {}{}".format(self.lvalue, self.array_type, "[]" * self._depth)
