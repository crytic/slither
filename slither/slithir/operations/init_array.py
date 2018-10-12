import logging
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

class InitArray(OperationWithLValue):

    def __init__(self, init_values, lvalue):
        assert all(is_valid_rvalue(v) for v in init_values)
        self._init_values = init_values
        self._lvalue = lvalue

    @property
    def read(self):
        return list(self.init_values)

    @property
    def init_values(self):
        return list(self._init_values)

    def __str__(self):
        return "{}({}) =  {}".format(self.lvalue, self.lvalue.type, [str(x) for x in self.init_values])
