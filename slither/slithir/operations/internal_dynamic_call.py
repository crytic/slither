from slither.core.declarations.function import Function
from slither.core.solidity_types import FunctionType
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue


class InternalDynamicCall(Call, OperationWithLValue):

    def __init__(self, lvalue, function, function_type):
        assert isinstance(function_type, FunctionType)
        assert isinstance(function, Variable)
        assert is_valid_lvalue(lvalue)
        super(InternalDynamicCall, self).__init__()
        self._function = function
        self._function_type = function_type
        self._lvalue = lvalue

    @property
    def read(self):
        return list(self.arguments) + [self.function]

    @property
    def function(self):
        return self._function

    @property
    def function_type(self):
        return self._function_type

    def __str__(self):
        args = [str(a) for a in self.arguments]
        if not self.lvalue:
            lvalue = ''
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = '{}({}) = '.format(self.lvalue, ','.join(str(x) for x in self.lvalue.type))
        else:
            lvalue = '{}({}) = '.format(self.lvalue, self.lvalue.type)
        txt = '{}INTERNAL_DYNAMIC_CALL {}({})'
        return txt.format(lvalue,
                          self.function.name,
                          ','.join(args))

