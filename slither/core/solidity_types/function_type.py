from slither.core.solidity_types.type import Type
from slither.core.variables.function_type_variable import FunctionTypeVariable
from slither.core.expressions.expression import Expression

class FunctionType(Type):

    def __init__(self, params, return_values):
        assert all(isinstance(x, FunctionTypeVariable) for x in params)
        assert all(isinstance(x, FunctionTypeVariable) for x in return_values)
        super(FunctionType, self).__init__()
        self._params = params
        self._return_values = return_values

    @property
    def params(self):
        return self._params

    @property
    def return_values(self):
        return self._return_values

    def __str__(self):
        # Use x.type
        # x.name may be empty
        params = ",".join([str(x.type) for x in self._params])
        return_values = ",".join([str(x.type) for x in self._return_values])
        if return_values:
            return 'function({}) returns({})'.format(params, return_values)
        return 'function({})'.format(params)

    @property
    def parameters_signature(self):
        '''
            Return the parameters signature(without the return statetement)
        '''
        # Use x.type
        # x.name may be empty
        params = ",".join([str(x.type) for x in self._params])
        return '({})'.format(params)

    @property
    def signature(self):
        '''
            Return the signature(with the return statetement if it exists)
        '''
        # Use x.type
        # x.name may be empty
        params = ",".join([str(x.type) for x in self._params])
        return_values = ",".join([str(x.type) for x in self._return_values])
        if return_values:
            return '({}) returns({})'.format(params, return_values)
        return '({})'.format(params)



    def __eq__(self, other):
        if not isinstance(other, FunctionType):
            return False
        return self.params == other.params and self.return_values == other.return_values

    def __hash__(self):
        return hash(str(self))
