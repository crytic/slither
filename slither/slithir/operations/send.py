from typing import Union, List, TYPE_CHECKING

from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue


if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE, VALID_LVALUE


class Send(Call, OperationWithLValue):
    def __init__(
        self,
        destination: Union[Variable, SolidityVariable],
        value: "VALID_RVALUE",
        result: "VALID_LVALUE",
    ):
        assert is_valid_lvalue(result)
        assert isinstance(destination, (Variable, SolidityVariable))
        super(Send, self).__init__()
        self._destination = destination
        self._lvalue = result

        self._call_value = value

    def can_send_eth(self) -> bool:
        return True

    @property
    def call_value(self) -> "VALID_RVALUE":
        return self._call_value

    @property
    def read(self) -> List[Union["VALID_RVALUE", Variable]]:
        return [self.destination, self.call_value]

    @property
    def lvalue(self) -> "VALID_LVALUE":
        return self._lvalue

    @lvalue.setter
    def lvalue(self, lvalue):
        self._lvalue = lvalue

    @property
    def destination(self) -> Union[Variable, SolidityVariable]:
        return self._destination

    def __str__(self):
        value = "value:{}".format(self.call_value)
        return str(self.lvalue) + " = SEND dest:{} {}".format(self.destination, value)


#
