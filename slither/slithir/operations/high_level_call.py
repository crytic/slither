from typing import List, Optional, Union

from slither.core.declarations import Contract
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.declarations.function import Function

from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant
from slither.core.source_mapping.source_mapping import SourceMapping
from slither.slithir.variables.temporary import TemporaryVariable
from slither.slithir.variables.temporary_ssa import TemporaryVariableSSA
from slither.slithir.variables.tuple import TupleVariable


class HighLevelCall(Call, OperationWithLValue):
    """
    High level message call
    """

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(
        self,
        destination: SourceMapping,
        function_name: Constant,
        nbr_arguments: int,
        result: Optional[Union[TemporaryVariable, TupleVariable, TemporaryVariableSSA]],
        type_call: str,
        names: Optional[List[str]] = None,
    ) -> None:
        """
        #### Parameters
        names -
            For calls of the form f({argName1 : arg1, ...}), the names of parameters listed in call order.
            Otherwise, None.
        """
        assert isinstance(function_name, Constant)
        assert is_valid_lvalue(result) or result is None
        self._check_destination(destination)
        super().__init__(names=names)
        # Contract is only possible for library call, which inherits from highlevelcall
        self._destination: Union[Variable, SolidityVariable, Contract] = destination  # type: ignore
        self._function_name = function_name
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._callid = None  # only used if gas/value != 0
        self._function_instance = None

        self._call_value = None
        self._call_gas = None

    # Development function, to be removed once the code is stable
    # It is overridden by LibraryCall
    # pylint: disable=no-self-use
    def _check_destination(self, destination: Union[Variable, SolidityVariable, Contract]) -> None:
        assert isinstance(destination, (Variable, SolidityVariable))

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
    def read(self) -> List[SourceMapping]:
        all_read = [self.destination, self.call_gas, self.call_value] + self._unroll(self.arguments)
        # remove None
        return [x for x in all_read if x]

    @property
    def destination(self) -> Union[Variable, SolidityVariable, Contract]:
        """
        Return a variable or a solidityVariable
        Contract is only possible for LibraryCall

        Returns:

        """
        return self._destination

    @property
    def function_name(self) -> Constant:
        return self._function_name

    @property
    def function(self) -> Union[Function, Variable]:
        return self._function_instance

    @function.setter
    def function(self, function):
        self._function_instance = function

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################
    def is_static_call(self) -> bool:
        # If solidity >0.5, STATICCALL is used
        if self.compilation_unit.solc_version and self.compilation_unit.solc_version >= "0.5.0":
            if isinstance(self.function, Function) and (self.function.view or self.function.pure):
                return True
            if isinstance(self.function, Variable):
                return True
        return False

    def can_reenter(self, callstack: Optional[List[Union[Function, Variable]]] = None) -> bool:
        """
        Must be called after slithIR analysis pass
        For Solidity > 0.5, filter access to public variables and constant/pure/view
        For call to this. check if the destination can re-enter
        :param callstack: check for recursion
        :return: bool
        """
        if self.is_static_call():
            return False
        # If there is a call to itself
        # We can check that the function called is
        # reentrancy-safe
        if self.destination == SolidityVariable("this"):
            if isinstance(self.function, Variable):
                return False
            # In case of recursion, return False
            callstack = [] if callstack is None else callstack
            if self.function in callstack:
                return False
            callstack = callstack + [self.function]
            if self.function.can_reenter(callstack):
                return True
        if isinstance(self.destination, Variable):
            if not self.destination.is_reentrant:
                return False

        return True

    def can_send_eth(self) -> bool:
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        return self._call_value is not None

    # endregion
    ###################################################################################
    ###################################################################################
    # region Built in
    ###################################################################################
    ###################################################################################

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

        txt = "{}HIGH_LEVEL_CALL, dest:{}({}), function:{}, arguments:{} {} {}"
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = f"{self.lvalue}({','.join(str(x) for x in self.lvalue.type)}) = "
        else:
            lvalue = f"{self.lvalue}({self.lvalue.type}) = "
        return txt.format(
            lvalue,
            self.destination,
            self.destination.type,
            self.function_name,
            [str(x) for x in arguments],
            value,
            gas,
        )
