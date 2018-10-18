import logging

from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.variables import TupleVariable
from slither.core.declarations.function import Function
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

logger = logging.getLogger("AssignmentOperationIR")

class Assignment(OperationWithLValue):

    def __init__(self, left_variable, right_variable, variable_return_type):
        assert is_valid_lvalue(left_variable)
        assert is_valid_rvalue(right_variable) or isinstance(right_variable, (Function, TupleVariable))
        super(Assignment, self).__init__()
        self._variables = [left_variable, right_variable]
        self._lvalue = left_variable
        self._rvalue = right_variable
        self._variable_return_type = variable_return_type

    @property
    def variables(self):
        return list(self._variables)

    @property
    def read(self):
        return list(self.variables)

    @property
    def variable_return_type(self):
        return self._variable_return_type

    @property
    def rvalue(self):
        return self._rvalue

    def __str__(self):
        return '{} := {}'.format(self.lvalue, self.rvalue)
