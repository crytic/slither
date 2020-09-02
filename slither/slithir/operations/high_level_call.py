from typing import Union

from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.declarations.function import Function

from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant


class HighLevelCall(Call, OperationWithLValue):
    """
        High level message call
    """

    # pylint: disable=too-many-arguments,too-many-instance-attributes
    def __init__(self, destination, function_name, nbr_arguments, result, type_call):
        assert isinstance(function_name, Constant)
        assert is_valid_lvalue(result) or result is None
        self._check_destination(destination)
        super(HighLevelCall, self).__init__()
        self._destination = destination
        self._function_name = function_name
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._callid = None  # only used if gas/value != 0
        self._function_instance = None

        self._call_value = None
        self._call_gas = None

    # Development function, to be removed once the code is stable
    # It is ovveride by LbraryCall
    def _check_destination(self, destination):  # pylint: disable=no-self-use
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
    def read(self):
        all_read = [self.destination, self.call_gas, self.call_value] + self._unroll(
            self.arguments
        )
        # remove None
        return [x for x in all_read if x] + [self.destination]

    @property
    def destination(self):
        return self._destination

    @property
    def function_name(self):
        return self._function_name

    @property
    def function(self) -> Union[Function, Variable]:
        return self._function_instance

    @function.setter
    def function(self, function):
        self._function_instance = function

    @property
    def nbr_arguments(self):
        return self._nbr_arguments

    @property
    def type_call(self):
        return self._type_call

    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def can_reenter(self, callstack=None):
        """
        Must be called after slithIR analysis pass
        For Solidity > 0.5, filter access to public variables and constant/pure/view
        For call to this. check if the destination can re-enter
        :param callstack: check for recursion
        :return: bool
        """
        # If solidity >0.5, STATICCALL is used
        if self.slither.solc_version and self.slither.solc_version >= "0.5.0":
            if isinstance(self.function, Function) and (
                self.function.view or self.function.pure
            ):
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

    def can_send_eth(self):
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
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = "{}({}) = ".format(
                self.lvalue, ",".join(str(x) for x in self.lvalue.type)
            )
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
