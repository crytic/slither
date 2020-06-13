from typing import TYPE_CHECKING, Union, List

from slither.core.declarations import Function
from slither.core.declarations.contract import Contract
from slither.core.declarations.enum import Enum
from slither.slithir.operations import Operation
from slither.slithir.utils.utils import is_valid_rvalue
from slither.slithir.variables import TupleVariable
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE


class UpdateMember(Operation):
    def __init__(
        self,
        base: Union["VALID_RVALUE", Contract, Enum],
        member: Constant,
        new_val: Union["VALID_RVALUE", Function, TupleVariable],
    ):
        assert is_valid_rvalue(base) or isinstance(base, (Contract, Enum))
        assert is_valid_rvalue(new_val) or isinstance(new_val, (Function, TupleVariable))
        assert isinstance(member, Constant)
        super(UpdateMember, self).__init__()
        self._base = base
        self._member = member
        self._new_val = new_val

    @property
    def read(self) -> List[Union["VALID_RVALUE", Contract, Enum, Function, TupleVariable]]:
        return [self._base, self._new_val]

    @property
    def base(self) -> Union["VALID_RVALUE", Contract, Enum]:
        return self._base

    @property
    def member(self) -> Constant:
        return self._member

    @property
    def new_value(self) -> Union["VALID_RVALUE", Function, TupleVariable]:
        return self._new_val

    def __str__(self):
        return "Update({}, {}, {})".format(self.base, self.member, self.new_value)
