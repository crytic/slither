from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue

from slither.slithir.utils.utils import is_valid_lvalue, is_valid_rvalue

from slither.core.declarations.contract import Contract
from slither.slithir.variables.constant import Constant

class NewContract(Call, OperationWithLValue):

    def __init__(self, contract_name, lvalue):
        assert isinstance(contract_name, Constant)
        assert is_valid_lvalue(lvalue)
        super(NewContract, self).__init__()
        self._contract_name = contract_name
        # todo create analyze to add the contract instance
        self._lvalue = lvalue

    @property
    def contract_name(self):
        return self._contract_name

    @property
    def read(self):
        return list(self.arguments)
    def __str__(self):
        args = [str(a) for a in self.arguments]
        return '{} = new {}({})'.format(self.lvalue, self.contract_name, ','.join(args))
