from typing import List, Optional, Union
from slither.core.solidity_types import FunctionType
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.variables.constant import Constant
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA


class InternalDynamicCall(
    Call, OperationWithLValue
):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        lvalue: Optional[Union[TemporaryVariableSSA, TemporaryVariable]],
        function: Union[LocalVariable, LocalIRVariable],
        function_type: FunctionType,
    ) -> None:
        assert isinstance(function_type, FunctionType)
        assert isinstance(function, Variable)
        assert is_valid_lvalue(lvalue) or lvalue is None
        super().__init__()
        self._function: Variable = function
        self._function_type = function_type
        self._lvalue = lvalue

        self._callid = None  # only used if gas/value != 0
        self._call_value = None
        self._call_gas = None

    @property
    def read(self) -> List[Union[Constant, LocalIRVariable, LocalVariable]]:
        return self._unroll(self.arguments) + [self.function]

    @property
    def function(self) -> Variable:
        return self._function

    @property
    def function_type(self) -> FunctionType:
        return self._function_type

    @property
    def call_value(self):
        return self._call_value

    @call_value.setter
    def call_value(self, v):
        self._call_value = v

    @property
    def call_gas(self):
        return self._call_gas

    @call_gas.setter
    def call_gas(self, v):
        self._call_gas = v

    @property
    def call_id(self):
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    def __str__(self):
        value = ""
        gas = ""
        args = [str(a) for a in self.arguments]
        if self.call_value:
            value = f"value:{self.call_value}"
        if self.call_gas:
            gas = f"gas:{self.call_gas}"
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = f"{self.lvalue}({','.join(str(x) for x in self.lvalue.type)}) = "
        else:
            lvalue = f"{self.lvalue}({self.lvalue.type}) = "
        txt = "{}INTERNAL_DYNAMIC_CALL {}({}) {} {}"
        return txt.format(lvalue, self.function.name, ",".join(args), value, gas)
