from slither.slithir.operations import Operation
from slither.slithir.operations import OperationWithLValue
from slither.slithir.utils.utils import is_valid_rvalue
from slither.slithir.variables.member_variable import MemberVariable
from slither.slithir.variables.constant import Constant

from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum


class UpdateIndex(Operation):
    def __init__(self, base, offset, new_val):
        assert is_valid_rvalue(base)
        assert is_valid_rvalue(new_val)
        assert is_valid_rvalue(offset)
        super(UpdateIndex, self).__init__()
        self._base = base
        self._offset = offset
        self._new_val = new_val

    @property
    def read(self):
        return [self._base, self._new_val]

    @property
    def base(self):
        return self._base

    @property
    def offset(self):
        return self._offset

    @property
    def new_value(self):
        return self._new_val

    def __str__(self):
        return "Update({}, {}, {})".format(self.base, self.offset, self.new_value)
