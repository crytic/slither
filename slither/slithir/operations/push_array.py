import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

class PushArray(OperationWithLValue):

    def __init__(self, array, values):
        assert all(is_valid_rvalue(value) for value in values)
        assert is_valid_lvalue(array)
        self._values = values
        self._lvalue = array

    @property
    def read(self):
        return list(self._values)

    @property
    def array(self):
        return self._lvalue

    @property
    def values(self):
        return list(self._values)

    def __str__(self):
        return "PUSH_ARRAY {} in {}".format([str(x) for x in self.values], self.lvalue)
