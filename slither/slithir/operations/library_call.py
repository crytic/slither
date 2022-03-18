from slither.core.declarations import Function
from slither.slithir.operations.high_level_call import HighLevelCall
from slither.core.declarations.contract import Contract


class LibraryCall(HighLevelCall):
    """
    High level message call
    """

    # Development function, to be removed once the code is stable
    def _check_destination(self, destination):
        assert isinstance(destination, Contract)

    def can_reenter(self, callstack=None):
        """
        Must be called after slithIR analysis pass
        :return: bool
        """
        if self.is_static_call():
            return False
        # In case of recursion, return False
        callstack = [] if callstack is None else callstack
        if self.function in callstack:
            return False
        callstack = callstack + [self.function]
        return self.function.can_reenter(callstack)

    def __str__(self):
        gas = ""
        if self.call_gas:
            gas = f"gas:{self.call_gas}"
        arguments = []
        if self.arguments:
            arguments = self.arguments
        if not self.lvalue:
            lvalue = ""
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = f"{self.lvalue}({','.join(str(x) for x in self.lvalue.type)}) = "
        else:
            lvalue = f"{self.lvalue}({self.lvalue.type}) = "
        txt = "{}LIBRARY_CALL, dest:{}, function:{}, arguments:{} {}"

        function_name = self.function_name
        if self.function:
            if isinstance(self.function, Function):
                function_name = self.function.canonical_name
        return txt.format(
            lvalue,
            self.destination,
            function_name,
            [str(x) for x in arguments],
            gas,
        )
