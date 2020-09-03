from slither.core.declarations import (
    Event,
    Contract,
    SolidityVariableComposed,
    SolidityFunction,
    Structure,
)
from slither.core.variables.variable import Variable
from slither.slithir.operations.lvalue import OperationWithLValue


class TmpCall(OperationWithLValue):  # pylint: disable=too-many-instance-attributes
    def __init__(self, called, nbr_arguments, result, type_call):
        assert isinstance(
            called,
            (
                Contract,
                Variable,
                SolidityVariableComposed,
                SolidityFunction,
                Structure,
                Event,
            ),
        )
        super().__init__()
        self._called = called
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._ori = None  #
        self._callid = None
        self._gas = None
        self._value = None
        self._salt = None

    @property
    def call_value(self):
        return self._value

    @call_value.setter
    def call_value(self, v):
        self._value = v

    @property
    def call_gas(self):
        return self._gas

    @call_gas.setter
    def call_gas(self, gas):
        self._gas = gas

    @property
    def call_salt(self):
        return self._salt

    @call_salt.setter
    def call_salt(self, salt):
        self._salt = salt

    @property
    def call_id(self):
        return self._callid

    @property
    def read(self):
        return [self.called]

    @call_id.setter
    def call_id(self, c):
        self._callid = c

    @property
    def called(self):
        return self._called

    @called.setter
    def called(self, c):
        self._called = c

    @property
    def nbr_arguments(self):
        return self._nbr_arguments

    @property
    def type_call(self):
        return self._type_call

    @property
    def ori(self):
        return self._ori

    def set_ori(self, ori):
        self._ori = ori

    def __str__(self):
        return (
            str(self.lvalue)
            + " = TMPCALL{} ".format(self.nbr_arguments)
            + str(self._called)
        )
