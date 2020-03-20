from slither.slithir.operations import Call, OperationWithLValue
from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant


class NewContract(Call, OperationWithLValue):

    def __init__(self, contract_name, lvalue):
        assert isinstance(contract_name, Constant)
        assert is_valid_lvalue(lvalue)
        super(NewContract, self).__init__()
        self._contract_name = contract_name
        # todo create analyze to add the contract instance
        self._lvalue = lvalue
        self._callid = None  # only used if gas/value != 0
        self._call_value = None

    @property
    def call_value(self):
        return self._call_value

    @call_value.setter
    def call_value(self, v):
        self._call_value = v

    @property
    def call_id(self):
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def contract_name(self):
        return self._contract_name

    @property
    def read(self):
        return self._unroll(self.arguments)

    @property
    def contract_created(self):
        contract_name = self.contract_name
        contract_instance = self.slither.get_contract_from_name(contract_name)
        return contract_instance

    ###################################################################################
    ###################################################################################
    # region Analyses
    ###################################################################################
    ###################################################################################

    def can_reenter(self, callstack=None):
        '''
        Must be called after slithIR analysis pass
        For Solidity > 0.5, filter access to public variables and constant/pure/view
        For call to this. check if the destination can re-enter
        :param callstack: check for recursion
        :return: bool
        '''
        callstack = [] if callstack is None else callstack
        constructor = self.contract_created.constructor
        if constructor is None:
            return False
        if constructor in callstack:
            return False
        callstack = callstack + [constructor]
        return constructor.can_reenter(callstack)

    def can_send_eth(self):
        '''
        Must be called after slithIR analysis pass
        :return: bool
        '''
        return self._call_value is not None

    # endregion

    def __str__(self):
        value = ''
        if self.call_value:
            value = 'value:{}'.format(self.call_value)
        args = [str(a) for a in self.arguments]
        return '{} = new {}({}) {}'.format(self.lvalue, self.contract_name, ','.join(args), value)
