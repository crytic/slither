import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue
from slither.core.solidity_types.elementary_type import ElementaryType

class Length(OperationWithLValue):

    def __init__(self, value, lvalue):
        assert is_valid_rvalue(value)
        assert is_valid_lvalue(lvalue)
        self._value = value
        self._lvalue = lvalue
        lvalue.set_type(ElementaryType('uint256'))

    @property
    def read(self):
        return [self._value]

    @property
    def value(self):
        return self._value

    def __str__(self):
        return "{} -> LENGTH {}".format(self.lvalue, self.value)
