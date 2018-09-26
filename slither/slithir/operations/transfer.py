from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable

from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant

class Transfer(Call):

    def __init__(self, destination, value):
        assert isinstance(destination, (Variable, SolidityVariable))
        self._destination = destination
        super(Transfer, self).__init__()

        self._call_value = value


    @property
    def call_value(self):
        return self._call_value

    @property
    def read(self):
        return [self.destination]

    @property
    def destination(self):
        return self._destination

    def __str__(self):
        value = 'value:{}'.format(self.call_value)
        return 'Transfer dest:{} {}'.format(self.destination, value)


