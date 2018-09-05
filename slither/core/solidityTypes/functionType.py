from slither.core.solidityTypes.type import Type
from slither.core.variables.functionTypeVariable import FunctionTypeVariable
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
        params = ".".join([str(x) for x in self._params])
        return_values = ".".join([str(x) for x in self._return_values])
        return 'function({}) returns ({})'.format(params, return_values)

