from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_rvalue
from slither.slithir.variables.member_variable import MemberVariable
from slither.slithir.variables.constant import Constant

from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum

class UpdateMemberDependency(OperationWithLValue):

    def __init__(self, base, member, new_val, lvalue):
        assert is_valid_rvalue(base) or isinstance(base, (Contract, Enum))
        assert is_valid_rvalue(lvalue) or isinstance(lvalue, (Contract, Enum))
        assert is_valid_rvalue(new_val)
        assert isinstance(member, Constant)
        super(UpdateMemberDependency, self).__init__()
        self._base = base
        self._member = member
        self._lvalue = lvalue
        self._new_val = new_val

    @property
    def read(self):
        return [self._base]

    @property
    def base(self):
        return self._base

    @property
    def member(self):
        return self._member

    @property
    def new_value(self):
        return self._new_val

    def __str__(self):
        return '{}({}) := UpdateDependency({}, {}, {})'.format(self.lvalue,
                                                               self.lvalue.type,
                                                               self.base,
                                                               self.member,
                                                               self.new_value)
