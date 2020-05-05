from typing import Optional, TYPE_CHECKING, List

from slither.slithir.operations.high_level_call import HighLevelCall

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE
    from slither.slithir.variables import Constant
    from slither.core.declarations.contract import Contract


class LibraryCall(HighLevelCall):
    """
        High level message call
    """

    def __init__(self, destination: "Contract", function_name: "Constant", nbr_arguments: int,
                 result: Optional["VALID_LVALUE"], type_call: str):
        self._destination: "Contract"
        super().__init__(destination, function_name, nbr_arguments, result, type_call)

    # Development function, to be removed once the code is stable
    def _check_destination(self, destination):
        assert isinstance(destination, Contract)

    @property
    def destination(self) -> "Contract":
        return self._destination

    def can_reenter(self, callstack: Optional[List]=None):
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        # In case of recursion, return False
        callstack = [] if callstack is None else callstack
        if self.function in callstack:
            return False
        callstack = callstack + [self.function]
        return self.function.can_reenter(callstack)

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
