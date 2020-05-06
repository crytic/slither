from typing import Optional, TYPE_CHECKING, List

from slither.core.declarations import Function
from slither.core.variables.variable import Variable
from slither.slithir.operations.high_level_call import HighLevelCall

from slither.core.declarations.contract import Contract

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE
    from slither.slithir.variables import Constant


class LibraryCall(HighLevelCall):
    """
        High level message call
    """

    def __init__(
        self,
        destination: "Contract",
        function_name: "Constant",
        nbr_arguments: int,
        result: Optional["VALID_LVALUE"],
        type_call: str,
    ):
        self._destination: "Contract"
        super().__init__(destination, function_name, nbr_arguments, result, type_call)

    # Development function, to be removed once the code is stable
    def _check_destination(self, destination):
        assert isinstance(destination, Contract)

    @property
    def destination(self) -> "Contract":
        return self._destination

    def can_reenter(self, callstack: Optional[List] = None):
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        # Libraries never use static call
        # https://solidity.readthedocs.io/en/v0.6.7/contracts.html#view-functions
        # Yet we can make the assumption that state variable read wont re-enter
        # As well as view/pure calls
        # As library code is known at compile time
        # If someone were to deploys with a malicious library, other issues will be present
        return super().can_reenter(callstack)

    def __str__(self):
        gas = ""
        if self.call_gas:
            gas = "gas:{}".format(self.call_gas)
        arguments = []
        if self.arguments:
            arguments = self.arguments
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = "{}({}) = ".format(self.lvalue, ",".join(str(x) for x in self.lvalue.type))
        else:
            lvalue = "{}({}) = ".format(self.lvalue, self.lvalue.type)
        txt = "{}LIBRARY_CALL, dest:{}, function:{}, arguments:{} {}"
        return txt.format(
            lvalue, self.destination, self.function_name, [str(x) for x in arguments], gas
        )
