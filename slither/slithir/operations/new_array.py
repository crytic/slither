from typing import Optional, TYPE_CHECKING, List

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.operations.call import Call
from slither.core.solidity_types.type import Type

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_RVALUE


class NewArray(Call, OperationWithLValue):
    def __init__(self, depth: int, array_type: Type, lvalue: Optional["VALID_LVALUE"]):
        super(NewArray, self).__init__()
        assert isinstance(array_type, Type)
        self._depth = depth
        self._array_type = array_type

        self._lvalue = lvalue

    @property
    def array_type(self) -> Type:
        return self._array_type

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return self._unroll(self.arguments)

    @property
    def depth(self):
        return self._depth

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return "{} = new {}{}({})".format(
            self.lvalue, self.array_type, "[]" * self.depth, ",".join(args)
        )
