from typing import TYPE_CHECKING, List, Optional

from slither.core.declarations.solidity_variables import SolidityFunction
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_LVALUE, VALID_RVALUE


class SolidityCall(Call, OperationWithLValue):
    def __init__(
        self,
        function: SolidityFunction,
        nbr_arguments: int,
        result: Optional["VALID_LVALUE"],
        type_call: str,
    ):
        assert isinstance(function, SolidityFunction)
        super(SolidityCall, self).__init__()
        self._function: SolidityFunction = function
        self._nbr_arguments: int = nbr_arguments
        self._type_call = type_call
        self._lvalue = result

    @property
    def read(self) -> List["VALID_RVALUE"]:
        return self._unroll(self.arguments)

    # TODO: this collude with childNode, need to be changed to another name
    @property
    def function(self) -> SolidityFunction:
        return self._function

    @property
    def nbr_arguments(self) -> int:
        return self._nbr_arguments

    @property
    def type_call(self) -> str:
        return self._type_call

    def __str__(self):
        if (self.function == SolidityFunction("abi.decode()") and
                len(self.arguments) == 2 and
                isinstance(self.arguments[1], list)):
            args = str(self.arguments[0]) + '(' + ','.join([str(a) for a in self.arguments[1]]) + ')'
        else:
            args = ','.join([str(a) for a in self.arguments])

        lvalue = ''
        if self.lvalue:
            if isinstance(self.lvalue.type, (list,)):
                lvalue = '{}({}) = '.format(self.lvalue, ','.join(str(x) for x in self.lvalue.type))
            else:
                lvalue = '{}({}) = '.format(self.lvalue, self.lvalue.type)
        return lvalue + " = SOLIDITY_CALL {}({})".format(
            self.function.full_name, ",".join(args)
        )