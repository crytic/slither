from typing import TYPE_CHECKING, Optional

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.solidity_types.type import Type

class TmpNewArray(OperationWithLValue):
    def __init__(self, depth: int, array_type: Type, lvalue: Optional["VALID_LVALUE"]):
        super(TmpNewArray, self).__init__()
        assert isinstance(array_type, Type)
        self._depth = depth
        self._array_type = array_type
        self._lvalue = lvalue

    @property
    def array_type(self) -> Type:
        return self._array_type

    @property
    def read(self):
        return []

    @property
    def depth(self) -> int:
        return self._depth

    def __str__(self):
        return "{} = new {}{}".format(self.lvalue, self.array_type, "[]" * self._depth)
