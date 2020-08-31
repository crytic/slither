from typing import TYPE_CHECKING, List

from slither.core.declarations import Contract
from slither.core.solidity_types.type import Type
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class TypeConversion(OperationWithLValue):
    def __init__(self, result: "VALID_LVALUE", variable: "VALID_RVALUE", variable_type: Type):
        super().__init__()
        assert is_valid_rvalue(variable) or isinstance(variable, Contract)
        assert is_valid_lvalue(result)
        assert isinstance(variable_type, Type)

        self._variable = variable
        self._type = variable_type
        self._lvalue = result

    @property
    def variable(self) -> "VALID_RVALUE":
        return self._variable

    @property
    def type(self) -> Type:
        return self._type

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self.variable]

    def __str__(self):
        return str(self.lvalue) + " = CONVERT {} to {}".format(self.variable, self.type)
