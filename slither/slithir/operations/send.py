from slither.core.declarations.solidity_variables import SolidityVariable
from slither.core.variables.variable import Variable
from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue


class Send(Call, OperationWithLValue):
    def __init__(self, destination, value, result):
        assert is_valid_lvalue(result)
        assert isinstance(destination, (Variable, SolidityVariable))
        super().__init__()
        self._destination = destination
        self._lvalue = result

        self._call_value = value

    def can_send_eth(self):
        return True

    @property
    def call_value(self):
        return self._call_value

    @property
    def read(self):
        return [self.destination, self.call_value]

    @property
    def destination(self):
        return self._destination

    def __str__(self):
        value = "value:{}".format(self.call_value)
        return str(self.lvalue) + " = SEND dest:{} {}".format(self.destination, value)


#
