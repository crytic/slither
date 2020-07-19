from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable

from slither.slithir.variables.constant import Constant


class LowLevelCall(Call, OperationWithLValue):
    """
        High level message call
    """

    def __init__(self, destination, function_name, nbr_arguments, result, type_call):
        assert isinstance(destination, (Variable, SolidityVariable))
        assert isinstance(function_name, Constant)
        super(LowLevelCall, self).__init__()
        self._destination = destination
        self._function_name = function_name
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._callid = None  # only used if gas/value != 0

        self._call_value = None
        self._call_gas = None

    @property
    def call_id(self):
        return self._callid

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def call_value(self):
        return self._call_value

    @call_value.setter
    def call_value(self, v):
        self._call_value = v

    @property
    def call_gas(self):
        return self._call_gas

    @call_gas.setter
    def call_gas(self, v):
        self._call_gas = v

    @property
    def read(self):
        all_read = [self.destination, self.call_gas, self.call_value] + self.arguments
        # remove None
        return self._unroll([x for x in all_read if x])

    def can_reenter(self, callstack=None):
        '''
        Must be called after slithIR analysis pass
        :return: bool
        '''
        return True

    def can_send_eth(self):
        '''
        Must be called after slithIR analysis pass
        :return: bool
        '''
        return self._call_value is not None

    @property
    def destination(self):
        return self._destination

    @property
    def function_name(self):
        return self._function_name

    @property
    def nbr_arguments(self):
        return self._nbr_arguments

    @property
    def type_call(self):
        return self._type_call

    def __str__(self):
        value = ''
        gas = ''
        if self.call_value:
            value = 'value:{}'.format(self.call_value)
        if self.call_gas:
            gas = 'gas:{}'.format(self.call_gas)
        arguments = []
        if self.arguments:
            arguments = self.arguments
        return_type = self.lvalue.type

        if return_type and isinstance(return_type, list):
            return_type = ','.join(str(x) for x in return_type)

        txt = '{}({}) = LOW_LEVEL_CALL, dest:{}, function:{}, arguments:{} {} {}'
        return txt.format(self.lvalue,
                          return_type,
                          self.destination,
                          self.function_name,
                          [str(x) for x in arguments],
                          value,
                          gas)
