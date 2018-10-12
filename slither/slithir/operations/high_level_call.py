from slither.slithir.operations.call import Call
from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariable

from slither.slithir.utils.utils import is_valid_lvalue
from slither.slithir.variables.constant import Constant

class HighLevelCall(Call, OperationWithLValue):
    """
        High level message call
    """

    def __init__(self, destination, function_name, nbr_arguments, result, type_call):
        assert isinstance(function_name, Constant)
        assert is_valid_lvalue(result)
        self._check_destination(destination)
        super(HighLevelCall, self).__init__()
        self._destination = destination
        self._function_name = function_name
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._callid = None # only used if gas/value != 0
        self._function_instance = None

        self._call_value = None
        self._call_gas = None

    # Development function, to be removed once the code is stable
    # It is ovveride by LbraryCall
    def _check_destination(self, destination):
        assert isinstance(destination, (Variable, SolidityVariable))

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
        return [self.destination]

    @property
    def destination(self):
        return self._destination

    @property
    def function_name(self):
        return self._function_name

    @property
    def function(self):
        return self._function_instance

    @function.setter
    def function(self, function):
        self._function_instance = function

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

        txt = '{}HIGH_LEVEL_CALL, dest:{}({}), function:{}, arguments:{} {} {}'
        if not self.lvalue:
            lvalue = ''
        elif isinstance(self.lvalue.type, (list,)):
            lvalue = '{}({}) = '.format(self.lvalue, ','.join(str(x) for x in self.lvalue.type))
        else:
            lvalue = '{}({}) = '.format(self.lvalue, self.lvalue.type)
        return txt.format(lvalue,
                          self.destination,
                          self.destination.type,
                          self.function_name,
                          [str(x) for x in arguments],
                          value,
                          gas)
