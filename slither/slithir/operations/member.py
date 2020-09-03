from slither.core.declarations import Contract
from slither.core.declarations.enum import Enum
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_rvalue
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.reference import ReferenceVariable


class Member(OperationWithLValue):
    def __init__(self, variable_left, variable_right, result):
        assert is_valid_rvalue(variable_left) or isinstance(
            variable_left, (Contract, Enum)
        )
        assert isinstance(variable_right, Constant)
        assert isinstance(result, ReferenceVariable)
        super().__init__()
        self._variable_left = variable_left
        self._variable_right = variable_right
        self._lvalue = result
        self._gas = None
        self._value = None

    @property
    def read(self):
        return [self.variable_left, self.variable_right]

    @property
    def variable_left(self):
        return self._variable_left

    @property
    def variable_right(self):
        return self._variable_right

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self):
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    def __str__(self):
        return "{}({}) -> {}.{}".format(
            self.lvalue, self.lvalue.type, self.variable_left, self.variable_right
        )
