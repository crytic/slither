from slither.core.declarations.function import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.slithir.variables import Constant

class InternalCall(Call, OperationWithLValue):

    def __init__(self, function, contract, nbr_arguments, result, type_call):
        super(InternalCall, self).__init__()
        if isinstance(function, Function):
            self._function = function
            self._function_name = function.name
        else:
            isinstance(function, Constant)
            self._function = None
            self._function_name = function
        self._contract = contract
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result

    @property
    def read(self):
        return list(self._unroll(self.arguments))

    @property
    def function(self):
        return self._function

    @function.setter
    def function(self, f):
        self._function = f

    @property
    def contract(self):
        return self._contract

    @property
    def function_name(self):
        return self._function_name

    @property
    def nbr_arguments(self):
        return self._nbr_arguments

    @property
    def type_call(self):
        return self._type_call

    def __str__(self):
        args = [str(a) for a in self.arguments]
        if not self.lvalue:
            lvalue = ''
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = '{}({}) = '.format(self.lvalue, ','.join(str(x) for x in self.lvalue.type))
        else:
            lvalue = '{}({}) = '.format(self.lvalue, self.lvalue.type)
        txt = '{}INTERNAL_CALL, {}.{}({})'
        return txt.format(lvalue,
                          self.function.contract.name,
                          self.function.full_name,
                          ','.join(args))

