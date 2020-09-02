from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue


class SolidityCall(Call, OperationWithLValue):
    def __init__(self, function, nbr_arguments, result, type_call):
        assert isinstance(function, SolidityFunction)
        super(SolidityCall, self).__init__()
        self._function = function
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result

    @property
    def read(self):
        return self._unroll(self.arguments)

    @property
    def function(self):
        return self._function

    @property
    def nbr_arguments(self):
        return self._nbr_arguments

    @property
    def type_call(self):
        return self._type_call

    def __str__(self):
        if (
            self.function == SolidityFunction("abi.decode()")
            and len(self.arguments) == 2
            and isinstance(self.arguments[1], list)
        ):
            args = (
                str(self.arguments[0])
                + "("
                + ",".join([str(a) for a in self.arguments[1]])
                + ")"
            )
        else:
            args = ",".join([str(a) for a in self.arguments])

        lvalue = ""
        if self.lvalue:
            if isinstance(self.lvalue.type, (list,)):
                lvalue = "{}({}) = ".format(
                    self.lvalue, ",".join(str(x) for x in self.lvalue.type)
                )
            else:
                lvalue = "{}({}) = ".format(self.lvalue, self.lvalue.type)
        return lvalue + "SOLIDITY_CALL {}({})".format(self.function.full_name, args)
