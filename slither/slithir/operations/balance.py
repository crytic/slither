"""
Balance is modeled as a specific operation. It could have been modelized as a structure field,
but we decide to have it as an operand as an external call can change the balance of a contract, which would
have increase the SSA complexity
"""
from slither.core.solidity_types import ElementaryType
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue


class Balance(OperationWithLValue):
    def __init__(self, value, lvalue):
        assert is_valid_rvalue(value)
        assert is_valid_lvalue(lvalue)
        self._value = value
        self._lvalue = lvalue
        lvalue.set_type(ElementaryType("uint256"))

    @property
    def read(self):
        return [self._value]

    @property
    def value(self):
        return self._value

    def __str__(self):
        return "{} -> BALANCE {}".format(self.lvalue, self.value)
