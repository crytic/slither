from typing import List, Union, Optional

from slither.core.declarations import Function
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable

from slither.slithir.variables.constant import Constant
from slither.core.variables.local_variable import LocalVariable
from slither.slithir.variables.local_variable import LocalIRVariable
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA
from slither.slithir.variables.tuple import TupleVariable
from slither.slithir.variables.tuple_ssa import TupleVariableSSA


class LowLevelCall(Call, OperationWithLValue):  # pylint: disable=too-many-instance-attributes
    """
    High level message call
    """

    def __init__(
        self,
        destination: Union[LocalVariable, LocalIRVariable, TemporaryVariableSSA, TemporaryVariable],
        function_name: Constant,
        nbr_arguments: int,
        result: Union[TupleVariable, TupleVariableSSA],
        type_call: str,
    ) -> None:
        # pylint: disable=too-many-arguments
        assert isinstance(destination, (Variable, SolidityVariable))
        assert isinstance(function_name, Constant)
        super().__init__()
        self._destination = destination
        self._function_name = function_name
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._callid = None  # only used if gas/value != 0

        self._call_value = None
        self._call_gas = None

    @property
    def call_id(self):
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

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
    def read(
        self,
    ) -> List[
        Union[LocalIRVariable, Constant, LocalVariable, TemporaryVariableSSA, TemporaryVariable]
    ]:
        all_read = [self.destination, self.call_gas, self.call_value] + self.arguments
        # remove None
        return self._unroll([x for x in all_read if x])

    def can_reenter(self, _callstack: Optional[List[Union[Function, Variable]]] = None) -> bool:
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        if self.function_name == "staticcall":
            return False
        return True

    def can_send_eth(self) -> bool:
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return self._call_value is not None

    @property
    def destination(
        self,
    ) -> Union[LocalVariable, LocalIRVariable, TemporaryVariableSSA, TemporaryVariable]:
        return self._destination

    @property
    def function_name(self) -> Constant:
        return self._function_name

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    def __str__(self):
        value = ""
        gas = ""
        if self.call_value:
            value = f"value:{self.call_value}"
        if self.call_gas:
            gas = f"gas:{self.call_gas}"
        arguments = []
        if self.arguments:
            arguments = self.arguments
        return_type = self.lvalue.type

        if return_type and isinstance(return_type, list):
            return_type = ",".join(str(x) for x in return_type)

        txt = "{}({}) = LOW_LEVEL_CALL, dest:{}, function:{}, arguments:{} {} {}"
        return txt.format(
            self.lvalue,
            return_type,
            self.destination,
            self.function_name,
            [str(x) for x in arguments],
            value,
            gas,
        )
