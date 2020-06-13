"""
Balance is modeled as a specific operation. It could have been modelized as a structure field,
but we decide to have it as an operand as an external call can change the balance of a contract, which would
have increase the SSA complexity
"""
from typing import TYPE_CHECKING, List

from slither.core.solidity_types import ElementaryType
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE


class Balance(OperationWithLValue):
    def __init__(self, value: "VALID_RVALUE", lvalue: "VALID_LVALUE"):
        super().__init__()
        assert is_valid_rvalue(value)
        assert is_valid_lvalue(lvalue)
        self._value: "VALID_RVALUE" = value
        self._lvalue: "VALID_LVALUE" = lvalue
        lvalue.set_type(ElementaryType("uint256"))

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return [self._value]

    @property
    def value(self) -> "VALID_RVALUE":
        return self._value

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    def __str__(self):
        return "{} -> BALANCE {}".format(self.lvalue, self.value)
