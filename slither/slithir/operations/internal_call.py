from slither.core.declarations.function import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable


class InternalCall(Call, OperationWithLValue):

    def __init__(self, function, nbr_arguments, result, type_call):
        assert isinstance(function, Function)
        super(InternalCall, self).__init__()
        self._function = function
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result

    @property
    def read(self):
        return list(self.arguments)

    @property
    def function(self):
        return self._function

    @property
    def nbr_arguments(self):
        return self._nbr_arguments

    @property
    def type_call(self):
        return self._type_call

    def __str__(self):
        args = [str(a) for a in self.arguments]
        return str(self.lvalue) +' = INTERNAL_CALL {}.{} ({}) '.format(self.function.contract.name, self.function.full_name, ','.join(args))
   #     return str(self.lvalue) +' = INTERNALCALL {} (arg {})'.format(self.function,
   #                                                                   self.nbr_arguments)

