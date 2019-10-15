from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_rvalue
from slither.slithir.variables.member_variable import MemberVariable
from slither.slithir.variables.constant import Constant

from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum

class AccessMember(OperationWithLValue):

    def __init__(self, variable_left, variable_right, result):
        assert is_valid_rvalue(variable_left) or isinstance(variable_left, (Contract, Enum))
        assert isinstance(variable_right, Constant)
        assert isinstance(result, MemberVariable)
        super(AccessMember, self).__init__()
        self._variable_left = variable_left
        self._variable_right = variable_right
        self._lvalue = result

    @property
    def read(self):
        return [self.variable_left, self.variable_right]

    @property
    def variable_left(self):
        return self._variable_left

    @property
    def variable_right(self):
        return self._variable_right

    def __str__(self):
        return '{}({}) := Access({}, {})'.format(self.lvalue,
                                                 self.lvalue.type,
                                                 self.variable_left,
                                                 self.variable_right)
        # return '{}.{}({}) -> {}.{}'.format(self.lvalue.base,
        #                                    self.lvalue.member,
        #                                    self.lvalue.type,
        #                                    self.variable_left,
        #                                    self.variable_right)

