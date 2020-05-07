from typing import TYPE_CHECKING, Union, List, Optional

from slither.core.declarations import Contract
from slither.core.declarations.enum import Enum
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_rvalue
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.member_variable import MemberVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE


class AccessMember(OperationWithLValue):
    def __init__(
        self,
        variable_left: Union["VALID_RVALUE", Contract, Enum],
        variable_right: Constant,
        result: MemberVariable,
    ):
        assert is_valid_rvalue(variable_left) or isinstance(variable_left, (Contract, Enum))
        assert isinstance(variable_right, Constant)
        assert isinstance(result, MemberVariable)
        super(AccessMember, self).__init__()
        self._variable_left = variable_left
        self._variable_right = variable_right
        self._lvalue: MemberVariable = result
        self._gas: Optional["VALID_RVALUE"] = None
        self._value: Optional["VALID_RVALUE"] = None

    @property
    def read(self) -> List[Union["VALID_RVALUE", Contract, Enum]]:
        return [self.variable_left, self.variable_right]

    @property
    def variable_left(self) -> Union["VALID_RVALUE", Contract, Enum]:
        return self._variable_left

    @property
    def variable_right(self) -> Constant:
        return self._variable_right

    @property
    def call_value(self) -> Optional["VALID_RVALUE"]:
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self) -> Optional["VALID_RVALUE"]:
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    @property
    def lvalue(self) -> MemberVariable:
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    def __str__(self):
        return "{}({}) := Access({}, {})".format(
            self.lvalue, self.lvalue.type, self.variable_left, self.variable_right
        )
