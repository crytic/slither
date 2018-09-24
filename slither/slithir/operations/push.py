import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

class Push(OperationWithLValue):

    def __init__(self, array, value):
        assert is_valid_rvalue(value)
        assert is_valid_lvalue(array)
        self._value = value
        self._lvalue = array

    @property
    def read(self):
        return [self._value]

    @property
    def array(self):
        return self._lvalue

    def value(self):
        return self._value

    def __str__(self):
        return "PUSH {} in  {}".format(self.value, self.lvalue)
