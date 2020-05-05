from typing import TYPE_CHECKING, Union, List

from slither.core.declarations import Function
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue


if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE


class Push(OperationWithLValue):
    def __init__(self, array: "VALID_LVALUE", value: Union["VALID_LVALUE", Function]):
        super().__init__()
        assert is_valid_rvalue(value) or isinstance(value, Function)
        assert is_valid_lvalue(array)
        self._value = value
        self._lvalue = array

    @property
    def read(self) -> List[Union["VALID_LVALUE", Function]]:
        return [self._value]

    @property
    def array(self) -> "VALID_LVALUE":
        return self._lvalue

    @property
    def value(self) -> Union["VALID_LVALUE", Function]:
        return self._value

    def __str__(self):
        return "PUSH {} in {}".format(self.value, self.lvalue)
