from typing import Union, TYPE_CHECKING, List

from slither.slithir.operations.call import Call
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable

if TYPE_CHECKING:
    from slither.slithir.utils.utils import VALID_RVALUE


class Transfer(Call):
    def __init__(self, destination: Union[Variable, SolidityVariable], value: "VALID_RVALUE"):
        assert isinstance(destination, (Variable, SolidityVariable))
        self._destination = destination
        super(Transfer, self).__init__()

        self._call_value = value

    def can_send_eth(self) -> bool:
        return True

    @property
    def call_value(self) -> "VALID_RVALUE":
        return self._call_value

    @property
    def read(self) -> List[Union[Variable, SolidityVariable, "VALID_RVALUE"]]:
        return [self.destination, self.call_value]

    @property
    def destination(self) -> Union[Variable, SolidityVariable]:
        return self._destination

    def __str__(self):
        value = "value:{}".format(self.call_value)
        return "Transfer dest:{} {}".format(self.destination, value)
