from typing import Optional, TYPE_CHECKING, List, Union

from slither.core.solidity_types import FunctionType
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class InternalDynamicCall(Call, OperationWithLValue):
    def __init__(
        self, lvalue: Optional["VALID_LVALUE"], function: Variable, function_type: FunctionType
    ):
        assert isinstance(function_type, FunctionType)
        assert isinstance(function, Variable)
        assert is_valid_lvalue(lvalue) or lvalue is None
        super(InternalDynamicCall, self).__init__()
        self._function: Variable = function
        self._function_type: FunctionType = function_type
        self._lvalue: Optional["VALID_LVALUE"] = lvalue

        self._callid: Optional[str] = None  # only used if gas/value != 0
        self._call_value: Optional["VALID_RVALUE"] = None
        self._call_gas: Optional["VALID_RVALUE"] = None

    @property
    def read(self) -> List[Union["VALID_RVALUE", Variable]]:
        return self._unroll(self.arguments) + [self.function]

    @property
    def function(self) -> Variable:
        return self._function

    @property
    def function_type(self) -> FunctionType:
        return self._function_type

    @property
    def call_value(self) -> Optional["VALID_RVALUE"]:
        return self._call_value

    @call_value.setter
    def call_value(self, v):
        self._call_value = v

    @property
    def call_gas(self) -> Optional["VALID_RVALUE"]:
        return self._call_gas

    @call_gas.setter
    def call_gas(self, v):
        self._call_gas = v

    @property
    def call_id(self) -> Optional[str]:
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    def __str__(self):
        value = ""
        gas = ""
        args = [str(a) for a in self.arguments]
        if self.call_value:
            value = "value:{}".format(self.call_value)
        if self.call_gas:
            gas = "gas:{}".format(self.call_gas)
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = "{}({}) = ".format(self.lvalue, ",".join(str(x) for x in self.lvalue.type))
        else:
            lvalue = "{}({}) = ".format(self.lvalue, self.lvalue.type)
        txt = "{}INTERNAL_DYNAMIC_CALL {}({}) {} {}"
        return txt.format(lvalue, self.function.name, ",".join(args), value, gas)
