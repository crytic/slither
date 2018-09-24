from slither.slithir.operations.lvalue import OperationWithLValue
from slither.core.variables.variable import Variable
from slither.core.declarations.solidity_variables import SolidityVariableComposed, SolidityFunction
from slither.core.declarations.structure import Structure
from slither.core.declarations.event import Event


class TmpCall(OperationWithLValue):

    def __init__(self, called, nbr_arguments, result, type_call):
        assert isinstance(called, (Variable,
                                   SolidityVariableComposed,
                                   SolidityFunction,
                                   Structure,
                                   Event))
        super(TmpCall, self).__init__()
        self._called = called
        self._nbr_arguments = nbr_arguments
        self._type_call = type_call
        self._lvalue = result
        self._ori = None # 
        self._callid = None

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

    @property
    def read(self):
        return [self.called]

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
        return str(self.lvalue) +' = TMPCALL{} '.format(self.nbr_arguments)+ str(self._called) 

