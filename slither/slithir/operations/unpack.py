from typing import TYPE_CHECKING, List

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.tuple import TupleVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE


class Unpack(OperationWithLValue):
    def __init__(self, result: "VALID_LVALUE", tuple_var: TupleVariable, idx: int):
        assert is_valid_lvalue(result)
        assert isinstance(tuple_var, TupleVariable)
        assert isinstance(idx, int)
        super(Unpack, self).__init__()
        self._tuple: TupleVariable = tuple_var
        self._idx: int = idx
        self._lvalue = result

    @property
    def read(self) -> List[TupleVariable]:
        return [self.tuple]

    @property
    def tuple(self) -> TupleVariable:
        return self._tuple

    @property
    def index(self) -> int:
        return self._idx

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    def __str__(self):
        return "{}({})= UNPACK {} index: {} ".format(
            self.lvalue, self.lvalue.type, self.tuple, self.index
        )
