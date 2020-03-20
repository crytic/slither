from slither.core.solidity_types.type import Type
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue


class TypeConversion(OperationWithLValue):

    def __init__(self, result, variable, variable_type):
        super().__init__()
        assert is_valid_rvalue(variable)
        assert is_valid_lvalue(result)
        assert isinstance(variable_type, Type)

        self._variable = variable
        self._type = variable_type
        self._lvalue = result
    

    @property
    def variable(self):
        return self._variable

    @property
    def type(self):
        return self._type

    @property
    def read(self):
        return [self.variable]

    def __str__(self):
        return str(self.lvalue) +' = CONVERT {} to {}'.format(self.variable, self.type)
