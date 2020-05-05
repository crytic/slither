from typing import Optional, TYPE_CHECKING

from slither.core.declarations import Modifier
from slither.core.declarations.function import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE


class InternalCall(Call, OperationWithLValue):
    def __init__(self,
                 function: Optional[Function],
                 nbr_arguments: int,
                 result: Optional["VALID_LVALUE"],
                 type_call: str):
        super(InternalCall, self).__init__()
        self._function = Optional[Function]
        if isinstance(function, Function):
            self._function: Function = function
            self._function_name: str = function.name
            self._contract_name: str = function.contract_declarer.name
        else:
            self._function = None
            self._function_name, self._contract_name = function
        # self._contract = contract
        self._nbr_arguments: int = nbr_arguments
        self._type_call = type_call
        self._lvalue: Optional["VALID_LVALUE"] = result

    @property
    def read(self):
        return list(self._unroll(self.arguments))

    @property
    def function(self) -> Optional[Function]:
        return self._function

    @function.setter
    def function(self, f):
        self._function = f

    @property
    def function_name(self) -> str:
        return self._function_name

    @property
    def contract_name(self) -> str:
        return self._contract_name

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    @property
    def is_modifier_call(self) -> bool:
        """
        Check if the destination is a modifier
        :return: bool
        """
        return isinstance(self.function, Modifier)

    def __str__(self):
        args = [str(a) for a in self.arguments]
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = "{}({}) = ".format(self.lvalue, ",".join(str(x) for x in self.lvalue.type))
        else:
            lvalue = "{}({}) = ".format(self.lvalue, self.lvalue.type)
        if self.is_modifier_call:
            txt = "{}MODIFIER_CALL, {}({})"
        else:
            txt = "{}INTERNAL_CALL, {}({})"
        return txt.format(lvalue, self.function.canonical_name, ",".join(args))
