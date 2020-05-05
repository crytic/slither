from typing import Union, Type, Optional, TYPE_CHECKING, List

from slither.core.declarations import Contract
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.declarations.function import Function

from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class HighLevelCall(Call, OperationWithLValue):
    """
        High level message call
    """

    def __init__(
        self,
        destination: Union[Variable, SolidityVariable, Contract],
        function_name: Constant,
        nbr_arguments: int,
        result: Optional["VALID_LVALUE"],
        type_call: str,
    ):
        """
        destination is a contract only for LibraryCall

        :param destination:
        :param function_name:
        :param nbr_arguments:
        :param result:
        :param type_call:
        """
        assert isinstance(function_name, Constant)
        assert is_valid_lvalue(result) or result is None
        super(HighLevelCall, self).__init__()
        # _destination is a contract only for library
        self._check_destination(destination)
        self._destination: Union[Variable, SolidityVariable, Contract] = destination
        self._function_name: Constant = function_name
        self._nbr_arguments: int = nbr_arguments
        self._type_call: str = type_call
        self._lvalue: Optional["VALID_LVALUE"] = result
        self._callid: Optional[str] = None  # only used if gas/value != 0
        self._function_instance: Optional[Function, Variable] = None

        self._call_value: Optional["VALID_RVALUE"] = None
        self._call_gas: Optional["VALID_RVALUE"] = None

    # Development function, to be removed once the code is stable
    # It is ovveride by LbraryCall
    def _check_destination(self, destination):
        assert isinstance(destination, (Variable, SolidityVariable))

    @property
    def call_id(self) -> Optional[str]:
        return self._callid

    @call_id.setter
    def call_id(self, c: str):
        self._callid = c

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
    def read(self) -> List[Union["VALID_LVALUE", "VALID_RVALUE", "Variable", "SolidityVariable"]]:
        all_read = [self.destination, self.call_gas, self.call_value] + self._unroll(self.arguments)
        # remove None
        return [x for x in all_read if x] + [self.destination]

    @property
    def destination(self) -> Union[Variable, SolidityVariable]:
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

    def can_reenter(self, callstack: Optional[List] = None) -> bool:
        """
        Must be called after slithIR analysis pass
        For Solidity > 0.5, filter access to public variables and constant/pure/view
        For call to this. check if the destination can re-enter
        :param callstack: check for recursion
        :return: bool
        """
        # If solidity >0.5, STATICCALL is used
        if self.slither.solc_version and self.slither.solc_version >= "0.5.0":
            if isinstance(self.function, Function) and (self.function.view or self.function.pure):
                return False
            if isinstance(self.function, Variable):
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
            value = "value:{}".format(self.call_value)
        if self.call_gas:
            gas = "gas:{}".format(self.call_gas)
        arguments = []
        if self.arguments:
            arguments = self.arguments

        txt = "{}HIGH_LEVEL_CALL, dest:{}({}), function:{}, arguments:{} {} {}"
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, list):
            lvalue = "{}({}) = ".format(self.lvalue, ",".join(str(x) for x in self.lvalue.type))
        else:
            lvalue = "{}({}) = ".format(self.lvalue, self.lvalue.type)
        return txt.format(
            lvalue,
            self.destination,
            self.destination.type,
            self.function_name,
            [str(x) for x in arguments],
            value,
            gas,
        )
